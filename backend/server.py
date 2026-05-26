"""Live Astrology backend.

Real transactional endpoints backing the React frontend at /app/liveastrology.
Stores records in MongoDB and sends email through Resend.

Endpoints (all prefixed with /api):

  GET  /api/health                      → liveness probe

  POST /api/subscribe                   → starts double-opt-in flow
       body: { email, first_name? }
       sends template 01 (confirm) + template 07 (admin)

  GET  /api/subscribe/confirm?token=…   → completes opt-in
       sends template 02 (welcome)
       redirects to /?subscribed=1

  POST /api/unsubscribe                 → one-click unsubscribe
       body: { email?, token? }
       sends template 03 (unsub confirm)

  POST /api/feedback                    → /feedback page
       body: { name?, email?, rating?, category, message }
       sends template 04 (ack) + template 07 (admin)

  POST /api/contact                     → future contact form
       body: { name, email, subject, message }
       sends template 05 (ack) + template 07 (admin)
"""
import logging
import os
import re
import secrets
import string
from datetime import datetime, timezone
from typing import Annotated, Any, Literal

from dotenv import load_dotenv

load_dotenv()

from fastapi import Body, Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

import beta as beta_module
import billing as billing_module
import compatibility_reports as compatibility_module
import email_service
import feeds as feeds_module
import forecast as forecast_module
import google_indexing as google_indexing_module
import indexnow as indexnow_module
import interpretation as interpretation_module
import review_requests as review_requests_module
import scheduler as scheduler_module
import turnstile as turnstile_module

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("liveastrology")

# ---------- Config ----------
APP_ORIGIN    = os.environ.get("APP_ORIGIN", "https://liveastrology.app").rstrip("/")
NOTIFY_EMAIL  = os.environ.get("NOTIFY_EMAIL", "notify@liveastrology.app")
MONGO_URL     = os.environ["MONGO_URL"]
DB_NAME       = os.environ["DB_NAME"]
ADMIN_SECRET  = os.environ.get("ADMIN_SECRET", "")
SEO_WORKFLOW_TOKEN = os.environ.get("SEO_WORKFLOW_TOKEN", "")
RESEND_WEBHOOK_SECRET = os.environ.get("RESEND_WEBHOOK_SECRET", "")

# ---------- DB ----------
_mongo = AsyncIOMotorClient(MONGO_URL)
db = _mongo[DB_NAME]

# ---------- Rate limiter ----------
# IP-based, in-memory. Ingress may strip the real client IP — the limiter
# falls back to X-Forwarded-For via _client_ip. Fine for single-pod MVP;
# for multi-replica deployments swap storage_uri for Redis.
def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(
    key_func=_client_ip,
    default_limits=["120/minute"],
    # When REDIS_URL is set, slowapi stores counters in Redis so every
    # replica/worker shares the same per-IP state. Without it, counters
    # live in-process (fine for a single pod but not multi-replica).
    storage_uri=os.environ.get("REDIS_URL") or "memory://",
)

# ---------- App ----------
app = FastAPI(title="Live Astrology backend", version="1.0.0")
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests — please slow down and try again in a minute."},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _startup() -> None:
    if os.environ.get("ENABLE_SCHEDULER", "1") == "1":
        scheduler_module.start_scheduler(db)


@app.on_event("shutdown")
async def _shutdown() -> None:
    scheduler_module.stop_scheduler()


def require_admin(authorization: str = Header(default="")) -> str:
    """Shared-secret bearer auth for admin-only endpoints.

    Returns the token type (``"admin"``) on success — useful when the
    dependency is consumed as a value via ``Depends(require_admin)``.
    """
    if not ADMIN_SECRET:
        raise HTTPException(status_code=503, detail="ADMIN_SECRET is not configured")
    expected = f"Bearer {ADMIN_SECRET}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return "admin"


def require_seo_or_admin(authorization: str = Header(default="")) -> str:
    """Accepts EITHER ``ADMIN_SECRET`` or ``SEO_WORKFLOW_TOKEN``.

    Used to gate the article-CMS + indexing endpoints so external SEO
    automation (Arvow / Blotato / Claude Code) can publish without being
    granted full admin reach over subscribers, billing, etc.

    Returns ``"admin"`` or ``"seo"`` depending on which token authenticated
    the caller — consumed by the audit-log helper to attribute writes.
    """
    if not ADMIN_SECRET and not SEO_WORKFLOW_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="Neither ADMIN_SECRET nor SEO_WORKFLOW_TOKEN is configured",
        )
    if ADMIN_SECRET and authorization == f"Bearer {ADMIN_SECRET}":
        return "admin"
    if SEO_WORKFLOW_TOKEN and authorization == f"Bearer {SEO_WORKFLOW_TOKEN}":
        return "seo"
    raise HTTPException(status_code=401, detail="Unauthorized")


# ---------- Utilities ----------
_ALPHANUM = string.ascii_uppercase + string.digits


def _short_id(prefix: str, length: int = 6) -> str:
    return f"{prefix}-" + "".join(secrets.choice(_ALPHANUM) for _ in range(length))


def _token(n: int = 32) -> str:
    return secrets.token_urlsafe(n)


def _first_name(name: str | None, email: str | None) -> str:
    if name and name.strip():
        return name.strip().split()[0]
    if email:
        return email.split("@")[0]
    return "friend"


def _unsub_url(token: str) -> str:
    return f"{APP_ORIGIN}/api/unsubscribe?token={token}"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _admin_vars(
    *,
    event_type: str,
    summary: str,
    user_display: str,
    user_email: str,
    user_first_name: str,
    reference_id: str,
    payload: str,
    source: str,
    source_path: str,
    request: Request,
    reply_subject: str = "",
) -> dict[str, str]:
    """Template variables for template 07 (admin notification). Returns a
    dict safe to splat as ``**_admin_vars(...)`` into ``send_template`` so
    long as the caller does *not* also pass ``event_type`` / ``summary``
    explicitly."""
    ua = (request.headers.get("user-agent") or "unknown")[:200]
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown").split(",")[0].strip()
    return {
        "event_type": event_type,
        "summary": summary,
        "user_display": user_display or "anonymous",
        "user_email": user_email or "no-reply@liveastrology.app",
        "user_first_name": user_first_name,
        "reference_id": reference_id,
        "payload": payload,
        "source": source,
        "source_path": source_path,
        "received_at": _now().strftime("%Y-%m-%d %H:%M UTC"),
        "ip": ip,
        "user_agent": ua,
        "reply_subject": reply_subject or "Re: your message to Live Astrology",
    }


# ---------- Pydantic models ----------
class SubscribeIn(BaseModel):
    email: EmailStr
    first_name: Annotated[str | None, Field(default=None, max_length=80)] = None
    source: Annotated[str, Field(default="footer", max_length=40)] = "footer"
    cf_turnstile_token: Annotated[str | None, Field(default=None, max_length=3000)] = None


class UnsubscribeIn(BaseModel):
    email: EmailStr | None = None
    token: str | None = None


class FeedbackIn(BaseModel):
    name: Annotated[str | None, Field(default=None, max_length=80)] = None
    email: EmailStr | None = None
    rating: Annotated[int | None, Field(default=None, ge=0, le=5)] = None
    # Categorised beta-feedback ratings (1–5). All optional.
    rating_accuracy: Annotated[int | None, Field(default=None, ge=1, le=5)] = None
    rating_ui: Annotated[int | None, Field(default=None, ge=1, le=5)] = None
    rating_ai_quality: Annotated[int | None, Field(default=None, ge=1, le=5)] = None
    rating_recommend: Annotated[int | None, Field(default=None, ge=1, le=5)] = None
    category: Annotated[Literal["general", "bug", "feature", "content", "praise"], Field(default="general")] = "general"
    message: Annotated[str, Field(min_length=10, max_length=4000)]
    # User explicitly consents to having their feedback published on the
    # site as a testimonial. Default is *false* — opt-in, never opt-out.
    publish_consent: bool = False
    cf_turnstile_token: Annotated[str | None, Field(default=None, max_length=3000)] = None


class ContactIn(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=80)]
    email: EmailStr
    subject: Annotated[str, Field(min_length=1, max_length=200)]
    message: Annotated[str, Field(min_length=10, max_length=4000)]
    cf_turnstile_token: Annotated[str | None, Field(default=None, max_length=3000)] = None


# ---------- Routes ----------
@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "service": "liveastrology-backend", "time": _now().isoformat()}


# ---------- AI chart interpretation ----------
class InterpretIn(BaseModel):
    sun: Annotated[str, Field(min_length=3, max_length=20)]
    moon: Annotated[str, Field(min_length=3, max_length=20)]
    rising: Annotated[str, Field(min_length=3, max_length=20)]


@app.post("/api/interpret")
@limiter.limit("20/minute")
async def interpret(request: Request, payload: InterpretIn = Body(...)) -> dict[str, Any]:
    """Generate a plain-English interpretation for a Sun/Moon/Rising
    combination using Claude Sonnet 4.5. Results are cached in MongoDB
    by (sun, moon, rising) tuple, so repeated requests are free.
    """
    try:
        result = await interpretation_module.get_interpretation(
            db, payload.sun, payload.moon, payload.rising
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    # Increment the lifetime "charts interpreted today" counter.
    today = _now().strftime("%Y-%m-%d")
    await db.daily_metrics.update_one(
        {"date": today},
        {"$inc": {"charts": 1}, "$setOnInsert": {"date": today}},
        upsert=True,
    )
    return {"status": "ok", "interpretation": result}


@app.get("/api/charts-today")
async def charts_today() -> dict[str, Any]:
    """Counter for social proof: how many charts have been generated
    today. Combines AI interpretations (charts) with a baseline so the
    number is meaningful from day one.
    """
    today = _now().strftime("%Y-%m-%d")
    doc = await db.daily_metrics.find_one({"date": today}, {"_id": 0, "charts": 1})
    live_count = int(doc.get("charts", 0)) if doc else 0
    # Add a deterministic baseline derived from the day of the year so
    # the counter looks alive even at the start of a slow day.
    day_of_year = _now().timetuple().tm_yday
    baseline = 312 + (day_of_year * 17) % 91  # 312–402 baseline range
    return {"date": today, "charts_today": baseline + live_count}



# ---------- Billing / Premium subscription ----------
class CheckoutIn(BaseModel):
    package_id: Annotated[Literal["monthly", "yearly"], Field()]
    email: EmailStr
    origin_url: Annotated[str, Field(min_length=8, max_length=200)]


@app.get("/api/billing/packages")
async def billing_packages() -> dict[str, Any]:
    """Server-side fixed packages. Frontend renders these — but the
    amount is always trusted from this endpoint, never from a form."""
    return {
        "packages": [
            {"id": pid, **{k: v for k, v in pkg.items()}}
            for pid, pkg in billing_module.PACKAGES.items()
        ]
    }


@app.post("/api/billing/checkout")
@limiter.limit("5/minute")
async def billing_checkout(request: Request, payload: CheckoutIn = Body(...)) -> dict[str, Any]:
    try:
        return await billing_module.create_checkout_session(
            db,
            package_id=payload.package_id,
            email=str(payload.email),
            origin_url=payload.origin_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@app.get("/api/billing/checkout/status/{session_id}")
async def billing_checkout_status(session_id: str) -> dict[str, Any]:
    try:
        return await billing_module.get_checkout_status(db, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@app.get("/api/billing/status")
async def billing_status(email: str) -> dict[str, Any]:
    return await billing_module.get_entitlement(db, email)


@app.post("/api/webhook/stripe")
async def stripe_webhook(request: Request) -> dict[str, Any]:
    raw = await request.body()
    signature = request.headers.get("Stripe-Signature") or request.headers.get("stripe-signature")
    result = await billing_module.handle_webhook(db, raw, signature)
    # When a webhook secret is configured AND the payload didn't verify,
    # respond with 400 so Stripe retries (and so the secret is enforced).
    if result.get("status") == "rejected" and not result.get("dev_mode"):
        raise HTTPException(status_code=400, detail="webhook signature verification failed")
    return result


class CustomerPortalIn(BaseModel):
    email: EmailStr
    return_url: Annotated[str, Field(min_length=8, max_length=200)]


@app.post("/api/billing/portal")
@limiter.limit("10/minute")
async def billing_portal(request: Request, payload: CustomerPortalIn = Body(...)) -> dict[str, Any]:
    """Create a Stripe Customer Portal session for an existing paying
    subscriber. Only available when STRIPE_SUBSCRIPTION_MODE is on; for
    beta users (plan='beta') this returns a 409 since there's no Stripe
    billing relationship to manage."""
    customer_id = await billing_module.get_customer_id_for_email(db, str(payload.email))
    if not customer_id:
        raise HTTPException(
            status_code=409,
            detail="No Stripe subscription found for this email — nothing to manage.",
        )
    try:
        return await billing_module.create_customer_portal_session(
            customer_id=customer_id,
            return_url=payload.return_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))



# ---------- Beta launch (first 100 users get free Premium) ----------
class BetaClaimIn(BaseModel):
    email: EmailStr
    name: Annotated[str | None, Field(default=None, max_length=80)] = None


@app.get("/api/beta/status")
async def beta_status(email: str | None = None) -> dict[str, Any]:
    return await beta_module.get_status(db, email)


@app.post("/api/beta/claim")
@limiter.limit("5/minute")
async def beta_claim(request: Request, payload: BetaClaimIn = Body(...)) -> dict[str, Any]:
    try:
        result = await beta_module.claim(db, email=str(payload.email), name=payload.name)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Fire premium-fulfilment emails for granted (not already-claimed,
    # not waitlisted). Best-effort — failures are logged but don't fail
    # the claim. The actual entitlement row is already persisted.
    if result.get("result") == "granted":
        await _send_premium_welcome(
            email=str(payload.email),
            name=payload.name or "",
            plan_label="Beta — 90 days free",
            expires_at_iso=result["expires_at"],
        )

    return result


# ---------- Public testimonials ----------
@app.get("/api/testimonials")
async def public_testimonials(limit: int = 12) -> dict[str, Any]:
    """Returns feedback rows that the user consented to publish AND that
    an admin has approved (``published=true``). Excludes the email field
    entirely. Used for the homepage testimonial strip."""
    limit = max(1, min(50, int(limit)))
    cursor = db.feedback.find(
        {"publish_consent": True, "published": True},
        {"_id": 0, "email": 0, "ticket_id": 0},
    ).sort("created_at", -1).limit(limit)
    items: list[dict[str, Any]] = []
    async for row in cursor:
        # Coerce datetimes into ISO strings for JSON.
        if isinstance(row.get("created_at"), datetime):
            row["created_at"] = row["created_at"].isoformat()
        items.append(row)
    return {"count": len(items), "testimonials": items}


@app.post("/api/admin/feedback/{ticket_id}/publish", dependencies=[Depends(require_admin)])
async def admin_publish_feedback(ticket_id: str, published: bool = True) -> dict[str, Any]:
    """Admin-only toggle to approve a consented testimonial for display."""
    res = await db.feedback.update_one(
        {"ticket_id": ticket_id, "publish_consent": True},
        {"$set": {"published": published, "updated_at": _now()}},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="ticket not found or consent not given")
    return {"status": "ok", "ticket_id": ticket_id, "published": published}


# ---------- Premium: monthly forecast dispatch (admin / cron) ----------
class ForecastDispatchIn(BaseModel):
    force: bool = False


@app.post("/api/admin/premium/dispatch-monthly-forecast", dependencies=[Depends(require_admin)])
async def admin_dispatch_monthly_forecast(payload: ForecastDispatchIn = Body(default=ForecastDispatchIn())) -> dict[str, Any]:
    """Generate (if not cached) and send the current month's Premium
    forecast to every active entitlement. Designed to be called by a
    GitHub Actions cron on the 1st of each month; can also be invoked
    manually from the admin dashboard.
    """
    async def _send(slug: str, *, to: str, **kw: Any) -> None:
        await email_service.send_template(slug, to=to, **kw)

    try:
        result = await forecast_module.dispatch_monthly_forecast(
            db, _send, force=payload.force,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {"status": "ok", **result}


@app.get("/api/admin/premium/forecast-preview", dependencies=[Depends(require_admin)])
async def admin_forecast_preview(force: bool = False) -> dict[str, Any]:
    """Read-only preview of the current month's forecast payload
    without sending. Useful for sanity-checking the LLM output before
    triggering the dispatch."""
    try:
        forecast = await forecast_module.get_monthly_forecast(db, force=force)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {"status": "ok", "forecast": forecast}


# ---------- Premium: Day-60 review-ask dispatch (admin / cron) ----------
class ReviewRequestDispatchIn(BaseModel):
    dry_run: bool = False


@app.post("/api/admin/premium/dispatch-review-requests", dependencies=[Depends(require_admin)])
async def admin_dispatch_review_requests(
    payload: ReviewRequestDispatchIn = Body(default=ReviewRequestDispatchIn()),
) -> dict[str, Any]:
    """Email every beta claimant who's crossed the 60-day mark a
    Trustpilot/Product Hunt review-ask. One email per address, ever.

    Designed to be called by a GitHub Actions daily cron; can also be
    invoked manually from the admin dashboard. Pass ``dry_run=true``
    to count eligible recipients without actually sending.
    """
    async def _send(slug: str, *, to: str, **kw: Any) -> None:
        await email_service.send_template(slug, to=to, **kw)

    result = await review_requests_module.dispatch_review_requests(
        db, _send, dry_run=payload.dry_run,
    )
    return {"status": "ok", **result}


# ---------- Premium: request-driven compatibility report ----------
class CompatibilitySendIn(BaseModel):
    recipient_email: EmailStr
    person1_name: Annotated[str, Field(min_length=1, max_length=80)]
    person1_sun: Annotated[str, Field(min_length=3, max_length=20)]
    person1_moon: Annotated[str, Field(min_length=3, max_length=20)]
    person2_name: Annotated[str, Field(min_length=1, max_length=80)]
    person2_sun: Annotated[str, Field(min_length=3, max_length=20)]
    person2_moon: Annotated[str, Field(min_length=3, max_length=20)]
    score: Annotated[int, Field(ge=0, le=100)]


@app.post("/api/admin/premium/compatibility/send", dependencies=[Depends(require_admin)])
async def admin_send_compatibility(payload: CompatibilitySendIn = Body(...)) -> dict[str, Any]:
    """Admin-only endpoint that generates a Premium compatibility
    report via Claude and emails it to ``recipient_email`` using the
    `premium_compatibility` template. Used when a paying user replies
    to their welcome email asking for a synastry deep-dive.
    """
    # Sanity check — the recipient must be an active Premium member.
    ent = await db.entitlements.find_one(
        {"email": str(payload.recipient_email).lower(), "status": "active"},
        {"_id": 0, "expires_at": 1},
    )
    if not ent:
        raise HTTPException(
            status_code=409,
            detail="Recipient has no active Premium entitlement.",
        )

    async def _send(slug: str, *, to: str, **kw: Any) -> None:
        await email_service.send_template(slug, to=to, **kw)

    try:
        result = await compatibility_module.generate_and_send(
            db, _send,
            recipient_email=str(payload.recipient_email),
            person1_name=payload.person1_name,
            person1_sun=payload.person1_sun,
            person1_moon=payload.person1_moon,
            person2_name=payload.person2_name,
            person2_sun=payload.person2_sun,
            person2_moon=payload.person2_moon,
            score=payload.score,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {"status": "ok", **result}



# ---------- Premium fulfilment helpers ----------
async def _send_premium_welcome(
    *, email: str, name: str, plan_label: str, expires_at_iso: str
) -> None:
    """Send the premium welcome email and queue the 10-planet report.
    Idempotent at the email level: the caller controls when this fires
    (typically once, immediately after entitlement grant).
    """
    try:
        expires_dt = datetime.fromisoformat(expires_at_iso.replace("Z", "+00:00"))
        expires_human = expires_dt.strftime("%B %-d, %Y")
    except Exception:  # noqa: BLE001
        expires_human = expires_at_iso

    display_name = (name or email.split("@")[0]).strip() or "there"
    try:
        await email_service.send_template(
            "premium_welcome",
            to=email,
            name=display_name,
            plan_label=plan_label,
            expires_at_human=expires_human,
            unsubscribe_url=f"{APP_ORIGIN}/upgrade/manage",
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Could not send premium_welcome email: %s", exc)

    # The 10-planet report is the generic activation reading. It uses
    # the existing template and ships immediately.
    try:
        await email_service.send_template(
            "premium_10_planet",
            to=email,
            name=display_name,
            unsubscribe_url=f"{APP_ORIGIN}/upgrade/manage",
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Could not send premium_10_planet email: %s", exc)


# ---------- Existing routes ----------
@app.post("/api/subscribe", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("5/minute")
async def subscribe(request: Request, payload: SubscribeIn = Body(...)) -> dict[str, Any]:
    if not await turnstile_module.verify(payload.cf_turnstile_token, remote_ip=_client_ip(request)):
        raise HTTPException(status_code=403, detail="Human verification failed — please retry.")
    email = payload.email.lower()
    first_name = _first_name(payload.first_name, email)
    confirm_token = _token()
    unsub_token = _token()

    # Upsert subscriber in pending state. Idempotent for duplicate submissions.
    await db.subscribers.update_one(
        {"email": email},
        {
            "$set": {
                "email": email,
                "first_name": first_name,
                "status": "pending",
                "confirm_token": confirm_token,
                "unsub_token": unsub_token,
                "source": payload.source,
                "updated_at": _now(),
            },
            "$setOnInsert": {"created_at": _now()},
        },
        upsert=True,
    )

    confirm_url = f"{APP_ORIGIN}/api/subscribe/confirm?token={confirm_token}"
    unsubscribe_url = _unsub_url(unsub_token)

    # 1) User opt-in confirmation (template 01)
    await email_service.send_template(
        "subscribe_confirm",
        to=email,
        list_unsubscribe=unsubscribe_url,
        first_name=first_name,
        email=email,
        confirm_url=confirm_url,
        unsubscribe_url=unsubscribe_url,
    )

    # 2) Admin notification (template 07) — sent to NOTIFY_EMAIL
    await email_service.send_template(
        "admin_notification",
        to=NOTIFY_EMAIL,
        **_admin_vars(
            event_type="subscribe",
            summary=f"New subscription request from {email}",
            user_display=first_name,
            user_email=email,
            user_first_name=first_name,
            reference_id=confirm_token[:8].upper(),
            payload=f"email       : {email}\nfirst_name  : {first_name}\nsource      : {payload.source}\nstatus      : pending-confirmation",
            source=payload.source,
            source_path="/api/subscribe",
            request=request,
            reply_subject="Welcome to Live Astrology",
        ),
    )

    return {"status": "pending", "message": "Please check your inbox to confirm your subscription."}


@app.get("/api/subscribe/confirm")
async def subscribe_confirm(token: str) -> RedirectResponse:
    sub = await db.subscribers.find_one({"confirm_token": token}, {"_id": 0})
    if not sub:
        return RedirectResponse(url=f"{APP_ORIGIN}/?subscribed=0&reason=invalid", status_code=302)

    already_confirmed = sub.get("status") == "confirmed"
    await db.subscribers.update_one(
        {"email": sub["email"]},
        {"$set": {"status": "confirmed", "confirmed_at": _now(), "updated_at": _now()}},
    )

    if not already_confirmed:
        await email_service.send_template(
            "subscribe_welcome",
            to=sub["email"],
            list_unsubscribe=_unsub_url(sub["unsub_token"]),
            first_name=sub.get("first_name") or _first_name(None, sub["email"]),
            email=sub["email"],
            unsubscribe_url=_unsub_url(sub["unsub_token"]),
        )

    return RedirectResponse(url=f"{APP_ORIGIN}/?subscribed=1", status_code=302)


@app.post("/api/unsubscribe")
@app.get("/api/unsubscribe")  # Gmail / Yahoo one-click header hits this via GET
async def unsubscribe(request: Request, token: str | None = None, email: str | None = None) -> dict[str, Any]:
    # When called via POST with a JSON body, FastAPI's query-param fallback
    # won't pick it up — parse body manually if present.
    if request.method == "POST":
        try:
            body = await request.json()
            token = token or body.get("token")
            email = email or body.get("email")
        except Exception:  # noqa: BLE001
            pass

    query: dict[str, Any] = {}
    if token:
        query = {"unsub_token": token}
    elif email:
        query = {"email": email.lower()}
    else:
        raise HTTPException(status_code=400, detail="token or email is required")

    sub = await db.subscribers.find_one(query, {"_id": 0})
    if not sub:
        # Be generous: still confirm to avoid leaking whether the email is in our list.
        return {"status": "ok"}

    await db.subscribers.update_one(
        {"email": sub["email"]},
        {"$set": {"status": "unsubscribed", "unsubscribed_at": _now(), "updated_at": _now()}},
    )

    await email_service.send_template(
        "unsubscribe_confirm",
        to=sub["email"],
        first_name=sub.get("first_name") or _first_name(None, sub["email"]),
        email=sub["email"],
    )

    return {"status": "ok", "message": "You have been unsubscribed."}


@app.post("/api/feedback", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("3/minute")
async def feedback(request: Request, payload: FeedbackIn = Body(...)) -> dict[str, Any]:
    if not await turnstile_module.verify(payload.cf_turnstile_token, remote_ip=_client_ip(request)):
        raise HTTPException(status_code=403, detail="Human verification failed — please retry.")
    ticket_id = _short_id("FB")
    first_name = _first_name(payload.name, payload.email)
    category_labels = {
        "general": "General feedback",
        "bug":     "Bug report",
        "feature": "Feature request",
        "content": "Astrology content correction",
        "praise":  "Just saying thanks",
    }
    category_label = category_labels.get(payload.category, "General feedback")
    rating_stars = (
        f"{'★' * payload.rating}{'☆' * (5 - payload.rating)} ({payload.rating}/5)"
        if payload.rating else "Not rated"
    )
    message_snippet = payload.message.strip()[:500]

    await db.feedback.insert_one({
        "ticket_id": ticket_id,
        "name": payload.name,
        "email": payload.email,
        "rating": payload.rating,
        "rating_accuracy": payload.rating_accuracy,
        "rating_ui": payload.rating_ui,
        "rating_ai_quality": payload.rating_ai_quality,
        "rating_recommend": payload.rating_recommend,
        "category": payload.category,
        "message": payload.message,
        "publish_consent": payload.publish_consent,
        # Admin must approve before a consenting testimonial is shown.
        "published": False,
        "created_at": _now(),
    })

    # 1) Ack the user (skip if they didn't share an email)
    if payload.email:
        await email_service.send_template(
            "feedback_ack",
            to=payload.email,
            first_name=first_name,
            email=payload.email,
            ticket_id=ticket_id,
            category=category_label,
            rating_stars=rating_stars,
            message_snippet=message_snippet,
        )

    # 2) Admin notification
    payload_dump = (
        f"ticket_id   : {ticket_id}\n"
        f"category    : {category_label}\n"
        f"rating      : {rating_stars}\n"
        f"name        : {payload.name or '-'}\n"
        f"email       : {payload.email or '-'}\n\n"
        f"message:\n{payload.message.strip()}"
    )
    await email_service.send_template(
        "admin_notification",
        to=NOTIFY_EMAIL,
        reply_to=payload.email or None,
        **_admin_vars(
            event_type="feedback",
            summary=f"{category_label} from {payload.name or 'anonymous'}",
            user_display=payload.name or "Anonymous",
            user_email=payload.email or "",
            user_first_name=first_name,
            reference_id=ticket_id,
            payload=payload_dump,
            source="/feedback",
            source_path="/api/feedback",
            request=request,
            reply_subject=f"Re: your feedback (#{ticket_id})",
        ),
    )

    return {"status": "ok", "ticket_id": ticket_id, "message": "Thanks! We've logged your feedback."}


@app.post("/api/contact", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("3/minute")
async def contact(request: Request, payload: ContactIn = Body(...)) -> dict[str, Any]:
    if not await turnstile_module.verify(payload.cf_turnstile_token, remote_ip=_client_ip(request)):
        raise HTTPException(status_code=403, detail="Human verification failed — please retry.")
    ticket_id = _short_id("CT")
    first_name = _first_name(payload.name, payload.email)
    received_at = _now().strftime("%Y-%m-%d %H:%M UTC")
    snippet = payload.message.strip()[:500]

    await db.contacts.insert_one({
        "ticket_id": ticket_id,
        "name": payload.name,
        "email": payload.email,
        "subject": payload.subject,
        "message": payload.message,
        "created_at": _now(),
    })

    await email_service.send_template(
        "contact_ack",
        to=payload.email,
        first_name=first_name,
        email=payload.email,
        subject=payload.subject,
        received_at=received_at,
        message_snippet=snippet,
    )

    await email_service.send_template(
        "admin_notification",
        to=NOTIFY_EMAIL,
        reply_to=payload.email,
        **_admin_vars(
            event_type="contact",
            summary=f"{payload.subject} — from {payload.name}",
            user_display=payload.name,
            user_email=payload.email,
            user_first_name=first_name,
            reference_id=ticket_id,
            payload=(
                f"ticket_id : {ticket_id}\n"
                f"subject   : {payload.subject}\n"
                f"name      : {payload.name}\n"
                f"email     : {payload.email}\n\n"
                f"message:\n{payload.message.strip()}"
            ),
            source="/contact",
            source_path="/api/contact",
            request=request,
            reply_subject=f"Re: {payload.subject} (#{ticket_id})",
        ),
    )

    return {"status": "ok", "ticket_id": ticket_id, "message": "Thanks! We'll reply within 2 business days."}


# ---------- Admin endpoints ----------
@app.post("/api/admin/dispatch-weekly", dependencies=[Depends(require_admin)])
async def admin_dispatch_weekly() -> dict[str, Any]:
    """Manually trigger the weekly horoscope send. Safe for external cron."""
    result = await scheduler_module.dispatch_weekly_horoscope(db)
    return result


@app.get("/api/admin/stats", dependencies=[Depends(require_admin)])
async def admin_stats() -> dict[str, Any]:
    subscribers_total   = await db.subscribers.count_documents({})
    subscribers_pending = await db.subscribers.count_documents({"status": "pending"})
    subscribers_active  = await db.subscribers.count_documents({"status": "confirmed"})
    subscribers_unsub   = await db.subscribers.count_documents({"status": "unsubscribed"})
    feedback_total      = await db.feedback.count_documents({})
    contacts_total      = await db.contacts.count_documents({})
    dispatches_total    = await db.weekly_dispatches.count_documents({})

    # Email deliverability health from ingested Resend webhook events.
    sent       = await db.email_events.count_documents({"type": "email.sent"})
    delivered  = await db.email_events.count_documents({"type": "email.delivered"})
    bounced    = await db.email_events.count_documents({"type": "email.bounced"})
    opened     = await db.email_events.count_documents({"type": "email.opened"})
    complained = await db.email_events.count_documents({"type": "email.complained"})
    clicked    = await db.email_events.count_documents({"type": "email.clicked"})
    last_event = await db.email_events.find_one({}, {"_id": 0, "type": 1, "received_at": 1}, sort=[("received_at", -1)])

    bounce_rate = round((bounced / delivered) * 100, 2) if delivered else 0.0
    open_rate   = round((opened  / delivered) * 100, 2) if delivered else 0.0

    return {
        "subscribers": {
            "total": subscribers_total,
            "pending": subscribers_pending,
            "confirmed": subscribers_active,
            "unsubscribed": subscribers_unsub,
        },
        "feedback_total": feedback_total,
        "contacts_total": contacts_total,
        "weekly_dispatches_total": dispatches_total,
        "email_health": {
            "sent": sent,
            "delivered": delivered,
            "bounced": bounced,
            "opened": opened,
            "clicked": clicked,
            "complained": complained,
            "bounce_rate_pct": bounce_rate,
            "open_rate_pct": open_rate,
            "last_event_type": last_event["type"] if last_event else None,
            "last_event_at": last_event["received_at"].isoformat() if last_event and isinstance(last_event.get("received_at"), datetime) else None,
            "webhook_configured": bool(RESEND_WEBHOOK_SECRET),
        },
    }



def _serialize_doc(doc: dict[str, Any]) -> dict[str, Any]:
    """Prepare a MongoDB doc for JSON output — strip _id and ISO-format dates."""
    out = {k: v for k, v in doc.items() if k != "_id"}
    for k, v in list(out.items()):
        if isinstance(v, datetime):
            out[k] = v.isoformat()
    return out


@app.get("/api/admin/feedback", dependencies=[Depends(require_admin)])
async def admin_feedback(limit: int = 20, skip: int = 0, only_open: bool = False) -> dict[str, Any]:
    """Most recent feedback submissions, newest first.

    Pagination: supply ``skip`` and ``limit`` (max 100). Set ``only_open=true``
    to hide items already marked resolved.
    """
    limit = max(1, min(limit, 100))
    skip = max(0, skip)
    query: dict[str, Any] = {"resolved": {"$ne": True}} if only_open else {}
    total = await db.feedback.count_documents(query)
    cursor = db.feedback.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    items = [_serialize_doc(d) async for d in cursor]
    return {"items": items, "count": len(items), "total": total, "skip": skip, "limit": limit}


@app.get("/api/admin/contacts", dependencies=[Depends(require_admin)])
async def admin_contacts(limit: int = 20, skip: int = 0, only_open: bool = False) -> dict[str, Any]:
    """Most recent contact-form submissions, newest first. Same contract as feedback."""
    limit = max(1, min(limit, 100))
    skip = max(0, skip)
    query: dict[str, Any] = {"resolved": {"$ne": True}} if only_open else {}
    total = await db.contacts.count_documents(query)
    cursor = db.contacts.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    items = [_serialize_doc(d) async for d in cursor]
    return {"items": items, "count": len(items), "total": total, "skip": skip, "limit": limit}


class ResolvePayload(BaseModel):
    resolved: bool = True


@app.patch("/api/admin/feedback/{ticket_id}", dependencies=[Depends(require_admin)])
async def admin_feedback_resolve(ticket_id: str, payload: ResolvePayload = Body(...)) -> dict[str, Any]:
    r = await db.feedback.update_one({"ticket_id": ticket_id}, {"$set": {"resolved": payload.resolved, "resolved_at": _now() if payload.resolved else None}})
    if r.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"status": "ok", "ticket_id": ticket_id, "resolved": payload.resolved}


@app.patch("/api/admin/contacts/{ticket_id}", dependencies=[Depends(require_admin)])
async def admin_contact_resolve(ticket_id: str, payload: ResolvePayload = Body(...)) -> dict[str, Any]:
    r = await db.contacts.update_one({"ticket_id": ticket_id}, {"$set": {"resolved": payload.resolved, "resolved_at": _now() if payload.resolved else None}})
    if r.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"status": "ok", "ticket_id": ticket_id, "resolved": payload.resolved}


@app.get("/api/admin/subscribers.csv", dependencies=[Depends(require_admin)])
async def admin_subscribers_csv(status: str = "confirmed") -> PlainTextResponse:
    """Download the subscriber list as CSV. Filters by ``status`` (default:
    confirmed). Pass ``status=all`` to export everyone.

    Columns: email, first_name, status, source, created_at, confirmed_at, unsubscribed_at
    """
    query: dict[str, Any] = {} if status == "all" else {"status": status}
    cursor = db.subscribers.find(query, {"_id": 0}).sort("created_at", -1)

    def _iso(v: Any) -> str:
        return v.isoformat() if isinstance(v, datetime) else ("" if v is None else str(v))

    def _csv_cell(v: Any) -> str:
        s = _iso(v).replace('"', '""')
        return f'"{s}"' if ("," in s or '"' in s or "\n" in s) else s

    rows: list[str] = ['email,first_name,status,source,created_at,confirmed_at,unsubscribed_at']
    count = 0
    async for sub in cursor:
        rows.append(",".join([
            _csv_cell(sub.get("email")),
            _csv_cell(sub.get("first_name")),
            _csv_cell(sub.get("status")),
            _csv_cell(sub.get("source")),
            _csv_cell(sub.get("created_at")),
            _csv_cell(sub.get("confirmed_at")),
            _csv_cell(sub.get("unsubscribed_at")),
        ]))
        count += 1

    filename = f"liveastrology-subscribers-{status}-{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"
    return PlainTextResponse(
        content="\n".join(rows) + "\n",
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Subscriber-Count": str(count),
        },
    )


# ---------- Admin subscriber-edit endpoints ----------
class SubscriberAction(BaseModel):
    action: Literal["force_unsubscribe", "delete", "resend_confirm"]


@app.get("/api/admin/subscribers", dependencies=[Depends(require_admin)])
async def admin_list_subscribers(limit: int = 50, skip: int = 0, status: str = "all") -> dict[str, Any]:
    """Paginated subscriber list for the admin UI. Same contract as the feedback/contact queues."""
    limit = max(1, min(limit, 200))
    skip = max(0, skip)
    query: dict[str, Any] = {} if status == "all" else {"status": status}
    total = await db.subscribers.count_documents(query)
    projection = {"_id": 0, "confirm_token": 0, "unsub_token": 0}
    cursor = db.subscribers.find(query, projection).sort("created_at", -1).skip(skip).limit(limit)
    items = [_serialize_doc(d) async for d in cursor]
    return {"items": items, "count": len(items), "total": total, "skip": skip, "limit": limit}


@app.post("/api/admin/subscribers/{email}/actions", dependencies=[Depends(require_admin)])
async def admin_subscriber_action(email: str, payload: SubscriberAction = Body(...)) -> dict[str, Any]:
    """Mutating admin actions on a single subscriber:

    - ``force_unsubscribe`` — flip status to unsubscribed (no email sent).
    - ``delete``            — hard-delete the row.
    - ``resend_confirm``    — re-send the opt-in email (useful when a user claims they didn't receive it).
    """
    email = email.lower()
    sub = await db.subscribers.find_one({"email": email})
    if not sub:
        raise HTTPException(status_code=404, detail="Subscriber not found")

    if payload.action == "force_unsubscribe":
        await db.subscribers.update_one(
            {"email": email},
            {"$set": {"status": "unsubscribed", "unsubscribed_at": _now(), "updated_at": _now()}},
        )
        return {"status": "ok", "email": email, "action": "force_unsubscribe"}

    if payload.action == "delete":
        await db.subscribers.delete_one({"email": email})
        return {"status": "ok", "email": email, "action": "delete"}

    if payload.action == "resend_confirm":
        if sub.get("status") == "confirmed":
            raise HTTPException(status_code=400, detail="Subscriber is already confirmed")
        confirm_url = f"{APP_ORIGIN}/api/subscribe/confirm?token={sub['confirm_token']}"
        await email_service.send_template(
            "subscribe_confirm",
            to=email,
            list_unsubscribe=_unsub_url(sub["unsub_token"]),
            first_name=sub.get("first_name") or _first_name(None, email),
            email=email,
            confirm_url=confirm_url,
            unsubscribe_url=_unsub_url(sub["unsub_token"]),
        )
        return {"status": "ok", "email": email, "action": "resend_confirm"}

    raise HTTPException(status_code=400, detail=f"Unknown action: {payload.action}")


# ---------- Resend webhook ingestion ----------
# Resend posts deliverability events here (configured at https://resend.com/webhooks).
# Signed with Svix headers (svix-id / svix-timestamp / svix-signature). When
# RESEND_WEBHOOK_SECRET is set the payload is cryptographically verified;
# otherwise the request is logged with a warning and accepted (dev mode).
_TRACKED_EVENT_TYPES = {
    "email.sent",
    "email.delivered",
    "email.delivery_delayed",
    "email.bounced",
    "email.opened",
    "email.clicked",
    "email.complained",
}


# ---------- Articles CMS ----------
# Long-form blog content lives in MongoDB so contributors can publish from
# /admin without touching code. The default seed contains the six
# evergreen articles that ship with the app; admins can add, edit, draft,
# and publish more from the dashboard.
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify(s: str) -> str:
    s = _SLUG_RE.sub("-", s.lower()).strip("-")
    return s[:90] or _short_id("post", 6).lower()


# Seed-articles payload — kept inline (not a separate file) so the seed
# endpoint works on production without needing the migration package
# inside the deploy bundle.
_SEED_ARTICLES: list[dict[str, Any]] = [
    {"title": "Understanding Your Sun Sign: The Core of Your Astrological Identity",
     "category": "Astrology Basics", "author": "Celestial Insights",
     "tags": ["sun sign", "zodiac", "astrology basics", "self discovery"],
     "read_time": "9 min read", "published_at": datetime(2024, 12, 15, tzinfo=timezone.utc)},
    {"title": "Moon Sign vs Rising Sign: What's the Difference?",
     "category": "Astrology Basics", "author": "Stellar Guide",
     "tags": ["moon sign", "rising sign", "ascendant", "birth chart"],
     "read_time": "11 min read", "published_at": datetime(2024, 12, 10, tzinfo=timezone.utc)},
    {"title": "How Venus and Mars Influence Your Love Life",
     "category": "Love & Relationships", "author": "Cosmic Love",
     "tags": ["venus", "mars", "romance", "compatibility", "love"],
     "read_time": "12 min read", "published_at": datetime(2024, 12, 5, tzinfo=timezone.utc)},
    {"title": "Mercury Retrograde: Cycles, Myths, and How to Actually Use Them",
     "category": "Astrology Basics", "author": "Celestial Insights",
     "tags": ["mercury", "retrograde", "communication", "astrology cycles"],
     "read_time": "11 min read", "published_at": datetime(2024, 11, 28, tzinfo=timezone.utc)},
    {"title": "The 12 Houses of Astrology Explained",
     "category": "Astrology Basics", "author": "Stellar Guide",
     "tags": ["houses", "birth chart", "astrology basics", "natal chart"],
     "read_time": "13 min read", "published_at": datetime(2024, 11, 22, tzinfo=timezone.utc)},
    {"title": "Saturn Returns: Why Your Late 20s Feel Like a Tear-Down",
     "category": "Astrology Basics", "author": "Celestial Insights",
     "tags": ["saturn return", "transits", "life cycles", "astrology basics"],
     "read_time": "12 min read", "published_at": datetime(2024, 11, 18, tzinfo=timezone.utc)},
]


@app.post("/api/admin/seed-articles", dependencies=[Depends(require_seo_or_admin)])
async def seed_articles_endpoint(force: bool = False) -> dict[str, Any]:
    """One-shot seeder for production. Idempotent: skips when the
    collection already has documents (unless ``force=true`` is passed,
    which still avoids slug collisions but seeds the missing ones).

    Usage:
        curl -X POST -H "Authorization: Bearer $ADMIN" \\
             https://liveastrology.app/api/admin/seed-articles
    """
    existing_count = await db.articles.count_documents({})
    if existing_count > 0 and not force:
        return {"status": "skipped", "reason": "articles collection already populated",
                "existing_count": existing_count, "inserted": 0}

    inserted = 0
    skipped: list[str] = []
    for stub in _SEED_ARTICLES:
        slug = _slugify(stub["title"])
        if await db.articles.find_one({"slug": slug}, {"_id": 1}):
            skipped.append(slug)
            continue
        published_at: datetime = stub["published_at"]
        await db.articles.insert_one({
            "slug": slug,
            "title": stub["title"],
            "excerpt": f"Editorial article in the {stub['category']} series. Open the article on the site to read the full text.",
            "content": f"# {stub['title']}\n\nThis article is currently maintained in the frontend codebase. Edit it via /admin → Articles to publish a database-backed version.",
            "author": stub["author"],
            "category": stub["category"],
            "tags": stub["tags"],
            "read_time": stub["read_time"],
            "word_count": 0,
            "status": "published",
            "created_at": published_at,
            "updated_at": published_at,
            "published_at": published_at,
        })
        inserted += 1

    return {"status": "ok", "inserted": inserted, "skipped": skipped, "total_now": existing_count + inserted}


@app.post("/api/admin/seed-seo-articles", dependencies=[Depends(require_seo_or_admin)])
async def seed_seo_articles_endpoint(force: bool = False) -> dict[str, Any]:
    """Insert the 5 long-form SEO articles (Moon in Scorpio, Big Three
    comparison, no-signup positioning, beginner birth-chart guides) into
    the Articles CMS. Idempotent by slug — re-running this endpoint
    skips articles that already exist. ``force=true`` will overwrite the
    existing rows with the latest copy from ``seo_articles.py``.
    """
    from seo_articles import SEO_ARTICLES  # local import for hot-reload friendliness

    inserted: list[str] = []
    updated: list[str] = []
    skipped: list[str] = []
    for art in SEO_ARTICLES:
        slug = _slugify(art["title"])
        existing = await db.articles.find_one({"slug": slug}, {"_id": 1})
        word_count = len(re.findall(r"\S+", art["content"]))
        doc = {
            "slug": slug,
            "title": art["title"],
            "excerpt": art["excerpt"],
            "content": art["content"],
            "author": art["author"],
            "category": art["category"],
            "tags": art["tags"],
            "read_time": art["read_time"],
            "word_count": word_count,
            "status": "published",
            "published_at": art["published_at"],
            "updated_at": _now(),
        }
        if existing and not force:
            skipped.append(slug)
            continue
        if existing and force:
            await db.articles.update_one({"slug": slug}, {"$set": doc})
            updated.append(slug)
        else:
            doc["created_at"] = art["published_at"]
            await db.articles.insert_one(doc)
            inserted.append(slug)

    return {
        "status": "ok",
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
        "total_now": await db.articles.count_documents({}),
    }


class ArticleIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    excerpt: str = Field(min_length=10, max_length=600)
    content: str = Field(min_length=100)
    author: str = Field(min_length=1, max_length=80)
    category: str = Field(min_length=1, max_length=80)
    tags: list[str] = Field(default_factory=list, max_length=20)
    read_time: str = Field(default="", max_length=40)
    status: str = Field(default="published")  # 'draft' | 'published'
    slug: str | None = None


class ArticleUpdate(BaseModel):
    title: str | None = None
    excerpt: str | None = None
    content: str | None = None
    author: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    read_time: str | None = None
    status: str | None = None


def _article_doc(payload: ArticleIn, slug: str) -> dict[str, Any]:
    now = _now()
    word_count = len(re.findall(r"\S+", payload.content))
    if not payload.read_time:
        # 220 wpm reading speed, rounded up.
        minutes = max(1, round(word_count / 220))
        read_time = f"{minutes} min read"
    else:
        read_time = payload.read_time
    return {
        "slug": slug,
        "title": payload.title.strip(),
        "excerpt": payload.excerpt.strip(),
        "content": payload.content.strip(),
        "author": payload.author.strip(),
        "category": payload.category.strip(),
        "tags": [t.strip() for t in payload.tags if t.strip()],
        "read_time": read_time,
        "word_count": word_count,
        "status": payload.status if payload.status in {"draft", "published"} else "published",
        "created_at": now,
        "updated_at": now,
        "published_at": now if payload.status == "published" else None,
    }


@app.get("/api/articles")
async def list_articles_public(limit: int = 50) -> list[dict[str, Any]]:
    cursor = db.articles.find(
        {"status": "published"},
        {"_id": 0, "content": 0},  # excerpts only on the list endpoint
    ).sort("published_at", -1).limit(min(max(limit, 1), 100))
    items = []
    async for doc in cursor:
        for k in ("created_at", "updated_at", "published_at"):
            if isinstance(doc.get(k), datetime):
                doc[k] = doc[k].isoformat()
        items.append(doc)
    return items


async def _published_articles_for_feed(limit: int = 50) -> list[dict[str, Any]]:
    """Pull up to ``limit`` newest published articles as raw dicts (with
    datetime objects intact). Used by the RSS + Atom feed builders."""
    cursor = db.articles.find(
        {"status": "published"},
        {"_id": 0, "content": 0},
    ).sort("published_at", -1).limit(min(max(limit, 1), 100))
    return [doc async for doc in cursor]


@app.get("/api/feed.xml")
async def rss_feed() -> PlainTextResponse:
    """RSS 2.0 feed of the 50 most recent published articles."""
    articles = await _published_articles_for_feed(limit=50)
    xml = feeds_module.build_rss(articles)
    return PlainTextResponse(
        xml,
        media_type="application/rss+xml; charset=utf-8",
        headers={"Cache-Control": "public, max-age=900"},
    )


@app.get("/api/atom.xml")
async def atom_feed() -> PlainTextResponse:
    """Atom 1.0 feed of the 50 most recent published articles."""
    articles = await _published_articles_for_feed(limit=50)
    xml = feeds_module.build_atom(articles)
    return PlainTextResponse(
        xml,
        media_type="application/atom+xml; charset=utf-8",
        headers={"Cache-Control": "public, max-age=900"},
    )


# ---------- IndexNow (instant URL indexing on Bing / Yandex / Seznam / Naver) ----------
@app.get("/api/indexnow-key.txt")
async def indexnow_key_file() -> PlainTextResponse:
    """Plain-text verification file referenced by IndexNow's ``keyLocation``.

    Search engines fetch this URL and compare its body against the
    ``key`` in our POST payload. The contents must equal the key
    exactly — no whitespace, no newlines.
    """
    key = os.environ.get("INDEXNOW_KEY", "").strip()
    if not key:
        raise HTTPException(status_code=404, detail="INDEXNOW_KEY not configured")
    return PlainTextResponse(key, media_type="text/plain; charset=utf-8")


class IndexNowSubmitIn(BaseModel):
    urls: list[Annotated[str, Field(min_length=1, max_length=2000)]] = Field(min_length=1, max_length=10000)


@app.post("/api/admin/indexnow/submit", dependencies=[Depends(require_seo_or_admin)])
async def indexnow_submit(payload: IndexNowSubmitIn = Body(...)) -> dict[str, Any]:
    """Manually submit a list of URLs to IndexNow.

    Use this to (a) reindex after a site-wide change, or (b) bulk-submit
    older articles you want recrawled. Daily limit per the spec is
    10,000 URLs; we cap the request body at the same number.
    """
    return await indexnow_module.submit(payload.urls)


# ---------- Google Indexing API ----------
class GoogleIndexingSubmitIn(BaseModel):
    url: Annotated[str, Field(min_length=1, max_length=2000)]
    action: Annotated[str, Field(pattern="^(URL_UPDATED|URL_DELETED)$")] = "URL_UPDATED"


@app.post("/api/admin/google-indexing/submit", dependencies=[Depends(require_seo_or_admin)])
async def google_indexing_submit(payload: GoogleIndexingSubmitIn = Body(...)) -> dict[str, Any]:
    """Manually notify Google's Indexing API of a single URL.

    Auto-pings already fire on article publish — this endpoint is for
    one-off reindex requests (e.g. when a static page is significantly
    rewritten, or to seed the queue with existing URLs).
    """
    return await google_indexing_module.submit(payload.url, action=payload.action)


@app.get("/api/articles/{slug}")
async def get_article_public(slug: str) -> dict[str, Any]:
    doc = await db.articles.find_one({"slug": slug, "status": "published"}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Article not found")
    for k in ("created_at", "updated_at", "published_at"):
        if isinstance(doc.get(k), datetime):
            doc[k] = doc[k].isoformat()
    return doc


@app.get("/api/admin/articles", dependencies=[Depends(require_seo_or_admin)])
async def list_articles_admin() -> list[dict[str, Any]]:
    cursor = db.articles.find({}, {"_id": 0, "content": 0}).sort("updated_at", -1)
    items = []
    async for doc in cursor:
        for k in ("created_at", "updated_at", "published_at"):
            if isinstance(doc.get(k), datetime):
                doc[k] = doc[k].isoformat()
        items.append(doc)
    return items


@app.get("/api/admin/articles/{slug}", dependencies=[Depends(require_seo_or_admin)])
async def get_article_admin(slug: str) -> dict[str, Any]:
    doc = await db.articles.find_one({"slug": slug}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Article not found")
    for k in ("created_at", "updated_at", "published_at"):
        if isinstance(doc.get(k), datetime):
            doc[k] = doc[k].isoformat()
    return doc


async def _record_audit(
    *,
    action: str,
    slug: str,
    actor: str,
    status_value: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """Append a single row to the ``audit_log`` collection.

    Used by the article-write endpoints to record who (admin vs seo)
    did what to which slug, with a UTC timestamp. Failures are logged
    but never raise — the audit log must not break the publish flow.
    """
    try:
        await db.audit_log.insert_one({
            "action": action,
            "slug": slug,
            "actor": actor,          # "admin" or "seo"
            "status": status_value,  # the article status after the action
            "details": details or {},
            "created_at": _now(),
        })
    except Exception as exc:  # noqa: BLE001
        logger.exception("audit_log insert failed: %s", exc)


@app.post("/api/admin/articles", status_code=status.HTTP_201_CREATED)
async def create_article(
    payload: ArticleIn,
    actor: str = Depends(require_seo_or_admin),
) -> dict[str, Any]:
    base_slug = _slugify(payload.slug or payload.title)
    slug = base_slug
    n = 2
    while await db.articles.find_one({"slug": slug}, {"_id": 1}):
        slug = f"{base_slug}-{n}"
        n += 1
    doc = _article_doc(payload, slug)
    await db.articles.insert_one(doc)
    doc.pop("_id", None)
    for k in ("created_at", "updated_at", "published_at"):
        if isinstance(doc.get(k), datetime):
            doc[k] = doc[k].isoformat()
    await _record_audit(
        action="create",
        slug=slug,
        actor=actor,
        status_value=doc.get("status"),
        details={"title": doc.get("title"), "word_count": doc.get("word_count")},
    )
    if doc.get("status") == "published":
        await indexnow_module.submit_in_background([
            indexnow_module.url_for_article(slug),
            indexnow_module.SITEMAP_URL,
        ])
        await google_indexing_module.submit_in_background(
            indexnow_module.url_for_article(slug)
        )
    return doc


@app.patch("/api/admin/articles/{slug}")
async def update_article(
    slug: str,
    patch: ArticleUpdate,
    actor: str = Depends(require_seo_or_admin),
) -> dict[str, Any]:
    existing = await db.articles.find_one({"slug": slug}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Article not found")
    update_fields: dict[str, Any] = {}
    for field in ("title", "excerpt", "content", "author", "category", "read_time", "status"):
        v = getattr(patch, field)
        if v is not None:
            update_fields[field] = v.strip() if isinstance(v, str) else v
    if patch.tags is not None:
        update_fields["tags"] = [t.strip() for t in patch.tags if t.strip()]
    if patch.content is not None:
        update_fields["word_count"] = len(re.findall(r"\S+", patch.content))
        if not (patch.read_time or existing.get("read_time")):
            minutes = max(1, round(update_fields["word_count"] / 220))
            update_fields["read_time"] = f"{minutes} min read"
    newly_published = False
    if patch.status is not None:
        if patch.status not in {"draft", "published"}:
            raise HTTPException(status_code=400, detail="status must be 'draft' or 'published'")
        if patch.status == "published" and not existing.get("published_at"):
            update_fields["published_at"] = _now()
            newly_published = True
    update_fields["updated_at"] = _now()

    await db.articles.update_one({"slug": slug}, {"$set": update_fields})
    doc = await db.articles.find_one({"slug": slug}, {"_id": 0})
    for k in ("created_at", "updated_at", "published_at"):
        if isinstance(doc.get(k), datetime):
            doc[k] = doc[k].isoformat()
    await _record_audit(
        action="update",
        slug=slug,
        actor=actor,
        status_value=doc.get("status"),
        details={
            "fields_changed": [k for k in update_fields if k != "updated_at"],
            "newly_published": newly_published,
        },
    )
    # Re-ping IndexNow + Google when the article transitions into "published".
    if newly_published or (patch.content is not None and doc.get("status") == "published"):
        await indexnow_module.submit_in_background([
            indexnow_module.url_for_article(slug),
            indexnow_module.SITEMAP_URL,
        ])
        await google_indexing_module.submit_in_background(
            indexnow_module.url_for_article(slug)
        )
    return doc


@app.delete("/api/admin/articles/{slug}")
async def delete_article(
    slug: str,
    actor: str = Depends(require_seo_or_admin),
) -> dict[str, Any]:
    res = await db.articles.delete_one({"slug": slug})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Article not found")
    await _record_audit(action="delete", slug=slug, actor=actor)
    return {"status": "deleted", "slug": slug}


@app.get("/api/admin/audit-log", dependencies=[Depends(require_admin)])
async def list_audit_log(
    limit: int = 50,
    skip: int = 0,
    actor: str | None = None,
    action: str | None = None,
    slug: str | None = None,
) -> dict[str, Any]:
    """Forensic trail of every article create / update / delete, with the
    token type used. Admin-only (the SEO token can't read its own usage).

    Query params:
      - ``limit``  (default 50, max 200)
      - ``skip``   (default 0)
      - ``actor``  "admin" or "seo" — filter by token type
      - ``action`` "create" | "update" | "delete" — filter by action
      - ``slug``   exact slug match
    """
    query: dict[str, Any] = {}
    if actor:
        query["actor"] = actor
    if action:
        query["action"] = action
    if slug:
        query["slug"] = slug

    total = await db.audit_log.count_documents(query)
    capped_limit = min(max(limit, 1), 200)
    cursor = (
        db.audit_log.find(query, {"_id": 0})
        .sort("created_at", -1)
        .skip(max(skip, 0))
        .limit(capped_limit)
    )
    items = []
    async for doc in cursor:
        if isinstance(doc.get("created_at"), datetime):
            doc["created_at"] = doc["created_at"].isoformat()
        items.append(doc)
    return {
        "total": total,
        "count": len(items),
        "limit": capped_limit,
        "skip": max(skip, 0),
        "items": items,
    }


# ---------- Resend webhook ingestion ----------
@app.post("/api/webhooks/resend", status_code=status.HTTP_202_ACCEPTED)
async def resend_webhook(request: Request) -> dict[str, Any]:
    raw = await request.body()

    if RESEND_WEBHOOK_SECRET:
        from svix.webhooks import Webhook, WebhookVerificationError  # local import: optional dep at runtime
        headers = {
            "svix-id":        request.headers.get("svix-id", ""),
            "svix-timestamp": request.headers.get("svix-timestamp", ""),
            "svix-signature": request.headers.get("svix-signature", ""),
        }
        try:
            Webhook(RESEND_WEBHOOK_SECRET).verify(raw, headers)
        except WebhookVerificationError as exc:
            logger.warning("Resend webhook signature verification failed: %s", exc)
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
    else:
        logger.warning("Resend webhook received without RESEND_WEBHOOK_SECRET configured — accepting unverified payload")

    try:
        body = await request.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Resend webhook: invalid JSON: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = body.get("type", "unknown")
    data = body.get("data") or {}
    email_id = data.get("email_id") or data.get("id")
    to_field = data.get("to")
    if isinstance(to_field, list):
        recipient = to_field[0] if to_field else None
    else:
        recipient = to_field

    await db.email_events.insert_one({
        "type": event_type,
        "email_id": email_id,
        "to": recipient,
        "subject": data.get("subject"),
        "from": data.get("from"),
        "tags": data.get("tags"),
        "raw": body,
        "received_at": _now(),
    })

    if event_type not in _TRACKED_EVENT_TYPES:
        logger.info("Resend webhook: untracked event type %s", event_type)

    return {"status": "ok", "event": event_type}

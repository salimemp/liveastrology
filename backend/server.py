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
import secrets
import string
from datetime import datetime, timezone
from typing import Annotated, Any, Literal

from dotenv import load_dotenv
from fastapi import Body, Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

import email_service
import scheduler as scheduler_module
import turnstile as turnstile_module

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("liveastrology")

# ---------- Config ----------
APP_ORIGIN    = os.environ.get("APP_ORIGIN", "https://liveastrology.app").rstrip("/")
NOTIFY_EMAIL  = os.environ.get("NOTIFY_EMAIL", "notify@liveastrology.app")
MONGO_URL     = os.environ["MONGO_URL"]
DB_NAME       = os.environ["DB_NAME"]
ADMIN_SECRET  = os.environ.get("ADMIN_SECRET", "")

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


limiter = Limiter(key_func=_client_ip, default_limits=["120/minute"])

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


def require_admin(authorization: str = Header(default="")) -> None:
    """Shared-secret bearer auth for admin-only endpoints."""
    if not ADMIN_SECRET:
        raise HTTPException(status_code=503, detail="ADMIN_SECRET is not configured")
    expected = f"Bearer {ADMIN_SECRET}"
    if authorization != expected:
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
    category: Annotated[Literal["general", "bug", "feature", "content", "praise"], Field(default="general")] = "general"
    message: Annotated[str, Field(min_length=10, max_length=4000)]
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
        "category": payload.category,
        "message": payload.message,
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

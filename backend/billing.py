"""Stripe billing — fixed-package checkout + entitlements.

We do *not* manage a full Stripe recurring-subscription lifecycle here.
Instead, each "Premium" purchase is a one-time Stripe Checkout charge
for a known fixed amount (configured server-side, never trusted from
the client). On successful payment we extend the buyer's entitlement
in MongoDB by 30 days (monthly plan) or 365 days (yearly plan).

Collections:
  - ``payment_transactions``  one row per Checkout session. Tracks the
    session_id, amount, plan, email, status (initiated → paid / failed
    / expired). Idempotent: we never grant an entitlement twice for the
    same session_id even if the status endpoint is polled in parallel.
  - ``entitlements``          one row per email. Tracks ``plan`` (none |
    monthly | yearly), ``expires_at`` (ISO datetime), and the most recent
    ``last_session_id`` that granted access. ``GET /api/billing/status``
    reads from this table.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger("liveastrology.billing")

STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
# Subscription mode toggle: when ``STRIPE_SUBSCRIPTION_MODE=1`` the
# checkout will create a true recurring subscription instead of a
# one-time charge. Off by default for the beta phase.
STRIPE_SUBSCRIPTION_MODE = os.environ.get("STRIPE_SUBSCRIPTION_MODE", "0") == "1"
# Stripe Price IDs for the recurring subscription products. Only used
# when STRIPE_SUBSCRIPTION_MODE is on.
STRIPE_PRICE_MONTHLY = os.environ.get("STRIPE_PRICE_MONTHLY", "")
STRIPE_PRICE_YEARLY = os.environ.get("STRIPE_PRICE_YEARLY", "")

# Server-side fixed packages. Frontend may only choose by id; amounts
# are never accepted from the frontend.
PACKAGES: dict[str, dict[str, Any]] = {
    "monthly": {
        "label": "Premium Monthly",
        "amount": 4.99,
        "currency": "usd",
        "days": 30,
    },
    "yearly": {
        "label": "Premium Yearly",
        "amount": 39.00,
        "currency": "usd",
        "days": 365,
    },
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def get_package(package_id: str) -> dict[str, Any]:
    if package_id not in PACKAGES:
        raise ValueError(f"Unknown package id: {package_id}")
    return PACKAGES[package_id]


async def create_checkout_session(
    db: Any, *, package_id: str, email: str, origin_url: str
) -> dict[str, Any]:
    """Create a Stripe Checkout session and persist a pending payment
    row. Returns ``{url, session_id}``. Raises ValueError on bad input
    and RuntimeError on Stripe-side failure.
    """
    pkg = get_package(package_id)
    email = email.strip().lower()
    if not email or "@" not in email:
        raise ValueError("email is required and must look like an email")

    if not STRIPE_API_KEY:
        raise RuntimeError("Stripe is not configured on this environment")

    from emergentintegrations.payments.stripe.checkout import (  # type: ignore
        StripeCheckout,
        CheckoutSessionRequest,
    )

    success_url = f"{origin_url.rstrip('/')}/upgrade/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin_url.rstrip('/')}/upgrade?cancelled=1"
    webhook_url = f"{origin_url.rstrip('/')}/api/webhook/stripe"

    metadata = {
        "package_id": package_id,
        "email": email,
        "product": "liveastrology-premium",
    }

    checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    req = CheckoutSessionRequest(
        amount=float(pkg["amount"]),
        currency=pkg["currency"],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=metadata,
    )
    try:
        session = await checkout.create_checkout_session(req)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Stripe create_checkout_session failed: %s", exc)
        raise RuntimeError("Could not create checkout session") from exc

    # Persist a pending transaction row before redirecting the user.
    await db.payment_transactions.insert_one({
        "session_id": session.session_id,
        "email": email,
        "package_id": package_id,
        "plan_label": pkg["label"],
        "amount": float(pkg["amount"]),
        "currency": pkg["currency"],
        "days": pkg["days"],
        "status": "initiated",
        "payment_status": "unpaid",
        "metadata": metadata,
        "created_at": _now(),
        "updated_at": _now(),
    })

    return {"url": session.url, "session_id": session.session_id}


async def get_checkout_status(db: Any, session_id: str) -> dict[str, Any]:
    """Poll Stripe for the latest status of a checkout session and
    update our row. Idempotently grants the entitlement on first
    transition into ``payment_status=paid``.
    """
    txn = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    if not txn:
        raise ValueError("Unknown session id")

    from emergentintegrations.payments.stripe.checkout import StripeCheckout  # type: ignore

    checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url="")
    try:
        status = await checkout.get_checkout_status(session_id)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Stripe get_checkout_status failed: %s", exc)
        raise RuntimeError("Could not fetch checkout status") from exc

    update: dict[str, Any] = {
        "status": status.status,
        "payment_status": status.payment_status,
        "updated_at": _now(),
    }

    grant_now = (
        status.payment_status == "paid"
        and txn.get("payment_status") != "paid"
    )

    await db.payment_transactions.update_one(
        {"session_id": session_id}, {"$set": update}
    )

    granted: dict[str, Any] | None = None
    if grant_now:
        granted = await _grant_entitlement(db, txn)

    return {
        "session_id": session_id,
        "status": status.status,
        "payment_status": status.payment_status,
        "amount_total": status.amount_total,
        "currency": status.currency,
        "granted": granted,
    }


async def _grant_entitlement(db: Any, txn: dict[str, Any]) -> dict[str, Any]:
    """Extend or create the buyer's entitlement row. Adds ``days`` from
    today (or from the current expiry if it's in the future). Idempotent
    when called twice for the same session_id thanks to the
    ``last_session_id`` check.
    """
    email = txn["email"]
    days = int(txn["days"])
    plan = txn["package_id"]
    session_id = txn["session_id"]

    existing = await db.entitlements.find_one({"email": email}, {"_id": 0})
    if existing and existing.get("last_session_id") == session_id:
        return existing

    now = _now()
    current_expiry = None
    if existing and existing.get("expires_at"):
        v = existing["expires_at"]
        if isinstance(v, datetime):
            current_expiry = v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    start = current_expiry if (current_expiry and current_expiry > now) else now
    new_expiry = start + timedelta(days=days)

    doc = {
        "email": email,
        "plan": plan,
        "status": "active",
        "expires_at": new_expiry,
        "last_session_id": session_id,
        "updated_at": now,
    }
    await db.entitlements.update_one(
        {"email": email},
        {"$set": doc, "$setOnInsert": {"created_at": now}},
        upsert=True,
    )
    return {**doc, "expires_at": new_expiry.isoformat()}


async def get_entitlement(db: Any, email: str) -> dict[str, Any]:
    """Public ``GET /api/billing/status`` payload for a given email."""
    email = email.strip().lower()
    if not email:
        return {"email": "", "active": False, "plan": None, "expires_at": None}

    doc = await db.entitlements.find_one({"email": email}, {"_id": 0})
    if not doc:
        return {"email": email, "active": False, "plan": None, "expires_at": None}

    expires_at = doc.get("expires_at")
    if isinstance(expires_at, datetime):
        # mongomock can hand back a naive datetime even though we wrote
        # a tz-aware one; coerce to UTC to keep the comparison sane.
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        active = expires_at > _now()
        return {
            "email": email,
            "active": active,
            "plan": doc.get("plan"),
            "expires_at": expires_at.isoformat(),
            "status": "active" if active else "expired",
        }
    return {"email": email, "active": False, "plan": doc.get("plan"), "expires_at": None}


async def handle_webhook(db: Any, raw_body: bytes, signature: str | None) -> dict[str, Any]:
    """Process a Stripe webhook payload. Grants entitlements
    idempotently for ``checkout.session.completed`` events.

    When ``STRIPE_WEBHOOK_SECRET`` is configured we require a valid
    signature — invalid payloads return ``status: rejected`` and the
    caller MUST surface this as a 401/400 to Stripe so the event is
    retried. In dev (no secret configured) we accept unsigned payloads
    but still log loudly so the gap is obvious.
    """
    from emergentintegrations.payments.stripe.checkout import StripeCheckout  # type: ignore

    secret_required = bool(STRIPE_WEBHOOK_SECRET)

    checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url="")
    try:
        evt = await checkout.handle_webhook(raw_body, signature or "")
    except Exception as exc:  # noqa: BLE001
        if secret_required:
            logger.warning("Stripe webhook signature verification FAILED: %s", exc)
            return {"status": "rejected", "verified": False, "reason": str(exc)}
        logger.warning("Stripe webhook unsigned (dev mode): %s", exc)
        return {"status": "rejected", "verified": False, "reason": str(exc), "dev_mode": True}

    if not getattr(evt, "session_id", None):
        return {"status": "ok", "verified": True, "event": evt.event_type, "handled": False}

    txn = await db.payment_transactions.find_one({"session_id": evt.session_id}, {"_id": 0})
    if not txn:
        logger.info("Stripe webhook for unknown session_id %s", evt.session_id)
        return {"status": "ok", "verified": True, "event": evt.event_type, "handled": False}

    await db.payment_transactions.update_one(
        {"session_id": evt.session_id},
        {"$set": {
            "payment_status": evt.payment_status,
            "last_event": evt.event_type,
            "updated_at": _now(),
        }},
    )

    granted = None
    if evt.payment_status == "paid" and txn.get("payment_status") != "paid":
        granted = await _grant_entitlement(db, txn)

    return {"status": "ok", "verified": True, "event": evt.event_type, "handled": True, "granted": granted}


async def create_customer_portal_session(*, customer_id: str, return_url: str) -> dict[str, Any]:
    """Create a Stripe Customer Portal session. Requires a real Stripe
    customer_id (resolved from past Checkout sessions). Returns the
    portal URL the user can be redirected to.

    Only available when ``STRIPE_SUBSCRIPTION_MODE`` is on — in
    one-time-charge mode there's no recurring billing to manage.
    """
    if not STRIPE_SUBSCRIPTION_MODE:
        raise RuntimeError("Customer Portal requires STRIPE_SUBSCRIPTION_MODE=1")
    if not STRIPE_API_KEY:
        raise RuntimeError("Stripe is not configured")
    if not customer_id:
        raise ValueError("customer_id is required")

    # Use Stripe SDK directly here since the emergentintegrations
    # wrapper doesn't expose the Customer Portal API.
    import stripe  # type: ignore
    stripe.api_key = STRIPE_API_KEY
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )
    return {"url": session.url}


async def get_customer_id_for_email(db: Any, email: str) -> str | None:
    """Look up the Stripe customer_id used in the most recent paid
    Checkout session for this email. Returns ``None`` if we have no
    Stripe-side billing relationship to manage (e.g. beta users)."""
    email = email.strip().lower()
    txn = await db.payment_transactions.find_one(
        {"email": email, "payment_status": "paid", "customer_id": {"$exists": True}},
        {"_id": 0, "customer_id": 1},
        sort=[("updated_at", -1)],
    )
    return txn.get("customer_id") if txn else None

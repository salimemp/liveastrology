"""Beta launch — first 100 users get free Premium.

While Stripe payments are disabled for the public launch, eligible
visitors can claim a free 90-day Premium entitlement on a
first-come, first-served basis. The cap, counter, and grant logic
all live here.

Endpoints (defined in server.py, just calling into this module):
  - GET  /api/beta/status  → seats remaining, total, claimed-by-me
  - POST /api/beta/claim   → email-based claim, returns the granted
                              entitlement or a 409 if all seats are
                              taken (with waitlist position).

A claim is idempotent for the same email — repeated calls return the
existing entitlement instead of consuming an extra seat.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger("liveastrology.beta")

# Configurable via env so we can extend mid-campaign without a deploy.
BETA_TOTAL_SEATS = int(os.environ.get("BETA_TOTAL_SEATS", "100"))
BETA_DURATION_DAYS = int(os.environ.get("BETA_DURATION_DAYS", "90"))


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def get_status(db: Any, email: str | None = None) -> dict[str, Any]:
    """Public counter — used by the /upgrade page to switch between
    'Claim free beta access' and 'Join the waitlist'."""
    claimed = await db.beta_claims.count_documents({})
    waitlisted = await db.beta_waitlist.count_documents({})
    me: dict[str, Any] | None = None
    if email:
        email = email.strip().lower()
        c = await db.beta_claims.find_one({"email": email}, {"_id": 0})
        if c:
            ent = await db.entitlements.find_one({"email": email}, {"_id": 0})
            expires = ent.get("expires_at") if ent else None
            if isinstance(expires, datetime):
                expires = expires.isoformat()
            me = {"claimed": True, "expires_at": expires}
        else:
            w = await db.beta_waitlist.find_one({"email": email}, {"_id": 0})
            if w:
                pos = await db.beta_waitlist.count_documents(
                    {"created_at": {"$lte": w["created_at"]}}
                )
                me = {"claimed": False, "waitlist_position": pos}
    return {
        "total_seats": BETA_TOTAL_SEATS,
        "seats_claimed": claimed,
        "seats_remaining": max(0, BETA_TOTAL_SEATS - claimed),
        "waitlist_size": waitlisted,
        "duration_days": BETA_DURATION_DAYS,
        "me": me,
    }


async def claim(db: Any, *, email: str, name: str | None = None) -> dict[str, Any]:
    """Idempotently grant a beta entitlement, or add the email to the
    waitlist if the cap is reached.

    Returns one of:
      ``{result: "granted", expires_at, claim_number, seats_remaining}``
      ``{result: "already_claimed", expires_at}``
      ``{result: "waitlisted", waitlist_position}``
    """
    email = email.strip().lower()
    if not email or "@" not in email:
        raise ValueError("email is required")

    existing = await db.beta_claims.find_one({"email": email}, {"_id": 0})
    if existing:
        ent = await db.entitlements.find_one({"email": email}, {"_id": 0})
        expires = ent.get("expires_at") if ent else None
        return {
            "result": "already_claimed",
            "expires_at": expires.isoformat() if isinstance(expires, datetime) else None,
        }

    # Check the cap atomically-ish — there's a tiny race window but at
    # 100-seat scale it's fine; the cap is a soft business cap.
    claimed_count = await db.beta_claims.count_documents({})
    if claimed_count >= BETA_TOTAL_SEATS:
        # Add to waitlist.
        wl = await db.beta_waitlist.find_one({"email": email}, {"_id": 0})
        if not wl:
            await db.beta_waitlist.insert_one({
                "email": email,
                "name": name,
                "created_at": _now(),
            })
        position = await db.beta_waitlist.count_documents({})
        return {"result": "waitlisted", "waitlist_position": position}

    now = _now()
    expires_at = now + timedelta(days=BETA_DURATION_DAYS)
    claim_number = claimed_count + 1

    await db.beta_claims.insert_one({
        "email": email,
        "name": name,
        "claim_number": claim_number,
        "created_at": now,
        "expires_at": expires_at,
    })

    # Grant a Premium entitlement using the same schema as Stripe purchases.
    await db.entitlements.update_one(
        {"email": email},
        {
            "$set": {
                "email": email,
                "plan": "beta",
                "status": "active",
                "expires_at": expires_at,
                "source": "beta_launch",
                "updated_at": now,
            },
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )

    return {
        "result": "granted",
        "expires_at": expires_at.isoformat(),
        "claim_number": claim_number,
        "seats_remaining": BETA_TOTAL_SEATS - claim_number,
    }

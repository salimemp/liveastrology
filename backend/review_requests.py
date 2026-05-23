"""Day-60 review-ask cron.

Sixty days after a beta claim is granted (and at least 30 days before
the 90-day Premium grant expires), we email the user asking for a
Trustpilot review or Product Hunt upvote. Goal: convert engaged
beta users into public social proof before their free window closes.

Idempotency lives in the ``review_requests`` collection — one row per
``email``. Each address is emailed at most once. Re-running the dispatch
is therefore safe.

Configurable knobs (env vars, all optional):
  REVIEW_REQUEST_AFTER_DAYS    default 60  — minimum days since claim
  REVIEW_REQUEST_BEFORE_DAYS   default 7   — minimum days remaining
  REVIEW_TRUSTPILOT_URL        public review URL
  REVIEW_PRODUCTHUNT_URL       public PH URL
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger("liveastrology.review_requests")

REVIEW_AFTER_DAYS = int(os.environ.get("REVIEW_REQUEST_AFTER_DAYS", "60"))
REVIEW_BEFORE_DAYS = int(os.environ.get("REVIEW_REQUEST_BEFORE_DAYS", "7"))
TRUSTPILOT_URL = os.environ.get(
    "REVIEW_TRUSTPILOT_URL",
    "https://www.trustpilot.com/review/liveastrology.app",
)
PRODUCTHUNT_URL = os.environ.get(
    "REVIEW_PRODUCTHUNT_URL",
    "https://www.producthunt.com/products/live-astrology",
)
UNSUBSCRIBE_URL = "https://liveastrology.app/upgrade/manage"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _humanize(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    try:
        return dt.strftime("%B %-d, %Y")
    except ValueError:  # Windows fallback
        return dt.strftime("%B %d, %Y").replace(" 0", " ")


async def dispatch_review_requests(
    db: Any,
    email_sender,  # callable(slug, to, **vars) -> Awaitable[None]
    *,
    when: datetime | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Email every eligible beta claimant a Day-60 review-ask.

    Eligibility (all must hold):
      • beta_claims.created_at <= now - REVIEW_AFTER_DAYS
      • beta_claims.expires_at >= now + REVIEW_BEFORE_DAYS
      • no existing row in ``review_requests`` for this email
    """
    now = when or _now()
    earliest_claim_cutoff = now - timedelta(days=REVIEW_AFTER_DAYS)
    expiry_floor = now + timedelta(days=REVIEW_BEFORE_DAYS)

    cursor = db.beta_claims.find(
        {
            "created_at": {"$lte": earliest_claim_cutoff},
            "expires_at": {"$gte": expiry_floor},
        },
        {"_id": 0, "email": 1, "name": 1, "expires_at": 1},
    )

    sent: list[str] = []
    skipped_existing: list[str] = []
    failed: list[dict[str, Any]] = []
    eligible = 0

    async for claim in cursor:
        eligible += 1
        email = claim.get("email")
        if not email:
            continue

        already = await db.review_requests.find_one({"email": email}, {"_id": 1})
        if already:
            skipped_existing.append(email)
            continue

        if dry_run:
            sent.append(email)
            continue

        expires_at = claim.get("expires_at")
        if isinstance(expires_at, datetime):
            expires_human = _humanize(expires_at)
        else:
            expires_human = "your beta end date"

        display_name = (claim.get("name") or email.split("@", 1)[0]).strip() or "there"

        try:
            await email_sender(
                "premium_review_ask",
                to=email,
                name=display_name,
                expires_at_human=expires_human,
                trustpilot_url=TRUSTPILOT_URL,
                producthunt_url=PRODUCTHUNT_URL,
                unsubscribe_url=UNSUBSCRIBE_URL,
            )
            await db.review_requests.insert_one({
                "email": email,
                "sent_at": now,
                "trustpilot_url": TRUSTPILOT_URL,
                "producthunt_url": PRODUCTHUNT_URL,
            })
            sent.append(email)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Day-60 review email failed for %s: %s", email, exc)
            failed.append({"email": email, "error": str(exc)})

    return {
        "eligible": eligible,
        "sent_count": len(sent),
        "skipped_existing": len(skipped_existing),
        "failed": failed,
        "after_days": REVIEW_AFTER_DAYS,
        "before_days": REVIEW_BEFORE_DAYS,
        "dry_run": dry_run,
    }

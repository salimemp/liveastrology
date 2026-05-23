"""Generate the monthly Premium forecast using Claude Sonnet 4.5 and
dispatch it to every active Premium entitlement.

The forecast is a single generic-but-grounded read of the current
month's transits — same content for every recipient. We don't store
user birth data, so there's nothing to personalise off; instead we
write the email as the seasoned-astrologer voice of Live Astrology
covering "the themes the planets are surfacing this month."

Idempotency lives in ``forecast_dispatches`` collection — one row per
``year-month`` keyed cohort. Re-running the dispatch endpoint in the
same month is a no-op (the cached forecast is reused). Override with
``force=True`` if a regenerate is genuinely needed.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("liveastrology.forecast")

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
MODEL_PROVIDER = "anthropic"
MODEL_NAME = "claude-sonnet-4-5-20250929"

_SYSTEM_PROMPT = (
    "You are the lead astrologer at Live Astrology, writing the "
    "monthly Premium forecast for paying subscribers. Voice: warm, "
    "plain-English, never mystical-sounding, never deterministic. "
    "Focus on the *themes* the transits are surfacing this month — "
    "not date-by-date predictions for individual signs."
    "\n\n"
    "Return STRICT JSON in this exact shape:\n"
    "{\n"
    '  "theme_paragraph": "...",  // 110–160 words, the month\'s headline theme\n'
    '  "event_1_date": "Mon D",   // e.g. "Jun 6"\n'
    '  "event_1_text": "...",     // 35–55 words explaining the transit and why it matters\n'
    '  "event_2_date": "Mon D",\n'
    '  "event_2_text": "...",\n'
    '  "event_3_date": "Mon D",\n'
    '  "event_3_text": "...",\n'
    '  "practical_insight": "..." // 70–110 words, one concrete thing readers can do\n'
    "}\n\n"
    "No markdown, no lists, no emojis. Just JSON. Each paragraph reads "
    "as a single block. The three events should be real astrological "
    "happenings (new moon, full moon, planet ingresses, retrogrades) "
    "for the given month, in chronological order."
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _month_key(dt: datetime) -> str:
    return dt.strftime("%Y-%m")


async def get_monthly_forecast(db: Any, *, when: datetime | None = None, force: bool = False) -> dict[str, Any]:
    """Return the forecast for the given month, generating + caching
    via Claude if not already present.
    """
    when = when or _now()
    key = _month_key(when)

    if not force:
        cached = await db.forecast_dispatches.find_one(
            {"month_key": key},
            {"_id": 0, "forecast": 1, "generated_at": 1},
        )
        if cached and cached.get("forecast"):
            return cached["forecast"]

    if not EMERGENT_LLM_KEY:
        raise RuntimeError("EMERGENT_LLM_KEY is not configured")

    from emergentintegrations.llm.chat import LlmChat, UserMessage  # type: ignore

    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"forecast-{key}",
        system_message=_SYSTEM_PROMPT,
    ).with_model(MODEL_PROVIDER, MODEL_NAME)

    user_prompt = (
        f"Write the monthly Premium forecast for {when.strftime('%B %Y')}. "
        "Use real transits visible to a Western tropical astrologer for that "
        "month — new/full moon, planet ingresses, retrograde stations. "
        "Return JSON only."
    )

    try:
        raw = await chat.send_message(UserMessage(text=user_prompt))
    except Exception as exc:  # noqa: BLE001
        logger.exception("LLM monthly forecast call failed: %s", exc)
        raise RuntimeError("Forecast generation failed") from exc

    parsed = _parse_json(raw)
    required = ("theme_paragraph", "event_1_date", "event_1_text",
                "event_2_date", "event_2_text", "event_3_date",
                "event_3_text", "practical_insight")
    if not parsed or not all(k in parsed and isinstance(parsed[k], str) for k in required):
        logger.warning("Forecast LLM returned malformed payload: %s", raw[:300])
        raise RuntimeError("Forecast generation returned an unexpected response")

    forecast = {k: parsed[k].strip() for k in required}
    forecast["month_name"] = when.strftime("%B")
    forecast["year"] = when.strftime("%Y")

    await db.forecast_dispatches.update_one(
        {"month_key": key},
        {
            "$set": {
                "month_key": key,
                "month_name": forecast["month_name"],
                "year": forecast["year"],
                "forecast": forecast,
                "model": f"{MODEL_PROVIDER}/{MODEL_NAME}",
                "generated_at": _now(),
            },
        },
        upsert=True,
    )
    return forecast


async def dispatch_monthly_forecast(
    db: Any,
    email_sender,  # callable(slug, to, **vars) -> Awaitable[None]
    *,
    when: datetime | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Send the monthly forecast to every active Premium entitlement.

    Idempotent: each (month_key, email) pair is recorded in
    ``forecast_recipients`` and never resent. ``force=True`` regenerates
    the AI payload but still skips already-emailed addresses.
    """
    when = when or _now()
    key = _month_key(when)
    forecast = await get_monthly_forecast(db, when=when, force=force)

    cursor = db.entitlements.find(
        {"status": "active"},
        {"_id": 0, "email": 1, "expires_at": 1},
    )
    sent: list[str] = []
    skipped_existing: list[str] = []
    skipped_inactive: list[str] = []
    failed: list[dict[str, Any]] = []

    now = _now()
    async for ent in cursor:
        email = ent.get("email")
        if not email:
            continue
        expires_at = ent.get("expires_at")
        if isinstance(expires_at, datetime):
            ex = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=timezone.utc)
            if ex <= now:
                skipped_inactive.append(email)
                continue

        already = await db.forecast_recipients.find_one(
            {"month_key": key, "email": email}, {"_id": 1}
        )
        if already:
            skipped_existing.append(email)
            continue

        display_name = email.split("@", 1)[0]
        try:
            await email_sender(
                "premium_forecast",
                to=email,
                name=display_name,
                **forecast,
                unsubscribe_url="https://liveastrology.app/upgrade/manage",
            )
            await db.forecast_recipients.insert_one({
                "month_key": key,
                "email": email,
                "sent_at": now,
            })
            sent.append(email)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Forecast send failed for %s: %s", email, exc)
            failed.append({"email": email, "error": str(exc)})

    return {
        "month_key": key,
        "month_name": forecast["month_name"],
        "year": forecast["year"],
        "sent_count": len(sent),
        "skipped_existing": len(skipped_existing),
        "skipped_inactive": len(skipped_inactive),
        "failed": failed,
    }


def _parse_json(raw: str) -> dict[str, Any] | None:
    import json
    import re

    if not raw:
        return None
    candidates: list[str] = []
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.S)
    if fence:
        candidates.append(fence.group(1))
    first = raw.find("{")
    last = raw.rfind("}")
    if first != -1 and last != -1 and last > first:
        candidates.append(raw[first:last + 1])
    candidates.append(raw.strip())
    for c in candidates:
        try:
            obj = json.loads(c)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue
    return None

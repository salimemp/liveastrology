"""Generate and send a Premium compatibility report on demand.

This is admin-driven: a paying user replies to their welcome email
with two birth-detail blocks; an admin pastes them into the admin
dashboard; the backend generates the multi-paragraph reading via
Claude Sonnet 4.5 and sends the rendered Premium template via Resend.

Stored payloads live in ``compatibility_reports`` so we have a record
of every send (audit + idempotency).
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("liveastrology.compatibility")

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
MODEL_PROVIDER = "anthropic"
MODEL_NAME = "claude-sonnet-4-5-20250929"

_VALID_SIGNS = {
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
}

_SYSTEM_PROMPT = (
    "You are the lead astrologer at Live Astrology, writing a Premium "
    "compatibility report for two people. Voice: warm, candid, plain-"
    "English. Never mystical, never deterministic. Honour both the "
    "chemistry and the friction — every pairing has both."
    "\n\n"
    "Return STRICT JSON in this exact shape:\n"
    "{\n"
    '  "headline_paragraph": "...",   // 80–110 words framing the pairing\n'
    '  "sun_sun_paragraph": "...",    // 70–100 words on Sun×Sun dynamic\n'
    '  "moon_moon_paragraph": "...",  // 70–100 words on emotional fit\n'
    '  "venus_mars_paragraph": "...", // 70–100 words on chemistry\n'
    '  "composite_paragraph": "...",  // 80–110 words on the relationship itself\n'
    '  "work_paragraph": "..."        // 70–110 words on the work + the gift\n'
    "}\n"
    "No markdown, no lists, no emojis. JSON only."
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _norm(sign: str) -> str:
    return (sign or "").strip().lower()


def _validate(payload: dict[str, Any]) -> tuple[str, str, str, str, str, str]:
    p1n = (payload.get("person1_name") or "").strip()
    p2n = (payload.get("person2_name") or "").strip()
    p1s = _norm(payload.get("person1_sun"))
    p1m = _norm(payload.get("person1_moon"))
    p2s = _norm(payload.get("person2_sun"))
    p2m = _norm(payload.get("person2_moon"))
    if not (p1n and p2n):
        raise ValueError("Both person names are required")
    for s in (p1s, p1m, p2s, p2m):
        if s not in _VALID_SIGNS:
            raise ValueError(f"Invalid zodiac sign: {s}")
    return p1n, p2n, p1s, p1m, p2s, p2m


async def generate_and_send(
    db: Any,
    email_sender,                 # callable(slug, to, **vars) -> Awaitable
    *,
    recipient_email: str,
    person1_name: str,
    person1_sun: str,
    person1_moon: str,
    person2_name: str,
    person2_sun: str,
    person2_moon: str,
    score: int,
) -> dict[str, Any]:
    """Generate a Premium compatibility report and email it to
    ``recipient_email``. Returns a status dict including the
    persisted record id and the rendered paragraph word counts.
    """
    recipient_email = (recipient_email or "").strip().lower()
    if not recipient_email or "@" not in recipient_email:
        raise ValueError("recipient_email is required")

    p1n, p2n, p1s, p1m, p2s, p2m = _validate({
        "person1_name": person1_name, "person1_sun": person1_sun, "person1_moon": person1_moon,
        "person2_name": person2_name, "person2_sun": person2_sun, "person2_moon": person2_moon,
    })

    if not (0 <= int(score) <= 100):
        raise ValueError("score must be between 0 and 100")

    if not EMERGENT_LLM_KEY:
        raise RuntimeError("EMERGENT_LLM_KEY is not configured")

    # Has this exact pairing already been sent? (Allow regenerate by
    # using a different recipient or modifying the score.)
    cache_key = f"{p1n}-{p1s}-{p1m}|{p2n}-{p2s}-{p2m}"

    from emergentintegrations.llm.chat import LlmChat, UserMessage  # type: ignore

    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"compat-{cache_key}",
        system_message=_SYSTEM_PROMPT,
    ).with_model(MODEL_PROVIDER, MODEL_NAME)

    prompt = (
        f"Write a Premium compatibility reading for:\n"
        f"- {p1n}: Sun in {p1s.capitalize()}, Moon in {p1m.capitalize()}\n"
        f"- {p2n}: Sun in {p2s.capitalize()}, Moon in {p2m.capitalize()}\n"
        f"Overall compatibility score: {score}/100.\n"
        f"Return JSON only."
    )

    try:
        raw = await chat.send_message(UserMessage(text=prompt))
    except Exception as exc:  # noqa: BLE001
        logger.exception("Compatibility LLM call failed: %s", exc)
        raise RuntimeError("Compatibility generation failed") from exc

    parsed = _parse_json(raw)
    required = ("headline_paragraph", "sun_sun_paragraph", "moon_moon_paragraph",
                "venus_mars_paragraph", "composite_paragraph", "work_paragraph")
    if not parsed or not all(k in parsed and isinstance(parsed[k], str) for k in required):
        logger.warning("Compatibility LLM returned malformed payload: %s", raw[:300])
        raise RuntimeError("Compatibility generation returned an unexpected response")

    label = (
        "Cosmic match"      if score >= 80 else
        "Strong chemistry"  if score >= 65 else
        "Worth exploring"   if score >= 50 else
        "Spark with friction" if score >= 35 else "Growth pairing"
    )

    tmpl_vars = {
        "person1_name": p1n,
        "person2_name": p2n,
        "person1_sun":  p1s.capitalize(),
        "person2_sun":  p2s.capitalize(),
        "score":        str(score),
        "label":        label,
        **{k: parsed[k].strip() for k in required},
    }

    try:
        await email_sender(
            "premium_compatibility",
            to=recipient_email,
            unsubscribe_url="https://liveastrology.app/upgrade/manage",
            **tmpl_vars,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Compatibility email send failed: %s", exc)
        raise RuntimeError("Email send failed") from exc

    doc = {
        "recipient_email": recipient_email,
        "cache_key": cache_key,
        "person1": {"name": p1n, "sun": p1s, "moon": p1m},
        "person2": {"name": p2n, "sun": p2s, "moon": p2m},
        "score": int(score),
        "label": label,
        "paragraphs": {k: parsed[k].strip() for k in required},
        "sent_at": _now(),
    }
    await db.compatibility_reports.insert_one(doc)

    return {
        "status": "sent",
        "recipient": recipient_email,
        "label": label,
        "score": int(score),
        "word_counts": {k: len(parsed[k].split()) for k in required},
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

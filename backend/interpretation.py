"""Plain-English AI interpretation of a user's Sun, Moon, and Rising signs.

Uses Claude Sonnet 4.5 via the Emergent universal LLM key (no per-user
Anthropic API key needed). Responses are cached in MongoDB by
(sun, moon, rising) tuple so repeat requests are free and instant.

Returns three short paragraphs — one per placement — written for an
astrology-curious newcomer. No fortune-telling, no jargon, just plain
English that explains what each sign means in that position, how it
shows up in daily life, and one practical insight.
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("liveastrology.interpretation")

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
MODEL_PROVIDER = "anthropic"
MODEL_NAME = "claude-sonnet-4-5-20250929"

_SYSTEM_PROMPT = (
    "You are a warm, practical astrologer writing for someone who just "
    "calculated their birth chart for the first time. Your job is to "
    "explain their Sun, Moon, and Rising signs in plain English — no "
    "jargon, no fortune-telling, no horoscope clichés. For each "
    "placement: (1) what this sign means in that position, "
    "(2) how it shows up in their everyday life, "
    "(3) one practical insight or strength they can lean into."
    "\n\n"
    "Return STRICT JSON in this exact shape:\n"
    '{ "sun": "<paragraph 1>", "moon": "<paragraph 2>", "rising": "<paragraph 3>" }'
    "\n\n"
    "Each paragraph: 80–120 words, second person ('you'), friendly but "
    "not saccharine. No markdown, no lists, no emojis. Return JSON only."
)

_VALID_SIGNS = {
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
}


def _normalize(sign: str) -> str:
    return (sign or "").strip().lower()


def _is_valid(sun: str, moon: str, rising: str) -> bool:
    return all(s in _VALID_SIGNS for s in (sun, moon, rising))


async def get_interpretation(db: Any, sun: str, moon: str, rising: str) -> dict[str, str]:
    """Generate or load a cached Sun/Moon/Rising interpretation.

    Raises ValueError on invalid input. Raises RuntimeError if the LLM
    call fails and no cached fallback exists.
    """
    sun_n, moon_n, rising_n = _normalize(sun), _normalize(moon), _normalize(rising)
    if not _is_valid(sun_n, moon_n, rising_n):
        raise ValueError("sun, moon, and rising must be valid zodiac signs")

    cache_key = f"{sun_n}|{moon_n}|{rising_n}"

    cached = await db.interpretation_cache.find_one(
        {"key": cache_key}, {"_id": 0, "sun": 1, "moon": 1, "rising": 1}
    )
    if cached:
        return {"sun": cached["sun"], "moon": cached["moon"], "rising": cached["rising"]}

    if not EMERGENT_LLM_KEY:
        raise RuntimeError("EMERGENT_LLM_KEY is not configured")

    # Lazy import — keeps cold start fast and pytest happy when the
    # optional library is absent in CI.
    from emergentintegrations.llm.chat import LlmChat, UserMessage  # type: ignore

    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"interp-{cache_key}",
        system_message=_SYSTEM_PROMPT,
    ).with_model(MODEL_PROVIDER, MODEL_NAME)

    user_prompt = (
        f"My placements are:\n"
        f"- Sun in {sun_n.capitalize()}\n"
        f"- Moon in {moon_n.capitalize()}\n"
        f"- Rising in {rising_n.capitalize()}\n\n"
        f"Write the three-paragraph plain-English interpretation as JSON."
    )

    try:
        raw = await chat.send_message(UserMessage(text=user_prompt))
    except Exception as exc:  # noqa: BLE001
        logger.exception("LLM interpretation call failed: %s", exc)
        raise RuntimeError("Interpretation service is temporarily unavailable") from exc

    parsed = _parse_json(raw)
    if not parsed or not all(k in parsed and isinstance(parsed[k], str) for k in ("sun", "moon", "rising")):
        logger.warning("LLM returned malformed payload: %s", raw[:300])
        raise RuntimeError("Interpretation service returned an unexpected response")

    from datetime import datetime, timezone
    await db.interpretation_cache.update_one(
        {"key": cache_key},
        {
            "$set": {
                "key": cache_key,
                "sun_sign": sun_n,
                "moon_sign": moon_n,
                "rising_sign": rising_n,
                "sun": parsed["sun"].strip(),
                "moon": parsed["moon"].strip(),
                "rising": parsed["rising"].strip(),
                "model": f"{MODEL_PROVIDER}/{MODEL_NAME}",
                "cached_at": datetime.now(timezone.utc),
            }
        },
        upsert=True,
    )

    return {
        "sun": parsed["sun"].strip(),
        "moon": parsed["moon"].strip(),
        "rising": parsed["rising"].strip(),
    }


def _parse_json(raw: str) -> dict[str, Any] | None:
    """Extract a JSON object from the model's response, tolerating
    surrounding prose or code fences."""
    import json
    import re

    if not raw:
        return None

    candidates: list[str] = []
    # Code fence
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.S)
    if fence:
        candidates.append(fence.group(1))
    # Outermost brace
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

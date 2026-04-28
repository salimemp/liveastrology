"""Generate weekly-horoscope template variables.

This module produces a deterministic, week-stable set of vars that plug
into ``emails/html/06-weekly-horoscope.html``. The content is curated
(not real transits — yet), which means the same week always produces the
same output. When we later integrate a Python ephemeris (e.g. ``skyfield``
or the Python port of ``astronomy-engine``), swap ``_compute_transits``
for the real thing and the rest of the module keeps working.
"""
from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta, timezone
from typing import Any

# Zodiac Sun-sign ranges (approximate — matches the frontend's lookup).
_SIGNS: list[tuple[str, str, str]] = [
    # (name, glyph, short motto)
    ("Aries",       "♈", "initiate"),
    ("Taurus",      "♉", "savour"),
    ("Gemini",      "♊", "converse"),
    ("Cancer",      "♋", "nurture"),
    ("Leo",         "♌", "shine"),
    ("Virgo",       "♍", "refine"),
    ("Libra",       "♎", "balance"),
    ("Scorpio",     "♏", "transform"),
    ("Sagittarius", "♐", "explore"),
    ("Capricorn",   "♑", "build"),
    ("Aquarius",    "♒", "innovate"),
    ("Pisces",      "♓", "dream"),
]

# Sun-sign cutoff dates (month, day). First day of each sign.
_CUTOFFS = [
    (3, 21, "Aries"), (4, 20, "Taurus"), (5, 21, "Gemini"),
    (6, 21, "Cancer"), (7, 23, "Leo"), (8, 23, "Virgo"),
    (9, 23, "Libra"), (10, 23, "Scorpio"), (11, 22, "Sagittarius"),
    (12, 22, "Capricorn"), (1, 20, "Aquarius"), (2, 19, "Pisces"),
]

_WEEKLY_RITUALS = [
    "Light a single candle on Sunday night. Write one intention for the week on a slip of paper, fold it toward you three times, and tuck it under the candle for the week.",
    "Leave a glass of water on the windowsill overnight under the moon. Drink it at sunrise — a small reminder that you, too, are mostly water and mostly lunar.",
    "Take a walk without your phone for 20 minutes. Notice the first three things that catch your eye and ask each one what it has to tell you.",
    "Journal this prompt for seven minutes, no stopping: 'If nothing was in my way, the thing I'd do next is…' Then do the smallest version of it today.",
    "Put on music that matches the mood you *want*, not the one you have. Dance for one song. This is a spell, not a workout.",
    "Make a list of five people (living, dead, or fictional) whose courage you admire. Carry it in your wallet this week as a reminder.",
]

_TRANSIT_TITLES = [
    "A big-picture breakthrough",
    "A tender, emotional reset",
    "A week for finishing, not starting",
    "Words that travel further than expected",
    "Your relationships in soft focus",
    "A quiet clarity about what you value",
    "A moment of permission to rest",
]


def _week_bucket(d: date) -> int:
    """Stable 0-6 bucket so the same week always yields the same canned content."""
    iso_year, iso_week, _ = d.isocalendar()
    return (iso_year * 100 + iso_week) % 7


def _sun_sign(d: date) -> str:
    m, day = d.month, d.day
    for cm, cd, sign in _CUTOFFS:
        # Handle wrap-around (Capricorn: Dec 22 → Jan 19)
        if cm == 12 and m == 12 and day >= cd:
            return "Capricorn"
        if cm == 1 and ((m == 12 and day >= 22) or (m == 1 and day < cd)):
            return "Capricorn"
    # Fall-through: scan normally
    for cm, cd, sign in _CUTOFFS:
        if m == cm and day >= cd:
            return sign
    # If not matched above, return the previous sign
    order = ["Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini",
             "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius"]
    return order[(m - 1) % 12]


def _sign_info(name: str) -> tuple[str, str, str]:
    for n, glyph, motto in _SIGNS:
        if n == name:
            return n, glyph, motto
    return _SIGNS[0]


def _rotating_signs(seed: str, count: int) -> list[str]:
    """Deterministic pick of ``count`` signs from a seed string."""
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    names = [s[0] for s in _SIGNS]
    picked: list[str] = []
    while len(picked) < count:
        s = names[h % 12]
        h //= 7
        if s not in picked:
            picked.append(s)
    return picked


def build_weekly_vars(for_date: date | None = None, *, first_name: str = "there", unsubscribe_url: str = "#") -> dict[str, Any]:
    """Return the full set of ``{{placeholders}}`` needed for template 06."""
    d = for_date or datetime.now(timezone.utc).date()
    # Normalise to the Sunday that starts this week
    sunday = d - timedelta(days=(d.weekday() + 1) % 7)
    saturday = sunday + timedelta(days=6)

    sun = _sun_sign(d)
    bucket = _week_bucket(d)
    transit_title = _TRANSIT_TITLES[bucket % len(_TRANSIT_TITLES)]

    # Pick three "top signs" deterministically.
    top_signs = _rotating_signs(seed=f"top-{d.isocalendar()}", count=3)
    top_reasons = [
        "Doors open where last week saw walls. Say yes to the first invite you get.",
        "A feeling you've been sitting with finally finds its words. Write them down.",
        "Money, focus, or rest — one of the three gets dramatically easier this week.",
    ]

    moon_signs = " → ".join(_rotating_signs(seed=f"moon-{d.isocalendar()}", count=3))
    mercury_sign = _rotating_signs(seed=f"mercury-{d.month}", count=1)[0]
    venus_sign   = _rotating_signs(seed=f"venus-{d.month}", count=1)[0]
    mars_sign    = _rotating_signs(seed=f"mars-{d.month}", count=1)[0]

    def glyph(name: str) -> str:
        return _sign_info(name)[1]

    return {
        "first_name": first_name,
        "preheader": f"Your {sun} season brief — {transit_title.lower()}",
        "hero_emoji": "✨",
        "week_headline": transit_title,
        "week_of": f"{sunday.strftime('%b %-d')} – {saturday.strftime('%b %-d, %Y')}",

        "transit_title": transit_title,
        "transit_date_range": f"{sunday.strftime('%a %b %-d')} – {saturday.strftime('%a %b %-d')}",
        "transit_body": (
            f"The Sun moves through {sun} this week, asking you to {_sign_info(sun)[2]}. "
            "Pair that with a grounded daily rhythm and you'll feel the difference by Friday. "
            "The work this week is small, repeatable, and suspiciously boring. Do it anyway."
        ),

        "sun_sign":    sun,
        "sun_note":    f"lean into your capacity to {_sign_info(sun)[2]}",
        "moon_signs":  moon_signs,
        "moon_note":   "quick mood shifts — ride them, don't fix them",
        "mercury_sign": mercury_sign,
        "mercury_note": f"conversations colour-shifted by {mercury_sign.lower()} energy — more direct than usual",
        "venus_sign":  venus_sign,
        "venus_note":  f"what you find beautiful this week leans {venus_sign.lower()}",
        "mars_sign":   mars_sign,
        "mars_note":   f"drive shows up in {mars_sign.lower()} flavour — use it in short sprints",

        "top1_sign": top_signs[0], "top1_glyph": glyph(top_signs[0]), "top1_reason": top_reasons[0],
        "top2_sign": top_signs[1], "top2_glyph": glyph(top_signs[1]), "top2_reason": top_reasons[1],
        "top3_sign": top_signs[2], "top3_glyph": glyph(top_signs[2]), "top3_reason": top_reasons[2],

        "ritual_body": _WEEKLY_RITUALS[bucket % len(_WEEKLY_RITUALS)],
        "blog_url": "https://liveastrology.app/blog",

        "unsubscribe_url": unsubscribe_url,
        "email": "",
    }

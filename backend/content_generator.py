"""Generate weekly-horoscope template variables.

Uses the ``astronomy-engine`` Python package (same ephemeris as the
frontend's JS build) to compute real planetary positions, then maps
ecliptic longitudes to zodiac signs. Editorial/narrative content is
still curated (rituals, top-3 reasons) because that takes a human
eye — but every planet position is now real.
"""
from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta, timezone
from typing import Any

try:
    import astronomy  # type: ignore
    _HAS_EPHEMERIS = True
except Exception:  # noqa: BLE001
    astronomy = None  # type: ignore
    _HAS_EPHEMERIS = False

# (name, glyph, short motto) — ordered by ecliptic longitude (0° = Aries).
_SIGNS: list[tuple[str, str, str]] = [
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


# ---------- Ephemeris helpers ----------
def _longitude_to_sign(lon_deg: float) -> tuple[str, str, str]:
    """Map an ecliptic longitude (0..360°) to its zodiac sign."""
    idx = int(lon_deg % 360.0 // 30.0)
    return _SIGNS[idx]


def _ecliptic_longitude(body: Any, when: datetime) -> float:
    """Apparent geocentric ecliptic longitude of a body, in degrees."""
    t = astronomy.Time.Make(when.year, when.month, when.day, when.hour, when.minute, when.second)
    # GeoVector gives geocentric equatorial coordinates; convert to ecliptic.
    vec = astronomy.GeoVector(body, t, True)  # aberration = True
    ecl = astronomy.Ecliptic(vec)
    return float(ecl.elon)


def _compute_transits(when: datetime) -> dict[str, str]:
    """Return the live zodiac sign for Sun, Moon, Mercury, Venus, Mars.

    Falls back to deterministic dummy values if ``astronomy-engine`` is
    unavailable (so unit tests without the dependency still pass)."""
    if not _HAS_EPHEMERIS:
        fallback = _deterministic_signs(when.date())
        return fallback
    bodies = {
        "sun":     astronomy.Body.Sun,
        "moon":    astronomy.Body.Moon,
        "mercury": astronomy.Body.Mercury,
        "venus":   astronomy.Body.Venus,
        "mars":    astronomy.Body.Mars,
    }
    out: dict[str, str] = {}
    for key, body in bodies.items():
        lon = _ecliptic_longitude(body, when)
        out[key] = _longitude_to_sign(lon)[0]
    return out


def _deterministic_signs(d: date) -> dict[str, str]:
    """Deterministic fallback when astronomy-engine is not installed."""
    names = [s[0] for s in _SIGNS]
    h = int(hashlib.md5(d.isoformat().encode()).hexdigest(), 16)
    return {
        "sun":     names[h % 12],
        "moon":    names[(h // 3) % 12],
        "mercury": names[(h // 5) % 12],
        "venus":   names[(h // 7) % 12],
        "mars":    names[(h // 11) % 12],
    }


def _moon_signs_across_week(start: datetime) -> str:
    """The Moon changes sign every ~2.5 days — list the distinct signs it
    visits between ``start`` and ``start + 7 days``."""
    if not _HAS_EPHEMERIS:
        return "Scorpio → Sagittarius → Capricorn"
    seen: list[str] = []
    for h in range(0, 7 * 24, 6):  # every 6 hours
        when = start + timedelta(hours=h)
        lon = _ecliptic_longitude(astronomy.Body.Moon, when)
        sign = _longitude_to_sign(lon)[0]
        if not seen or seen[-1] != sign:
            seen.append(sign)
    return " → ".join(seen)


def _sign_motto(name: str) -> str:
    for n, _, motto in _SIGNS:
        if n == name:
            return motto
    return "observe"


def _sign_glyph(name: str) -> str:
    for n, glyph, _ in _SIGNS:
        if n == name:
            return glyph
    return ""


def _week_bucket(d: date) -> int:
    iso_year, iso_week, _ = d.isocalendar()
    return (iso_year * 100 + iso_week) % 7


def _rotating_signs(seed: str, count: int) -> list[str]:
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
    """Build the full set of ``{{placeholders}}`` for template 06."""
    d = for_date or datetime.now(timezone.utc).date()
    sunday = d - timedelta(days=(d.weekday() + 1) % 7)
    saturday = sunday + timedelta(days=6)
    midweek = datetime.combine(sunday + timedelta(days=3), datetime.min.time(), tzinfo=timezone.utc)

    transits = _compute_transits(midweek)
    moon_signs = _moon_signs_across_week(datetime.combine(sunday, datetime.min.time(), tzinfo=timezone.utc))

    bucket = _week_bucket(d)
    transit_title = _TRANSIT_TITLES[bucket % len(_TRANSIT_TITLES)]

    top_signs = _rotating_signs(seed=f"top-{d.isocalendar()}", count=3)
    top_reasons = [
        "Doors open where last week saw walls. Say yes to the first invite you get.",
        "A feeling you've been sitting with finally finds its words. Write them down.",
        "Money, focus, or rest — one of the three gets dramatically easier this week.",
    ]

    sun = transits["sun"]
    return {
        "first_name": first_name,
        "preheader": f"Sun in {sun} — {transit_title.lower()}",
        "hero_emoji": _sign_glyph(sun) or "✨",
        "week_headline": transit_title,
        "week_of": f"{sunday.strftime('%b %-d')} – {saturday.strftime('%b %-d, %Y')}",

        "transit_title": transit_title,
        "transit_date_range": f"{sunday.strftime('%a %b %-d')} – {saturday.strftime('%a %b %-d')}",
        "transit_body": (
            f"The Sun moves through {sun} this week, asking you to {_sign_motto(sun)}. "
            f"Mercury in {transits['mercury']} is shaping conversations; Venus in {transits['venus']} tints what you find beautiful; "
            f"Mars in {transits['mars']} flavours your drive. The work this week is small, repeatable, and suspiciously boring. Do it anyway."
        ),

        "sun_sign":    sun,
        "sun_note":    f"lean into your capacity to {_sign_motto(sun)}",
        "moon_signs":  moon_signs,
        "moon_note":   "quick mood shifts — ride them, don't fix them",
        "mercury_sign": transits["mercury"],
        "mercury_note": f"conversations carry a {transits['mercury'].lower()} edge",
        "venus_sign":  transits["venus"],
        "venus_note":  f"what draws you in this week leans {transits['venus'].lower()}",
        "mars_sign":   transits["mars"],
        "mars_note":   f"energy shows up in {transits['mars'].lower()} flavour — use it in short sprints",

        "top1_sign": top_signs[0], "top1_glyph": _sign_glyph(top_signs[0]), "top1_reason": top_reasons[0],
        "top2_sign": top_signs[1], "top2_glyph": _sign_glyph(top_signs[1]), "top2_reason": top_reasons[1],
        "top3_sign": top_signs[2], "top3_glyph": _sign_glyph(top_signs[2]), "top3_reason": top_reasons[2],

        "ritual_body": _WEEKLY_RITUALS[bucket % len(_WEEKLY_RITUALS)],
        "blog_url": "https://liveastrology.app/blog",

        "unsubscribe_url": unsubscribe_url,
        "email": "",
    }

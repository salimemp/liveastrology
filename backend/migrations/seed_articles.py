"""One-time seed migration that loads the six built-in evergreen articles
into the MongoDB ``articles`` collection if it is empty. Idempotent — it
will not overwrite or duplicate articles that have already been added.

Run inside the backend container with:

    python -m migrations.seed_articles

The article copy is the canonical version we ship with the app; once an
admin starts editing articles via /admin, this script should not be run
again (it is a no-op if the collection already has documents anyway, but
treat it as a one-shot bootstrap).
"""
from __future__ import annotations

import asyncio
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient


def _slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:90]


SEED_ARTICLES = [
    {
        "title": "Understanding Your Sun Sign: The Core of Your Astrological Identity",
        "category": "Astrology Basics",
        "author": "Celestial Insights",
        "tags": ["sun sign", "zodiac", "astrology basics", "self discovery"],
        "read_time": "9 min read",
        "published_at": datetime(2024, 12, 15, tzinfo=timezone.utc),
    },
    {
        "title": "Moon Sign vs Rising Sign: What's the Difference?",
        "category": "Astrology Basics",
        "author": "Stellar Guide",
        "tags": ["moon sign", "rising sign", "ascendant", "birth chart"],
        "read_time": "11 min read",
        "published_at": datetime(2024, 12, 10, tzinfo=timezone.utc),
    },
    {
        "title": "How Venus and Mars Influence Your Love Life",
        "category": "Love & Relationships",
        "author": "Cosmic Love",
        "tags": ["venus", "mars", "romance", "compatibility", "love"],
        "read_time": "12 min read",
        "published_at": datetime(2024, 12, 5, tzinfo=timezone.utc),
    },
    {
        "title": "Mercury Retrograde: Cycles, Myths, and How to Actually Use Them",
        "category": "Astrology Basics",
        "author": "Celestial Insights",
        "tags": ["mercury", "retrograde", "communication", "astrology cycles"],
        "read_time": "11 min read",
        "published_at": datetime(2024, 11, 28, tzinfo=timezone.utc),
    },
    {
        "title": "The 12 Houses of Astrology Explained",
        "category": "Astrology Basics",
        "author": "Stellar Guide",
        "tags": ["houses", "birth chart", "astrology basics", "natal chart"],
        "read_time": "13 min read",
        "published_at": datetime(2024, 11, 22, tzinfo=timezone.utc),
    },
    {
        "title": "Saturn Returns: Why Your Late 20s Feel Like a Tear-Down",
        "category": "Astrology Basics",
        "author": "Celestial Insights",
        "tags": ["saturn return", "transits", "life cycles", "astrology basics"],
        "read_time": "12 min read",
        "published_at": datetime(2024, 11, 18, tzinfo=timezone.utc),
    },
]


async def main() -> None:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    existing = await db.articles.count_documents({})
    if existing > 0:
        print(f"articles collection already has {existing} document(s) — skipping seed.")
        return

    inserted = 0
    for stub in SEED_ARTICLES:
        slug = _slugify(stub["title"])
        # Real long-form copy lives in the frontend bundle today; we seed
        # the metadata + a one-paragraph excerpt that links back to the
        # frontend route so the API is functional even before someone
        # imports the full text via the admin editor.
        doc = {
            "slug":         slug,
            "title":        stub["title"],
            "excerpt":      f"Editorial article in the {stub['category']} series. Open the article on the site to read the full text.",
            "content":      f"# {stub['title']}\n\nThis article is currently maintained in the frontend codebase. Edit it via /admin → Articles to publish a database-backed version.",
            "author":       stub["author"],
            "category":     stub["category"],
            "tags":         stub["tags"],
            "read_time":    stub["read_time"],
            "word_count":   0,
            "status":       "published",
            "created_at":   stub["published_at"],
            "updated_at":   stub["published_at"],
            "published_at": stub["published_at"],
        }
        await db.articles.insert_one(doc)
        inserted += 1

    print(f"Seeded {inserted} articles.")


if __name__ == "__main__":
    asyncio.run(main())

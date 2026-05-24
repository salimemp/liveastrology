"""RSS 2.0 + Atom 1.0 feed builders for the Articles CMS.

Both feeds expose the most recent published articles so aggregators
(Feedly, Google News, Perplexity / ChatGPT search crawlers) can pick
up new content without scraping HTML.

Spec compliance:
- RSS 2.0: https://www.rssboard.org/rss-specification
- Atom 1.0: https://datatracker.ietf.org/doc/html/rfc4287

Notes
-----
- Article ``content`` is intentionally NOT included in full — only the
  ``excerpt`` is exposed in <description> / <summary>. Aggregators
  follow the canonical link for the full read, which keeps engagement
  on liveastrology.app.
- Times are emitted as RFC 822 (RSS) and RFC 3339 (Atom), both UTC.
- Guids are stable: the article slug, prefixed with the site origin.
"""
from __future__ import annotations

from datetime import datetime, timezone
from email.utils import format_datetime
from typing import Any
from xml.sax.saxutils import escape

SITE_URL = "https://liveastrology.app"
SITE_TITLE = "Live Astrology"
SITE_DESCRIPTION = (
    "Plain-English astrology — free birth charts, AI interpretations, "
    "weekly horoscopes, and long-form guides from the Live Astrology editorial team."
)
SITE_LANGUAGE = "en-us"
EDITORIAL_EMAIL = "editorial@liveastrology.app"


def _coerce_dt(value: Any) -> datetime | None:
    """Return a timezone-aware datetime, or None if the value isn't one."""
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return None


def _article_url(slug: str) -> str:
    return f"{SITE_URL}/articles/{slug}"


def _rfc822(dt: datetime) -> str:
    return format_datetime(dt, usegmt=True)


def _rfc3339(dt: datetime) -> str:
    # Atom requires "YYYY-MM-DDTHH:MM:SSZ" (or with offset).
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_rss(articles: list[dict[str, Any]], *, now: datetime | None = None) -> str:
    """Render RSS 2.0 XML for the given list of published articles."""
    now = now or datetime.now(timezone.utc)
    last_build = _rfc822(now)

    items_xml: list[str] = []
    for art in articles:
        pub = _coerce_dt(art.get("published_at")) or _coerce_dt(art.get("created_at")) or now
        slug = str(art.get("slug", "")).strip()
        if not slug:
            continue
        url = _article_url(slug)
        category = str(art.get("category", "Astrology"))
        author = str(art.get("author", "Live Astrology Editorial"))
        items_xml.append(
            "    <item>\n"
            f"      <title>{escape(str(art.get('title', '')))}</title>\n"
            f"      <link>{escape(url)}</link>\n"
            f"      <guid isPermaLink=\"true\">{escape(url)}</guid>\n"
            f"      <pubDate>{_rfc822(pub)}</pubDate>\n"
            f"      <category>{escape(category)}</category>\n"
            f"      <author>{escape(EDITORIAL_EMAIL)} ({escape(author)})</author>\n"
            f"      <description>{escape(str(art.get('excerpt', '')))}</description>\n"
            "    </item>"
        )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "  <channel>\n"
        f"    <title>{escape(SITE_TITLE)} — Articles</title>\n"
        f"    <link>{escape(SITE_URL)}</link>\n"
        f"    <description>{escape(SITE_DESCRIPTION)}</description>\n"
        f"    <language>{SITE_LANGUAGE}</language>\n"
        f"    <lastBuildDate>{last_build}</lastBuildDate>\n"
        f'    <atom:link href="{SITE_URL}/api/feed.xml" rel="self" type="application/rss+xml" />\n'
        + ("\n".join(items_xml) + "\n" if items_xml else "")
        + "  </channel>\n"
        "</rss>\n"
    )


def build_atom(articles: list[dict[str, Any]], *, now: datetime | None = None) -> str:
    """Render Atom 1.0 XML for the given list of published articles."""
    now = now or datetime.now(timezone.utc)
    updated_dts = [
        d for d in (_coerce_dt(a.get("updated_at")) for a in articles) if d is not None
    ]
    feed_updated = max(updated_dts) if updated_dts else now

    entries_xml: list[str] = []
    for art in articles:
        slug = str(art.get("slug", "")).strip()
        if not slug:
            continue
        url = _article_url(slug)
        pub = _coerce_dt(art.get("published_at")) or _coerce_dt(art.get("created_at")) or now
        upd = _coerce_dt(art.get("updated_at")) or pub
        author = str(art.get("author", "Live Astrology Editorial"))
        entries_xml.append(
            "  <entry>\n"
            f"    <title>{escape(str(art.get('title', '')))}</title>\n"
            f'    <link rel="alternate" type="text/html" href="{escape(url)}" />\n'
            f"    <id>{escape(url)}</id>\n"
            f"    <published>{_rfc3339(pub)}</published>\n"
            f"    <updated>{_rfc3339(upd)}</updated>\n"
            "    <author>\n"
            f"      <name>{escape(author)}</name>\n"
            f"      <email>{escape(EDITORIAL_EMAIL)}</email>\n"
            "    </author>\n"
            f'    <category term="{escape(str(art.get("category", "Astrology")))}" />\n'
            f"    <summary>{escape(str(art.get('excerpt', '')))}</summary>\n"
            "  </entry>"
        )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<feed xmlns="http://www.w3.org/2005/Atom">\n'
        f"  <title>{escape(SITE_TITLE)} — Articles</title>\n"
        f"  <subtitle>{escape(SITE_DESCRIPTION)}</subtitle>\n"
        f'  <link rel="alternate" type="text/html" href="{SITE_URL}/" />\n'
        f'  <link rel="self" type="application/atom+xml" href="{SITE_URL}/api/atom.xml" />\n'
        f"  <id>{SITE_URL}/</id>\n"
        f"  <updated>{_rfc3339(feed_updated)}</updated>\n"
        "  <author>\n"
        f"    <name>{escape(SITE_TITLE)} Editorial</name>\n"
        f"    <email>{escape(EDITORIAL_EMAIL)}</email>\n"
        "  </author>\n"
        + ("\n".join(entries_xml) + "\n" if entries_xml else "")
        + "</feed>\n"
    )

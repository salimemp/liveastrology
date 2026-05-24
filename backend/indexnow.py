"""IndexNow — instant URL indexing pings to Bing, Yandex, Seznam, Naver.

IndexNow is a free open protocol (https://www.indexnow.org) that lets
publishers tell participating search engines about new or updated URLs
the moment they go live, bypassing slow crawl schedules. Bing, Yandex,
Seznam, Naver, and Yep are all members; Google does not participate
but doesn't penalise sites that use it.

How it works
------------
1. The site hosts a plain-text file containing a 32-char hex key at a
   publicly reachable URL — e.g. ``https://liveastrology.app/api/indexnow-key.txt``.
2. To submit URLs, the site POSTs JSON to ``https://api.indexnow.org/IndexNow``
   with the key + key location + list of URLs. Search engines hit the
   key URL to verify the publisher owns the site, then crawl the URLs.

Configuration (env)
-------------------
INDEXNOW_KEY              hex key (32 chars). Required to enable pings.
INDEXNOW_KEY_LOCATION     optional override URL of the key file
                          (default ``{SITE_URL}/api/indexnow-key.txt``).
INDEXNOW_HOST             host header sent in the payload
                          (default ``liveastrology.app``).
INDEXNOW_DISABLED         set to "1" to short-circuit all pings
                          (used by the test suite).

All pings are fire-and-forget background tasks — IndexNow latency or
failure must never affect the admin response. Failures are logged but
never raise.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Iterable

import httpx

logger = logging.getLogger("liveastrology.indexnow")

SITE_URL = "https://liveastrology.app"
SITEMAP_URL = f"{SITE_URL}/sitemap.xml"
ENDPOINT = "https://api.indexnow.org/IndexNow"
TIMEOUT_SECONDS = 8.0


def _key() -> str:
    return os.environ.get("INDEXNOW_KEY", "").strip()


def _key_location() -> str:
    return (
        os.environ.get("INDEXNOW_KEY_LOCATION", "").strip()
        or f"{SITE_URL}/api/indexnow-key.txt"
    )


def _host() -> str:
    return os.environ.get("INDEXNOW_HOST", "liveastrology.app").strip()


def _disabled() -> bool:
    return os.environ.get("INDEXNOW_DISABLED", "").strip() == "1"


def url_for_article(slug: str) -> str:
    return f"{SITE_URL}/articles/{slug}"


async def submit(urls: Iterable[str]) -> dict[str, object]:
    """Submit one or many URLs to IndexNow.

    Returns ``{"status": "ok"|"skipped"|"failed", ...}``. Never raises —
    network failures are logged and reported via the return value so the
    caller can decide whether to surface them (admin endpoint) or ignore
    them (background task on publish).
    """
    url_list = [str(u).strip() for u in urls if str(u).strip()]
    if not url_list:
        return {"status": "skipped", "reason": "no urls provided"}

    if _disabled():
        return {"status": "skipped", "reason": "INDEXNOW_DISABLED=1", "urls": url_list}

    key = _key()
    if not key:
        logger.info("IndexNow ping skipped — INDEXNOW_KEY not set")
        return {"status": "skipped", "reason": "INDEXNOW_KEY not configured", "urls": url_list}

    payload = {
        "host":         _host(),
        "key":          key,
        "keyLocation":  _key_location(),
        "urlList":      url_list,
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as http:
            r = await http.post(
                ENDPOINT,
                json=payload,
                headers={"Content-Type": "application/json; charset=utf-8"},
            )
    except (httpx.HTTPError, asyncio.TimeoutError) as exc:
        logger.warning("IndexNow ping failed: %s", exc)
        return {"status": "failed", "reason": str(exc), "urls": url_list}

    # 200 = accepted, 202 = accepted and queued, both = success per spec.
    if r.status_code in (200, 202):
        logger.info("IndexNow accepted %d url(s) — http=%d", len(url_list), r.status_code)
        return {"status": "ok", "http_status": r.status_code, "submitted": len(url_list)}

    # 400 = bad request, 403 = key file not found / invalid, 422 = url
    # not in keyLocation host, 429 = too many requests. All non-2xx are
    # surfaced so the admin can debug; never raise.
    body_preview = r.text[:200]
    logger.warning(
        "IndexNow rejected %d url(s) — http=%d body=%r", len(url_list), r.status_code, body_preview,
    )
    return {
        "status": "failed",
        "http_status": r.status_code,
        "body": body_preview,
        "urls": url_list,
    }


async def submit_in_background(urls: Iterable[str]) -> None:
    """Fire-and-forget wrapper used by the article publish path.

    Schedules ``submit`` as a detached task on the current event loop so
    the caller (admin endpoint) returns immediately.
    """
    loop = asyncio.get_event_loop()
    loop.create_task(submit(list(urls)))

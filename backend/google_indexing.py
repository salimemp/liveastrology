"""Google Indexing API client.

Tells Google directly to recrawl a URL the moment we publish an article.
Pairs with IndexNow (Bing/Yandex) — together, Bing + Google instant-indexing
cover the engines that matter for organic discovery.

Authentication
--------------
Service-account JSON key file at ``GOOGLE_INDEXING_CREDENTIALS_FILE``
(default ``/app/backend/secrets/google-indexing-credentials.json``).
The service account must be added as a **delegated owner** of the
``liveastrology.app`` property in Google Search Console — otherwise every
call returns ``403 Permission denied. Failed to verify the URL ownership.``

Quotas
------
- 200 ``URL_UPDATED``/``URL_DELETED`` notifications per day (Google default).
- 600 requests per minute (Google default).

Failure handling
----------------
Every public coroutine is wrapped in a try/except — auth failures, network
errors, non-2xx responses are all logged and returned as structured dicts
so the publish endpoint never 500s because of a Google outage.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("liveastrology.google_indexing")

INDEXING_SCOPE = "https://www.googleapis.com/auth/indexing"
INDEXING_ENDPOINT = "https://indexing.googleapis.com/v3/urlNotifications:publish"
TIMEOUT_SECONDS = 10.0

_DEFAULT_CREDENTIALS_PATH = "/app/backend/secrets/google-indexing-credentials.json"


def _credentials_path() -> str:
    return os.environ.get("GOOGLE_INDEXING_CREDENTIALS_FILE", _DEFAULT_CREDENTIALS_PATH)


def _disabled() -> bool:
    return os.environ.get("GOOGLE_INDEXING_DISABLED", "").strip() == "1"


# ---------- Credentials cache ----------
# Single shared Credentials object reused across calls. google-auth caches
# the access token + expiry internally and only re-mints a JWT when the
# current token is invalid/expired (~1h lifetime).
_creds = None
_creds_path_loaded: str | None = None


def _load_credentials():
    """Load (or reload) the service-account credentials. Raises RuntimeError
    if the file is missing or the JSON is invalid."""
    global _creds, _creds_path_loaded
    path = _credentials_path()
    if _creds is not None and _creds_path_loaded == path:
        return _creds

    if not os.path.exists(path):
        raise RuntimeError(
            f"GOOGLE_INDEXING_CREDENTIALS_FILE not found at {path}. "
            "Place the service-account JSON at that path or set the env var."
        )

    # Local import — the google-auth library is optional at runtime so tests
    # without it (or with INDEXING disabled) can still import this module.
    from google.oauth2 import service_account  # type: ignore

    _creds = service_account.Credentials.from_service_account_file(
        path, scopes=[INDEXING_SCOPE],
    )
    _creds_path_loaded = path
    return _creds


def _refresh_sync() -> str | None:
    """Refresh (if needed) and return the current access token.

    Blocking — only call from a threadpool.
    """
    from google.auth.transport.requests import Request as GoogleRequest  # type: ignore

    creds = _load_credentials()
    if not creds.valid or creds.expired:
        creds.refresh(GoogleRequest())
    return creds.token


async def _get_access_token() -> str | None:
    """Async wrapper around the blocking token refresh."""
    try:
        return await asyncio.to_thread(_refresh_sync)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Google Indexing token refresh failed: %s", exc)
        return None


# ---------- Public API ----------
async def submit(url: str, *, action: str = "URL_UPDATED") -> dict[str, Any]:
    """Send a single ``URL_UPDATED`` or ``URL_DELETED`` notification.

    Never raises. Returns a structured ``{"status": "ok"|"skipped"|"failed", ...}``
    dict the caller can log / surface.
    """
    if action not in ("URL_UPDATED", "URL_DELETED"):
        return {"status": "failed", "reason": f"invalid action: {action}"}
    if not url or not url.startswith(("http://", "https://")):
        return {"status": "failed", "reason": "url must be absolute https://"}

    if _disabled():
        return {"status": "skipped", "reason": "GOOGLE_INDEXING_DISABLED=1", "url": url}

    token = await _get_access_token()
    if not token:
        return {
            "status": "skipped",
            "reason": "credentials unavailable — check GOOGLE_INDEXING_CREDENTIALS_FILE and service-account ownership in Search Console",
            "url": url,
        }

    payload = {"url": url, "type": action}
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as http:
            r = await http.post(INDEXING_ENDPOINT, json=payload, headers=headers)
    except (httpx.HTTPError, asyncio.TimeoutError) as exc:
        logger.warning("Google Indexing network error for %s: %s", url, exc)
        return {"status": "failed", "reason": str(exc), "url": url}

    body_preview = r.text[:400]
    if r.status_code == 200:
        logger.info("Google Indexing accepted URL_UPDATED for %s", url)
        return {"status": "ok", "http_status": 200, "url": url}

    # 403 = ownership missing in Search Console (most common operational error).
    # 429 = quota exceeded (200/day default). 400 = malformed url.
    logger.warning(
        "Google Indexing rejected %s — http=%d body=%r", url, r.status_code, body_preview,
    )
    return {
        "status": "failed",
        "http_status": r.status_code,
        "body": body_preview,
        "url": url,
    }


async def submit_in_background(url: str, *, action: str = "URL_UPDATED") -> None:
    """Fire-and-forget wrapper for the article publish hook."""
    loop = asyncio.get_event_loop()
    loop.create_task(submit(url, action=action))

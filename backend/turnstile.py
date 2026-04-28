"""Cloudflare Turnstile verification.

Validates a client-submitted token against Cloudflare's siteverify endpoint.
Skips verification when ``TURNSTILE_DISABLED=1`` (dev / CI) or when
``CF_TURNSTILE_SECRET`` is unset, so tests don't need network access.
"""
from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger("liveastrology.turnstile")

_SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


async def verify(token: str | None, *, remote_ip: str | None = None) -> bool:
    """Return True if the token is valid (or if verification is disabled)."""
    if os.environ.get("TURNSTILE_DISABLED", "0") == "1":
        return True
    secret = os.environ.get("CF_TURNSTILE_SECRET")
    if not secret:
        logger.warning("CF_TURNSTILE_SECRET missing — accepting request without verification")
        return True
    if not token:
        return False

    data: dict[str, str] = {"secret": secret, "response": token}
    if remote_ip:
        data["remoteip"] = remote_ip

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.post(_SITEVERIFY_URL, data=data)
            r.raise_for_status()
            body = r.json()
    except Exception as exc:  # noqa: BLE001 — never 500 the user on a CF hiccup
        logger.exception("turnstile verify error: %s", exc)
        return False

    if not body.get("success"):
        logger.info("turnstile rejected: %s", body.get("error-codes"))
        return False
    return True

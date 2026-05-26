"""Shared pytest fixtures for Live Astrology backend tests.

Tests run against an in-memory mongomock-motor MongoDB and a fake
``email_service.send_template`` so we never hit Resend during CI.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

# Ensure /app/backend is on sys.path so ``import server`` works from anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Guarantee minimum env before server module is imported.
os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "liveastrology_test")
os.environ.setdefault("RESEND_API_KEY", "test-key")
os.environ.setdefault("SENDER_EMAIL", "test@example.com")
os.environ.setdefault("NOTIFY_EMAIL", "notify-test@example.com")
os.environ.setdefault("APP_ORIGIN", "http://testserver")
os.environ.setdefault("ADMIN_SECRET", "test-admin-secret")
os.environ.setdefault("SEO_WORKFLOW_TOKEN", "test-seo-workflow-token")
os.environ.setdefault("TURNSTILE_DISABLED", "1")
os.environ.setdefault("RESEND_WEBHOOK_SECRET", "")
os.environ.setdefault("INDEXNOW_DISABLED", "1")
os.environ.setdefault("GOOGLE_INDEXING_DISABLED", "1")


@pytest.fixture
def sent_emails() -> list[dict[str, Any]]:
    """Collects every send_template call made during a test."""
    return []


@pytest_asyncio.fixture
async def client(monkeypatch, sent_emails):
    """FastAPI test client wired to an in-memory Mongo + a fake mailer."""
    import server  # noqa: WPS433 — deferred to pick up env first
    import email_service

    # Disable per-IP rate limiting for tests — it's covered by a dedicated test below.
    server.limiter.enabled = False
    # Reset any in-memory counters accumulated in prior imports/tests.
    try:
        server.limiter.reset()
    except Exception:
        pass

    # Swap the real Motor client for an in-memory one.
    mock_db = AsyncMongoMockClient()["liveastrology_test"]
    monkeypatch.setattr(server, "db", mock_db, raising=True)

    # Swap Resend dispatch for a no-op that records the call.
    async def fake_send(slug, to, *, reply_to=None, list_unsubscribe=None, **vars_):
        sent_emails.append({
            "slug": slug, "to": to, "reply_to": reply_to,
            "list_unsubscribe": list_unsubscribe, "vars": vars_,
        })
        return {"id": f"fake-{slug}-{len(sent_emails)}"}

    monkeypatch.setattr(email_service, "send_template", fake_send)

    transport = ASGITransport(app=server.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac, mock_db

"""End-to-end API tests.

Each test hits the FastAPI app via an in-memory ASGI transport, against
an in-memory Mongo, with Resend mocked. Coverage:

- GET  /api/health
- POST /api/subscribe           (double opt-in start)
- GET  /api/subscribe/confirm   (double opt-in complete)
- POST /api/unsubscribe
- POST /api/feedback            (ticket ack + admin notify)
- POST /api/contact
- Validation errors             (bad email, short message)
- Rate limiting                 (per-IP on /subscribe + /feedback)
- Admin weekly dispatch         (requires bearer)
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def test_health(client):
    ac, _ = client
    r = await ac.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["service"] == "liveastrology-backend"


async def test_subscribe_creates_pending_and_sends_two_emails(client, sent_emails):
    ac, db = client
    r = await ac.post("/api/subscribe", json={"email": "alex@example.com", "first_name": "Alex"})
    assert r.status_code == 202
    assert r.json() == {"status": "pending", "message": "Please check your inbox to confirm your subscription."}

    sub = await db.subscribers.find_one({"email": "alex@example.com"}, {"_id": 0})
    assert sub is not None
    assert sub["status"] == "pending"
    assert sub["confirm_token"]
    assert sub["unsub_token"]

    # One user email (template 01) + one admin email (template 07)
    slugs = [e["slug"] for e in sent_emails]
    assert "subscribe_confirm" in slugs
    assert "admin_notification" in slugs
    user_email = next(e for e in sent_emails if e["slug"] == "subscribe_confirm")
    assert user_email["to"] == "alex@example.com"
    assert "confirm_url" in user_email["vars"]
    assert user_email["list_unsubscribe"]


async def test_subscribe_is_idempotent(client, sent_emails):
    ac, db = client
    await ac.post("/api/subscribe", json={"email": "alex@example.com"})
    await ac.post("/api/subscribe", json={"email": "alex@example.com"})
    count = await db.subscribers.count_documents({"email": "alex@example.com"})
    assert count == 1


async def test_confirm_redirects_and_sends_welcome(client, sent_emails):
    ac, db = client
    await ac.post("/api/subscribe", json={"email": "alex@example.com"})
    sub = await db.subscribers.find_one({"email": "alex@example.com"}, {"_id": 0})
    token = sub["confirm_token"]

    r = await ac.get(f"/api/subscribe/confirm?token={token}", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"].endswith("/?subscribed=1")

    # Welcome email fires once
    welcomes = [e for e in sent_emails if e["slug"] == "subscribe_welcome"]
    assert len(welcomes) == 1
    assert welcomes[0]["to"] == "alex@example.com"

    # Second click doesn't re-send
    await ac.get(f"/api/subscribe/confirm?token={token}", follow_redirects=False)
    welcomes = [e for e in sent_emails if e["slug"] == "subscribe_welcome"]
    assert len(welcomes) == 1


async def test_confirm_invalid_token_redirects_with_reason(client):
    ac, _ = client
    r = await ac.get("/api/subscribe/confirm?token=nope", follow_redirects=False)
    assert r.status_code == 302
    assert "reason=invalid" in r.headers["location"]


async def test_unsubscribe_by_email(client, sent_emails):
    ac, db = client
    await ac.post("/api/subscribe", json={"email": "alex@example.com"})
    r = await ac.post("/api/unsubscribe", json={"email": "alex@example.com"})
    assert r.status_code == 200
    sub = await db.subscribers.find_one({"email": "alex@example.com"}, {"_id": 0})
    assert sub["status"] == "unsubscribed"
    assert any(e["slug"] == "unsubscribe_confirm" for e in sent_emails)


async def test_unsubscribe_missing_identifiers_400(client):
    ac, _ = client
    r = await ac.post("/api/unsubscribe", json={})
    assert r.status_code == 400


async def test_feedback_happy_path(client, sent_emails):
    ac, db = client
    r = await ac.post("/api/feedback", json={
        "name": "Alex", "email": "alex@example.com",
        "rating": 5, "category": "praise",
        "message": "Absolutely love this site!",
    })
    assert r.status_code == 202
    body = r.json()
    assert body["status"] == "ok"
    assert body["ticket_id"].startswith("FB-")

    stored = await db.feedback.find_one({"ticket_id": body["ticket_id"]}, {"_id": 0})
    assert stored["email"] == "alex@example.com"
    assert stored["rating"] == 5

    slugs = [e["slug"] for e in sent_emails]
    assert "feedback_ack" in slugs
    assert "admin_notification" in slugs
    ack = next(e for e in sent_emails if e["slug"] == "feedback_ack")
    assert ack["vars"]["rating_stars"].startswith("★★★★★")


async def test_feedback_without_email_still_notifies_admin(client, sent_emails):
    ac, _ = client
    r = await ac.post("/api/feedback", json={
        "category": "bug",
        "message": "Something's broken but I'm shy about email.",
    })
    assert r.status_code == 202
    slugs = [e["slug"] for e in sent_emails]
    # No user ack (no email provided)…
    assert "feedback_ack" not in slugs
    # …but admin still gets notified.
    assert "admin_notification" in slugs


async def test_feedback_message_too_short_422(client):
    ac, _ = client
    r = await ac.post("/api/feedback", json={"category": "general", "message": "hi"})
    assert r.status_code == 422


async def test_subscribe_invalid_email_422(client):
    ac, _ = client
    r = await ac.post("/api/subscribe", json={"email": "not-an-email"})
    assert r.status_code == 422


async def test_contact_happy_path(client, sent_emails):
    ac, db = client
    r = await ac.post("/api/contact", json={
        "name": "Alex", "email": "alex@example.com",
        "subject": "Partnership", "message": "Hi — would love to chat about a collab.",
    })
    assert r.status_code == 202
    body = r.json()
    assert body["ticket_id"].startswith("CT-")
    stored = await db.contacts.find_one({"ticket_id": body["ticket_id"]}, {"_id": 0})
    assert stored["subject"] == "Partnership"
    slugs = [e["slug"] for e in sent_emails]
    assert "contact_ack" in slugs
    assert "admin_notification" in slugs


async def test_admin_weekly_requires_bearer(client):
    ac, _ = client
    r = await ac.post("/api/admin/dispatch-weekly")
    assert r.status_code == 401


async def test_admin_weekly_runs_and_reports(client, sent_emails):
    ac, db = client
    # Seed two confirmed subscribers
    await ac.post("/api/subscribe", json={"email": "a@example.com", "first_name": "Ada"})
    sub = await db.subscribers.find_one({"email": "a@example.com"}, {"_id": 0})
    await ac.get(f"/api/subscribe/confirm?token={sub['confirm_token']}", follow_redirects=False)

    await ac.post("/api/subscribe", json={"email": "b@example.com", "first_name": "Bo"})
    sub2 = await db.subscribers.find_one({"email": "b@example.com"}, {"_id": 0})
    await ac.get(f"/api/subscribe/confirm?token={sub2['confirm_token']}", follow_redirects=False)

    sent_emails.clear()

    r = await ac.post(
        "/api/admin/dispatch-weekly",
        headers={"Authorization": "Bearer test-admin-secret"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert body["sent"] == 2

    weekly = [e for e in sent_emails if e["slug"] == "weekly_horoscope"]
    assert len(weekly) == 2
    assert {e["to"] for e in weekly} == {"a@example.com", "b@example.com"}



async def test_rate_limit_on_subscribe(client):
    """5/minute limit on /api/subscribe — the 6th request from the same IP
    returns 429. Verified by flipping the limiter back on."""
    ac, _ = client
    import server
    server.limiter.enabled = True
    server.limiter.reset()
    try:
        for i in range(5):
            r = await ac.post("/api/subscribe", json={"email": f"rate{i}@example.com"})
            assert r.status_code == 202, f"call {i} expected 202, got {r.status_code}"
        r = await ac.post("/api/subscribe", json={"email": "overflow@example.com"})
        assert r.status_code == 429
        assert "Too many requests" in r.json()["detail"]
    finally:
        server.limiter.enabled = False
        server.limiter.reset()



async def test_admin_feedback_queue(client):
    """/api/admin/feedback returns newest-first with mailto-ready fields."""
    ac, _ = client
    # Seed 3 feedback submissions
    for i in range(3):
        await ac.post("/api/feedback", json={
            "name": f"User {i}", "email": f"u{i}@example.com",
            "category": "praise", "message": f"Queue test message number {i}",
        })
    r = await ac.get("/api/admin/feedback", headers={"Authorization": "Bearer test-admin-secret"})
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 3
    assert len(body["items"]) == 3
    messages = {item["message"] for item in body["items"]}
    assert messages == {"Queue test message number 0", "Queue test message number 1", "Queue test message number 2"}
    # No _id leaking
    assert "_id" not in body["items"][0]
    # Required fields present
    for item in body["items"]:
        assert "ticket_id" in item
        assert item["ticket_id"].startswith("FB-")
        assert "email" in item
        assert "created_at" in item


async def test_admin_contacts_queue(client):
    """/api/admin/contacts returns contact submissions newest-first."""
    ac, _ = client
    for i in range(2):
        await ac.post("/api/contact", json={
            "name": f"Contact {i}", "email": f"c{i}@example.com",
            "subject": f"Subject {i}", "message": f"Contact queue test message {i}",
        })
    r = await ac.get("/api/admin/contacts", headers={"Authorization": "Bearer test-admin-secret"})
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 2
    subjects = {item["subject"] for item in body["items"]}
    assert subjects == {"Subject 0", "Subject 1"}
    assert body["items"][0]["ticket_id"].startswith("CT-")


async def test_admin_queue_requires_auth(client):
    ac, _ = client
    for path in ["/api/admin/feedback", "/api/admin/contacts"]:
        r = await ac.get(path)
        assert r.status_code == 401, f"{path} should require auth"


async def test_turnstile_rejects_when_enabled(client, monkeypatch):
    """When TURNSTILE_DISABLED is off and no token is supplied, /subscribe 403s."""
    import os, turnstile as t_mod
    monkeypatch.setenv("TURNSTILE_DISABLED", "0")
    monkeypatch.setenv("CF_TURNSTILE_SECRET", "fake-secret")

    async def fake_verify(token, *, remote_ip=None):
        # Valid only if token starts with 'good'
        return bool(token and token.startswith("good"))
    monkeypatch.setattr(t_mod, "verify", fake_verify)

    ac, _ = client
    # Missing token
    r = await ac.post("/api/subscribe", json={"email": "captcha-miss@example.com"})
    assert r.status_code == 403
    assert "verification" in r.json()["detail"].lower()
    # Bad token
    r = await ac.post("/api/subscribe", json={"email": "captcha-bad@example.com", "cf_turnstile_token": "bad-token"})
    assert r.status_code == 403
    # Good token
    r = await ac.post("/api/subscribe", json={"email": "captcha-ok@example.com", "cf_turnstile_token": "good-token"})
    assert r.status_code == 202


async def test_mark_feedback_resolved(client):
    """PATCH /api/admin/feedback/{id} toggles the resolved flag."""
    ac, db = client
    await ac.post("/api/feedback", json={"category": "bug", "message": "Something is broken here"})
    fb = await db.feedback.find_one({}, {"_id": 0})
    tid = fb["ticket_id"]

    r = await ac.patch(
        f"/api/admin/feedback/{tid}",
        headers={"Authorization": "Bearer test-admin-secret"},
        json={"resolved": True},
    )
    assert r.status_code == 200
    assert r.json()["resolved"] is True

    # only_open filter now excludes it
    r2 = await ac.get("/api/admin/feedback?only_open=true", headers={"Authorization": "Bearer test-admin-secret"})
    assert r2.status_code == 200
    assert all(i["ticket_id"] != tid for i in r2.json()["items"])

    # Un-resolve
    r3 = await ac.patch(
        f"/api/admin/feedback/{tid}",
        headers={"Authorization": "Bearer test-admin-secret"},
        json={"resolved": False},
    )
    assert r3.json()["resolved"] is False


async def test_mark_feedback_resolved_404(client):
    ac, _ = client
    r = await ac.patch(
        "/api/admin/feedback/NOPE-123",
        headers={"Authorization": "Bearer test-admin-secret"},
        json={"resolved": True},
    )
    assert r.status_code == 404


async def test_subscribers_csv_export(client):
    """CSV export returns one row per matching subscriber + a header row."""
    ac, db = client
    # Seed two confirmed, one pending
    for i in range(2):
        await ac.post("/api/subscribe", json={"email": f"confirmed{i}@example.com", "first_name": f"C{i}"})
        sub = await db.subscribers.find_one({"email": f"confirmed{i}@example.com"}, {"_id": 0})
        await ac.get(f"/api/subscribe/confirm?token={sub['confirm_token']}", follow_redirects=False)
    await ac.post("/api/subscribe", json={"email": "pending@example.com"})

    r = await ac.get("/api/admin/subscribers.csv?status=confirmed", headers={"Authorization": "Bearer test-admin-secret"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert "filename=" in r.headers["content-disposition"]
    body = r.text
    # 1 header + 2 data rows
    lines = [ln for ln in body.splitlines() if ln.strip()]
    assert lines[0].startswith("email,first_name,status")
    assert len(lines) == 3
    assert "confirmed0@example.com" in body
    assert "pending@example.com" not in body

    # status=all includes the pending one
    r2 = await ac.get("/api/admin/subscribers.csv?status=all", headers={"Authorization": "Bearer test-admin-secret"})
    lines2 = [ln for ln in r2.text.splitlines() if ln.strip()]
    assert len(lines2) == 4


async def test_subscribers_csv_requires_auth(client):
    ac, _ = client
    r = await ac.get("/api/admin/subscribers.csv")
    assert r.status_code == 401


async def test_feedback_pagination(client):
    ac, _ = client
    for i in range(5):
        await ac.post("/api/feedback", json={"category": "general", "message": f"Pagination test message {i}"})
    r = await ac.get("/api/admin/feedback?limit=2&skip=0", headers={"Authorization": "Bearer test-admin-secret"})
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 2
    assert body["total"] == 5
    assert body["limit"] == 2
    assert body["skip"] == 0

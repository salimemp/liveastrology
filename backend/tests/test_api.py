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



async def test_admin_list_subscribers(client):
    ac, _ = client
    for i in range(3):
        await ac.post("/api/subscribe", json={"email": f"s{i}@example.com", "first_name": f"S{i}"})
    r = await ac.get("/api/admin/subscribers", headers={"Authorization": "Bearer test-admin-secret"})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3
    assert "confirm_token" not in body["items"][0]
    assert "unsub_token" not in body["items"][0]


async def test_admin_subscriber_force_unsubscribe(client):
    ac, db = client
    await ac.post("/api/subscribe", json={"email": "force@example.com"})
    r = await ac.post(
        "/api/admin/subscribers/force@example.com/actions",
        headers={"Authorization": "Bearer test-admin-secret"},
        json={"action": "force_unsubscribe"},
    )
    assert r.status_code == 200
    sub = await db.subscribers.find_one({"email": "force@example.com"}, {"_id": 0})
    assert sub["status"] == "unsubscribed"


async def test_admin_subscriber_delete(client):
    ac, db = client
    await ac.post("/api/subscribe", json={"email": "bye@example.com"})
    r = await ac.post(
        "/api/admin/subscribers/bye@example.com/actions",
        headers={"Authorization": "Bearer test-admin-secret"},
        json={"action": "delete"},
    )
    assert r.status_code == 200
    sub = await db.subscribers.find_one({"email": "bye@example.com"})
    assert sub is None


async def test_admin_subscriber_resend_confirm(client, sent_emails):
    ac, _ = client
    await ac.post("/api/subscribe", json={"email": "redo@example.com"})
    sent_emails.clear()
    r = await ac.post(
        "/api/admin/subscribers/redo@example.com/actions",
        headers={"Authorization": "Bearer test-admin-secret"},
        json={"action": "resend_confirm"},
    )
    assert r.status_code == 200
    assert any(e["slug"] == "subscribe_confirm" for e in sent_emails)


async def test_admin_subscriber_resend_confirm_rejects_already_confirmed(client):
    ac, db = client
    await ac.post("/api/subscribe", json={"email": "done@example.com"})
    sub = await db.subscribers.find_one({"email": "done@example.com"}, {"_id": 0})
    await ac.get(f"/api/subscribe/confirm?token={sub['confirm_token']}", follow_redirects=False)
    r = await ac.post(
        "/api/admin/subscribers/done@example.com/actions",
        headers={"Authorization": "Bearer test-admin-secret"},
        json={"action": "resend_confirm"},
    )
    assert r.status_code == 400


async def test_admin_subscriber_action_requires_auth(client):
    ac, _ = client
    r = await ac.post(
        "/api/admin/subscribers/nope@example.com/actions",
        json={"action": "delete"},
    )
    assert r.status_code == 401



# ---------- Resend webhook ingestion ----------

async def test_resend_webhook_unsigned_accepted_in_dev(client):
    """When RESEND_WEBHOOK_SECRET is empty (dev mode), unsigned payloads are accepted."""
    ac, db = client
    r = await ac.post("/api/webhooks/resend", json={
        "type": "email.delivered",
        "created_at": "2026-02-14T10:00:00Z",
        "data": {
            "email_id": "abc-123",
            "from": "hello@liveastrology.app",
            "to": ["alex@example.com"],
            "subject": "Welcome",
        },
    })
    assert r.status_code == 202
    assert r.json() == {"status": "ok", "event": "email.delivered"}

    stored = await db.email_events.find_one({"email_id": "abc-123"}, {"_id": 0})
    assert stored is not None
    assert stored["type"] == "email.delivered"
    assert stored["to"] == "alex@example.com"
    assert stored["subject"] == "Welcome"


async def test_resend_webhook_records_each_event_type(client):
    """delivered / bounced / opened / complained all reach the email_events collection."""
    ac, db = client
    for et in ("email.sent", "email.delivered", "email.bounced", "email.opened", "email.complained"):
        r = await ac.post("/api/webhooks/resend", json={
            "type": et,
            "data": {"email_id": f"id-{et}", "to": ["x@example.com"]},
        })
        assert r.status_code == 202

    counts = {
        et: await db.email_events.count_documents({"type": et})
        for et in ("email.sent", "email.delivered", "email.bounced", "email.opened", "email.complained")
    }
    assert counts == {"email.sent": 1, "email.delivered": 1, "email.bounced": 1, "email.opened": 1, "email.complained": 1}


async def test_admin_stats_includes_email_health(client):
    """/api/admin/stats now exposes deliverability counts derived from webhook events."""
    ac, _ = client
    # Seed webhook events
    for et, n in [("email.delivered", 10), ("email.bounced", 1), ("email.opened", 4), ("email.complained", 0), ("email.sent", 11)]:
        for i in range(n):
            await ac.post("/api/webhooks/resend", json={
                "type": et,
                "data": {"email_id": f"{et}-{i}", "to": ["x@example.com"]},
            })

    r = await ac.get("/api/admin/stats", headers={"Authorization": "Bearer test-admin-secret"})
    assert r.status_code == 200
    eh = r.json()["email_health"]
    assert eh["delivered"] == 10
    assert eh["bounced"] == 1
    assert eh["opened"] == 4
    assert eh["sent"] == 11
    assert eh["bounce_rate_pct"] == 10.0
    assert eh["open_rate_pct"] == 40.0
    assert eh["webhook_configured"] is False
    assert eh["last_event_type"] in ("email.sent", "email.delivered", "email.bounced", "email.opened")


async def test_resend_webhook_rejects_invalid_signature_when_secret_set(client, monkeypatch):
    """When RESEND_WEBHOOK_SECRET is configured, unsigned/wrong-signed payloads are rejected with 401."""
    import server
    monkeypatch.setattr(server, "RESEND_WEBHOOK_SECRET", "whsec_test_dummy_secret_for_unit_test")

    ac, _ = client
    r = await ac.post("/api/webhooks/resend", json={"type": "email.delivered", "data": {}})
    assert r.status_code == 401
    assert "signature" in r.json()["detail"].lower()


async def test_resend_webhook_accepts_valid_svix_signature(client, monkeypatch):
    """A correctly-signed Svix payload passes verification and is recorded."""
    import json as _json
    from svix.webhooks import Webhook
    import server

    secret = "whsec_" + "A" * 32  # base64-friendly fake secret accepted by svix-py
    monkeypatch.setattr(server, "RESEND_WEBHOOK_SECRET", secret)

    body = {
        "type": "email.bounced",
        "data": {"email_id": "signed-1", "to": ["bounced@example.com"], "subject": "Hi"},
    }
    payload = _json.dumps(body)
    msg_id = "msg_test_1"
    import datetime as _dt
    now_dt = _dt.datetime.now(tz=_dt.timezone.utc)
    timestamp = str(int(now_dt.timestamp()))
    signature = Webhook(secret).sign(msg_id=msg_id, timestamp=now_dt, data=payload)

    ac, db = client
    r = await ac.post(
        "/api/webhooks/resend",
        content=payload,
        headers={
            "Content-Type": "application/json",
            "svix-id": msg_id,
            "svix-timestamp": timestamp,
            "svix-signature": signature,
        },
    )
    assert r.status_code == 202, r.text
    stored = await db.email_events.find_one({"email_id": "signed-1"}, {"_id": 0})
    assert stored is not None
    assert stored["type"] == "email.bounced"


# ---------- Articles CMS ----------

LONG_CONTENT = ("Hello world. " * 50).strip()  # ~100 words → passes min_length validation


async def test_articles_public_list_empty_initially(client):
    ac, _ = client
    r = await ac.get("/api/articles")
    assert r.status_code == 200
    assert r.json() == []


async def test_admin_create_article_then_visible_publicly(client):
    ac, _ = client
    r = await ac.post(
        "/api/admin/articles",
        headers={"Authorization": "Bearer test-admin-secret"},
        json={
            "title": "My First Article",
            "excerpt": "A short summary of the article.",
            "content": LONG_CONTENT,
            "author": "Test",
            "category": "Astrology Basics",
            "tags": ["test", "first"],
            "status": "published",
        },
    )
    assert r.status_code == 201, r.text
    created = r.json()
    assert created["slug"] == "my-first-article"
    assert created["read_time"]  # auto-derived
    assert created["word_count"] >= 100

    # Public list now has 1 item
    pub = await ac.get("/api/articles")
    assert pub.status_code == 200
    assert len(pub.json()) == 1
    assert pub.json()[0]["slug"] == "my-first-article"
    # Public list does NOT include full content
    assert "content" not in pub.json()[0]

    # Public detail returns full content
    detail = await ac.get("/api/articles/my-first-article")
    assert detail.status_code == 200
    assert detail.json()["content"] == LONG_CONTENT


async def test_admin_create_article_requires_auth(client):
    ac, _ = client
    r = await ac.post("/api/admin/articles", json={
        "title": "x", "excerpt": "yyyyyyyyyy", "content": LONG_CONTENT,
        "author": "x", "category": "x",
    })
    assert r.status_code == 401


async def test_draft_article_hidden_from_public(client):
    ac, _ = client
    await ac.post(
        "/api/admin/articles",
        headers={"Authorization": "Bearer test-admin-secret"},
        json={
            "title": "Draft Post",
            "excerpt": "Draft excerpt only.",
            "content": LONG_CONTENT,
            "author": "Editor",
            "category": "Drafts",
            "status": "draft",
        },
    )
    pub_list = await ac.get("/api/articles")
    assert all(a["slug"] != "draft-post" for a in pub_list.json())
    pub_detail = await ac.get("/api/articles/draft-post")
    assert pub_detail.status_code == 404
    # But admin can still see it
    admin_detail = await ac.get(
        "/api/admin/articles/draft-post",
        headers={"Authorization": "Bearer test-admin-secret"},
    )
    assert admin_detail.status_code == 200
    assert admin_detail.json()["status"] == "draft"


async def test_slug_collision_appends_suffix(client):
    ac, _ = client
    body = lambda: {
        "title": "Same Title", "excerpt": "Same excerpt blah.", "content": LONG_CONTENT,
        "author": "x", "category": "x",
    }
    r1 = await ac.post("/api/admin/articles", headers={"Authorization": "Bearer test-admin-secret"}, json=body())
    r2 = await ac.post("/api/admin/articles", headers={"Authorization": "Bearer test-admin-secret"}, json=body())
    r3 = await ac.post("/api/admin/articles", headers={"Authorization": "Bearer test-admin-secret"}, json=body())
    slugs = sorted([r1.json()["slug"], r2.json()["slug"], r3.json()["slug"]])
    assert slugs == ["same-title", "same-title-2", "same-title-3"]


async def test_patch_article_updates_fields_and_publishes(client):
    ac, _ = client
    await ac.post(
        "/api/admin/articles",
        headers={"Authorization": "Bearer test-admin-secret"},
        json={
            "title": "To Be Edited", "excerpt": "Will be edited.", "content": LONG_CONTENT,
            "author": "x", "category": "x", "status": "draft",
        },
    )
    r = await ac.patch(
        "/api/admin/articles/to-be-edited",
        headers={"Authorization": "Bearer test-admin-secret"},
        json={"title": "Edited Title", "status": "published"},
    )
    assert r.status_code == 200
    assert r.json()["title"] == "Edited Title"
    assert r.json()["status"] == "published"
    assert r.json()["published_at"] is not None


async def test_delete_article(client):
    ac, _ = client
    await ac.post(
        "/api/admin/articles",
        headers={"Authorization": "Bearer test-admin-secret"},
        json={
            "title": "Delete Me", "excerpt": "A doomed article.", "content": LONG_CONTENT,
            "author": "x", "category": "x",
        },
    )
    r = await ac.delete(
        "/api/admin/articles/delete-me",
        headers={"Authorization": "Bearer test-admin-secret"},
    )
    assert r.status_code == 200
    # Now 404
    r2 = await ac.get("/api/articles/delete-me")
    assert r2.status_code == 404




# ---------- AI interpretation + charts-today counter ----------
async def test_charts_today_returns_baseline(client):
    """Counter should return a positive integer even with zero real charts."""
    ac, _ = client
    r = await ac.get("/api/charts-today")
    assert r.status_code == 200
    data = r.json()
    assert "date" in data
    assert isinstance(data["charts_today"], int)
    assert data["charts_today"] > 0


async def test_interpret_validates_signs(client):
    """Invalid zodiac sign names should return 422 (Pydantic) or 422 from module."""
    ac, _ = client
    r = await ac.post("/api/interpret", json={"sun": "Banana", "moon": "Pisces", "rising": "Leo"})
    assert r.status_code == 422


async def test_interpret_uses_module_and_increments_counter(client, monkeypatch):
    """The /api/interpret endpoint delegates to interpretation.get_interpretation
    and bumps the daily counter on success."""
    import interpretation

    async def fake_get(db, sun, moon, rising):
        return {
            "sun":    f"Mock {sun.capitalize()} reading.",
            "moon":   f"Mock {moon.capitalize()} reading.",
            "rising": f"Mock {rising.capitalize()} reading.",
        }

    monkeypatch.setattr(interpretation, "get_interpretation", fake_get)

    ac, _ = client
    before = (await ac.get("/api/charts-today")).json()["charts_today"]

    r = await ac.post("/api/interpret", json={"sun": "Aries", "moon": "Taurus", "rising": "Gemini"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["interpretation"]["sun"] == "Mock Aries reading."

    after = (await ac.get("/api/charts-today")).json()["charts_today"]
    assert after == before + 1


async def test_interpret_returns_503_on_runtime_error(client, monkeypatch):
    """If the underlying interpretation module raises RuntimeError, the API
    surfaces a 503 instead of a 500."""
    import interpretation

    async def fail(db, sun, moon, rising):
        raise RuntimeError("LLM down")

    monkeypatch.setattr(interpretation, "get_interpretation", fail)

    ac, _ = client
    r = await ac.post("/api/interpret", json={"sun": "Leo", "moon": "Scorpio", "rising": "Cancer"})
    assert r.status_code == 503
    assert "LLM down" in r.json()["detail"]


# ---------- SEO seed articles (Phase 2 of marketing audit) ----------
async def test_seed_seo_articles_inserts_five(client):
    ac, mock_db = client
    r = await ac.post(
        "/api/admin/seed-seo-articles",
        headers={"Authorization": "Bearer test-admin-secret"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert len(body["inserted"]) == 5
    # All 5 should be queryable on the public endpoint with >1000 word counts.
    listing = await ac.get("/api/articles?limit=20")
    assert listing.status_code == 200
    items = listing.json()
    slugs = {a["slug"] for a in items}
    assert "what-does-moon-in-scorpio-mean-a-plain-english-guide" in slugs
    assert "sun-sign-vs-moon-sign-vs-rising-sign-which-one-actually-matters" in slugs
    for a in items:
        if a["slug"] in body["inserted"]:
            assert a["word_count"] > 1000


async def test_seed_seo_articles_is_idempotent(client):
    ac, _ = client
    r1 = await ac.post("/api/admin/seed-seo-articles", headers={"Authorization": "Bearer test-admin-secret"})
    assert r1.status_code == 200
    assert len(r1.json()["inserted"]) == 5
    r2 = await ac.post("/api/admin/seed-seo-articles", headers={"Authorization": "Bearer test-admin-secret"})
    assert r2.status_code == 200
    body = r2.json()
    assert body["inserted"] == []
    assert len(body["skipped"]) == 5


async def test_seed_seo_articles_force_updates(client):
    ac, _ = client
    await ac.post("/api/admin/seed-seo-articles", headers={"Authorization": "Bearer test-admin-secret"})
    r = await ac.post("/api/admin/seed-seo-articles?force=true", headers={"Authorization": "Bearer test-admin-secret"})
    assert r.status_code == 200
    body = r.json()
    assert len(body["updated"]) == 5
    assert body["inserted"] == []


async def test_seed_seo_articles_requires_auth(client):
    ac, _ = client
    r = await ac.post("/api/admin/seed-seo-articles")
    assert r.status_code == 401



# ---------- Billing / Premium subscription (Phase 3) ----------
async def test_billing_packages_returns_two_plans(client):
    ac, _ = client
    r = await ac.get("/api/billing/packages")
    assert r.status_code == 200
    data = r.json()
    ids = {p["id"] for p in data["packages"]}
    assert ids == {"monthly", "yearly"}
    monthly = next(p for p in data["packages"] if p["id"] == "monthly")
    yearly  = next(p for p in data["packages"] if p["id"] == "yearly")
    assert monthly["amount"] == 4.99
    assert yearly["amount"] == 39.0


async def test_billing_status_for_unknown_email_returns_inactive(client):
    ac, _ = client
    r = await ac.get("/api/billing/status?email=nobody@example.com")
    assert r.status_code == 200
    data = r.json()
    assert data["active"] is False
    assert data["plan"] is None
    assert data["expires_at"] is None


async def test_billing_checkout_validates_package(client):
    ac, _ = client
    r = await ac.post(
        "/api/billing/checkout",
        json={"package_id": "lifetime", "email": "x@y.com", "origin_url": "https://t.example"},
    )
    assert r.status_code == 422  # Pydantic Literal rejection


async def test_billing_checkout_validates_email(client):
    ac, _ = client
    r = await ac.post(
        "/api/billing/checkout",
        json={"package_id": "monthly", "email": "not-an-email", "origin_url": "https://t.example"},
    )
    assert r.status_code == 422


async def test_billing_checkout_creates_pending_transaction(client, monkeypatch):
    """Mock Stripe so we can verify the pending payment_transactions row
    is written before the redirect URL is returned."""
    import billing

    class _FakeSession:
        url = "https://stripe.test/checkout"
        session_id = "cs_test_fake_123"

    class _FakeCheckout:
        def __init__(self, *a, **kw): pass
        async def create_checkout_session(self, req): return _FakeSession()

    monkeypatch.setattr(billing, "STRIPE_API_KEY", "sk_test_fake")

    # Patch the import inside the create function. emergentintegrations
    # may not be importable in CI, so we need to satisfy the import
    # statement by injecting a fake module first.
    import sys
    import types
    fake_root = types.ModuleType("emergentintegrations")
    fake_payments = types.ModuleType("emergentintegrations.payments")
    fake_stripe = types.ModuleType("emergentintegrations.payments.stripe")
    fake_checkout_mod = types.ModuleType("emergentintegrations.payments.stripe.checkout")
    fake_checkout_mod.StripeCheckout = _FakeCheckout
    class _FakeRequest:
        def __init__(self, **kw): pass
    fake_checkout_mod.CheckoutSessionRequest = _FakeRequest
    sys.modules["emergentintegrations"] = fake_root
    sys.modules["emergentintegrations.payments"] = fake_payments
    sys.modules["emergentintegrations.payments.stripe"] = fake_stripe
    sys.modules["emergentintegrations.payments.stripe.checkout"] = fake_checkout_mod

    ac, mock_db = client
    r = await ac.post(
        "/api/billing/checkout",
        json={"package_id": "monthly", "email": "buyer@example.com", "origin_url": "https://app.test"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["url"] == "https://stripe.test/checkout"
    assert data["session_id"] == "cs_test_fake_123"

    txn = await mock_db.payment_transactions.find_one({"session_id": "cs_test_fake_123"}, {"_id": 0})
    assert txn is not None
    assert txn["status"] == "initiated"
    assert txn["payment_status"] == "unpaid"
    assert txn["email"] == "buyer@example.com"
    assert txn["amount"] == 4.99


async def test_billing_grants_entitlement_on_paid_status(client, monkeypatch):
    """Once Stripe reports payment_status=paid, the entitlement row is
    created and /api/billing/status flips to active."""
    import billing
    from datetime import datetime, timezone

    monkeypatch.setattr(billing, "STRIPE_API_KEY", "sk_test_fake")

    ac, mock_db = client
    # Seed a pending transaction by calling DB directly (bypasses Stripe).
    await mock_db.payment_transactions.insert_one({
        "session_id": "cs_test_paid_1",
        "email": "vip@example.com",
        "package_id": "yearly",
        "plan_label": "Premium Yearly",
        "amount": 39.0,
        "currency": "usd",
        "days": 365,
        "status": "open",
        "payment_status": "unpaid",
        "metadata": {},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    })

    class _FakeStatus:
        status = "complete"
        payment_status = "paid"
        amount_total = 3900
        currency = "usd"
        metadata = {}

    class _FakeCheckout:
        def __init__(self, *a, **kw): pass
        async def get_checkout_status(self, sid): return _FakeStatus()

    import sys
    fake_mod = sys.modules.get("emergentintegrations.payments.stripe.checkout")
    if fake_mod is None:
        import types
        fake_mod = types.ModuleType("emergentintegrations.payments.stripe.checkout")
        sys.modules["emergentintegrations.payments.stripe.checkout"] = fake_mod
    fake_mod.StripeCheckout = _FakeCheckout

    r = await ac.get("/api/billing/checkout/status/cs_test_paid_1")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["payment_status"] == "paid"
    assert data["granted"] is not None
    assert data["granted"]["plan"] == "yearly"

    status = await ac.get("/api/billing/status?email=vip@example.com")
    body = status.json()
    assert body["active"] is True
    assert body["plan"] == "yearly"

    # Polling again must not double-grant.
    r2 = await ac.get("/api/billing/checkout/status/cs_test_paid_1")
    assert r2.status_code == 200
    assert r2.json()["granted"] is None



# ---------- Beta launch (Phase 4) ----------
async def test_beta_status_initial_state(client):
    ac, _ = client
    r = await ac.get("/api/beta/status")
    assert r.status_code == 200
    body = r.json()
    assert body["total_seats"] == 100
    assert body["seats_claimed"] == 0
    assert body["seats_remaining"] == 100
    assert body["waitlist_size"] == 0
    assert body["me"] is None


async def test_beta_claim_grants_entitlement(client):
    ac, mock_db = client
    r = await ac.post("/api/beta/claim", json={"email": "alpha@example.com", "name": "Alpha"})
    assert r.status_code == 200
    body = r.json()
    assert body["result"] == "granted"
    assert body["claim_number"] == 1
    assert body["seats_remaining"] == 99
    # Entitlement row exists and is active
    ent = await mock_db.entitlements.find_one({"email": "alpha@example.com"}, {"_id": 0})
    assert ent is not None
    assert ent["plan"] == "beta"
    # Billing status reflects active premium
    s = await ac.get("/api/billing/status?email=alpha@example.com")
    assert s.status_code == 200
    assert s.json()["active"] is True


async def test_beta_claim_is_idempotent_per_email(client):
    ac, _ = client
    r1 = await ac.post("/api/beta/claim", json={"email": "dup@example.com"})
    assert r1.status_code == 200
    assert r1.json()["result"] == "granted"
    r2 = await ac.post("/api/beta/claim", json={"email": "dup@example.com"})
    assert r2.status_code == 200
    assert r2.json()["result"] == "already_claimed"
    # Seat counter must not double-decrement
    status = await ac.get("/api/beta/status")
    assert status.json()["seats_claimed"] == 1


async def test_beta_claim_overflow_goes_to_waitlist(client, monkeypatch):
    import beta
    # Shrink the cap so the test is fast
    monkeypatch.setattr(beta, "BETA_TOTAL_SEATS", 2)

    ac, _ = client
    for i in range(2):
        r = await ac.post("/api/beta/claim", json={"email": f"early-{i}@example.com"})
        assert r.json()["result"] == "granted"

    # 3rd claim must be waitlisted with a position
    r = await ac.post("/api/beta/claim", json={"email": "late@example.com"})
    assert r.status_code == 200
    body = r.json()
    assert body["result"] == "waitlisted"
    assert body["waitlist_position"] == 1


async def test_beta_claim_validates_email(client):
    ac, _ = client
    r = await ac.post("/api/beta/claim", json={"email": "not-an-email"})
    assert r.status_code == 422


# ---------- Feedback: new beta rating fields + publish consent ----------
async def test_feedback_accepts_extended_rating_fields(client):
    ac, mock_db = client
    payload = {
        "name": "Tester",
        "email": "test@example.com",
        "message": "Loved the AI reading, UI is clean",
        "category": "praise",
        "rating": 5,
        "rating_accuracy": 5,
        "rating_ui": 4,
        "rating_ai_quality": 5,
        "rating_recommend": 5,
        "publish_consent": True,
    }
    r = await ac.post("/api/feedback", json=payload)
    assert r.status_code == 202, r.text
    body = r.json()
    assert body["status"] == "ok"
    row = await mock_db.feedback.find_one({"ticket_id": body["ticket_id"]}, {"_id": 0})
    assert row["rating_accuracy"] == 5
    assert row["rating_ui"] == 4
    assert row["publish_consent"] is True
    # Must default to unpublished — consent ≠ approval
    assert row["published"] is False


# ---------- Public testimonials ----------
async def test_testimonials_returns_only_published_and_consented(client):
    ac, mock_db = client
    # Insert one consented+published, one consented+unpublished, one not-consented
    from datetime import datetime, timezone
    base = {"created_at": datetime.now(timezone.utc), "category": "praise"}
    await mock_db.feedback.insert_many([
        {**base, "ticket_id": "T1", "name": "Approved",   "message": "Great app",   "publish_consent": True,  "published": True},
        {**base, "ticket_id": "T2", "name": "Pending",    "message": "Cool app",    "publish_consent": True,  "published": False},
        {**base, "ticket_id": "T3", "name": "NoConsent",  "message": "Decent app",  "publish_consent": False, "published": True},
    ])
    r = await ac.get("/api/testimonials")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 1
    assert body["testimonials"][0]["name"] == "Approved"
    # Email must never leak even on public testimonial
    assert "email" not in body["testimonials"][0]


async def test_admin_publish_feedback_requires_consent(client):
    ac, mock_db = client
    from datetime import datetime, timezone
    await mock_db.feedback.insert_one({
        "ticket_id": "no-consent-1",
        "name": "User",
        "message": "Feedback",
        "category": "general",
        "publish_consent": False,
        "published": False,
        "created_at": datetime.now(timezone.utc),
    })
    r = await ac.post(
        "/api/admin/feedback/no-consent-1/publish",
        headers={"Authorization": "Bearer test-admin-secret"},
    )
    assert r.status_code == 404  # cannot publish what user didn't consent to


async def test_admin_publish_feedback_flips_published(client):
    ac, mock_db = client
    from datetime import datetime, timezone
    await mock_db.feedback.insert_one({
        "ticket_id": "ok-pub-1",
        "name": "User",
        "message": "Loved the chart",
        "category": "praise",
        "publish_consent": True,
        "published": False,
        "created_at": datetime.now(timezone.utc),
    })
    r = await ac.post(
        "/api/admin/feedback/ok-pub-1/publish",
        headers={"Authorization": "Bearer test-admin-secret"},
    )
    assert r.status_code == 200
    listing = await ac.get("/api/testimonials")
    names = [t["name"] for t in listing.json()["testimonials"]]
    assert "User" in names



# ---------- Premium monthly forecast (Phase 5) ----------
async def test_forecast_preview_requires_admin(client):
    ac, _ = client
    r = await ac.get("/api/admin/premium/forecast-preview")
    assert r.status_code == 401


async def test_forecast_preview_returns_cached_payload(client, monkeypatch):
    """get_monthly_forecast should be called and the cached payload
    returned without hitting the LLM."""
    import forecast
    from datetime import datetime, timezone

    fake_payload = {
        "theme_paragraph": "Stub theme.",
        "event_1_date": "Jul 4", "event_1_text": "Full Moon",
        "event_2_date": "Jul 14", "event_2_text": "Mercury ingress",
        "event_3_date": "Jul 27", "event_3_text": "New Moon",
        "practical_insight": "Stub insight.",
        "month_name": "July", "year": "2026",
    }

    async def fake_get(db, when=None, force=False):
        return fake_payload

    monkeypatch.setattr(forecast, "get_monthly_forecast", fake_get)

    ac, _ = client
    r = await ac.get(
        "/api/admin/premium/forecast-preview",
        headers={"Authorization": "Bearer test-admin-secret"},
    )
    assert r.status_code == 200
    assert r.json()["forecast"]["month_name"] == "July"


async def test_forecast_dispatch_only_active_entitlements(client, monkeypatch):
    import forecast
    from datetime import datetime, timedelta, timezone

    sent_to: list[str] = []

    async def fake_dispatch(db, sender, force=False, when=None):
        # Iterate entitlements like the real implementation does.
        cursor = db.entitlements.find({"status": "active"}, {"_id": 0, "email": 1, "expires_at": 1})
        now = datetime.now(timezone.utc)
        sent_count = 0
        inactive = 0
        async for ent in cursor:
            v = ent.get("expires_at")
            if isinstance(v, datetime):
                vt = v if v.tzinfo else v.replace(tzinfo=timezone.utc)
                if vt <= now:
                    inactive += 1
                    continue
            sent_to.append(ent["email"])
            sent_count += 1
        return {
            "month_key": "2026-07", "month_name": "July", "year": "2026",
            "sent_count": sent_count, "skipped_existing": 0,
            "skipped_inactive": inactive, "failed": [],
        }

    monkeypatch.setattr(forecast, "dispatch_monthly_forecast", fake_dispatch)

    ac, mock_db = client
    now = datetime.now(timezone.utc)
    await mock_db.entitlements.insert_many([
        {"email": "active@a.com",  "status": "active", "expires_at": now + timedelta(days=10)},
        {"email": "expired@a.com", "status": "active", "expires_at": now - timedelta(days=1)},
    ])

    r = await ac.post(
        "/api/admin/premium/dispatch-monthly-forecast",
        headers={"Authorization": "Bearer test-admin-secret"},
        json={"force": False},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["sent_count"] == 1
    assert body["skipped_inactive"] == 1
    assert sent_to == ["active@a.com"]


# ---------- Premium compatibility report (admin send) ----------
async def test_compatibility_requires_active_entitlement(client):
    ac, _ = client
    r = await ac.post(
        "/api/admin/premium/compatibility/send",
        headers={"Authorization": "Bearer test-admin-secret"},
        json={
            "recipient_email": "nope@example.com",
            "person1_name": "Ada", "person1_sun": "leo",    "person1_moon": "cancer",
            "person2_name": "Bo",  "person2_sun": "pisces", "person2_moon": "virgo",
            "score": 70,
        },
    )
    assert r.status_code == 409


async def test_compatibility_send_invokes_module(client, monkeypatch):
    import compatibility_reports as cr
    from datetime import datetime, timedelta, timezone

    captured: dict = {}

    async def fake_send(db, sender, **kw):
        captured.update(kw)
        return {
            "status": "sent",
            "recipient": kw["recipient_email"],
            "label": "Strong chemistry",
            "score": kw["score"],
            "word_counts": {"headline_paragraph": 90},
        }

    monkeypatch.setattr(cr, "generate_and_send", fake_send)

    ac, mock_db = client
    await mock_db.entitlements.insert_one({
        "email": "premium@example.com", "status": "active",
        "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
    })

    r = await ac.post(
        "/api/admin/premium/compatibility/send",
        headers={"Authorization": "Bearer test-admin-secret"},
        json={
            "recipient_email": "premium@example.com",
            "person1_name": "Ada", "person1_sun": "gemini", "person1_moon": "pisces",
            "person2_name": "Bo",  "person2_sun": "leo",    "person2_moon": "cancer",
            "score": 72,
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "sent"
    assert body["recipient"] == "premium@example.com"
    assert captured["person1_name"] == "Ada"


# ---------- Stripe webhook signature enforcement ----------
async def test_stripe_webhook_returns_400_when_secret_configured(client, monkeypatch):
    """When STRIPE_WEBHOOK_SECRET is set, unsigned/invalid payloads
    must return 400 so Stripe retries."""
    import billing

    monkeypatch.setattr(billing, "STRIPE_API_KEY", "sk_test_anything")
    monkeypatch.setattr(billing, "STRIPE_WEBHOOK_SECRET", "whsec_fake_present")

    class _FakeCheckout:
        def __init__(self, *a, **kw): pass
        async def handle_webhook(self, body, signature):
            raise RuntimeError("invalid signature")

    import sys
    import types
    mod_path = "emergentintegrations.payments.stripe.checkout"
    fake_mod = sys.modules.get(mod_path) or types.ModuleType(mod_path)
    fake_mod.StripeCheckout = _FakeCheckout
    sys.modules[mod_path] = fake_mod

    ac, _ = client
    r = await ac.post("/api/webhook/stripe", content=b'{"hi":"there"}')
    assert r.status_code == 400


async def test_stripe_webhook_returns_200_when_secret_absent(client, monkeypatch):
    """In dev (no secret) the endpoint accepts unsigned payloads but
    returns ``status: rejected`` with a dev_mode marker."""
    import billing
    monkeypatch.setattr(billing, "STRIPE_API_KEY", "sk_test_anything")
    monkeypatch.setattr(billing, "STRIPE_WEBHOOK_SECRET", "")

    class _FakeCheckout:
        def __init__(self, *a, **kw): pass
        async def handle_webhook(self, body, signature):
            raise RuntimeError("no signature")

    import sys
    import types
    mod_path = "emergentintegrations.payments.stripe.checkout"
    fake_mod = sys.modules.get(mod_path) or types.ModuleType(mod_path)
    fake_mod.StripeCheckout = _FakeCheckout
    sys.modules[mod_path] = fake_mod

    ac, _ = client
    r = await ac.post("/api/webhook/stripe", content=b'{"hi":"there"}')
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "rejected"
    assert body.get("dev_mode") is True


# ---------- Customer Portal ----------
async def test_customer_portal_returns_409_when_no_stripe_relationship(client):
    """Beta users (no Stripe customer_id) cannot use the Portal."""
    ac, _ = client
    r = await ac.post(
        "/api/billing/portal",
        json={"email": "beta-only@example.com", "return_url": "https://liveastrology.app/upgrade/manage"},
    )
    assert r.status_code == 409


# ---------- Day-60 review-ask dispatch ----------
async def test_review_requests_requires_admin(client):
    ac, _ = client
    r = await ac.post("/api/admin/premium/dispatch-review-requests")
    assert r.status_code == 401


async def test_review_requests_only_sends_to_60_day_claims(client, sent_emails):
    """Eligibility: created_at <= now-60d AND expires_at >= now+7d AND
    no existing review_requests row."""
    ac, mock_db = client
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)

    # Eligible: claimed 61 days ago, beta still valid for ~29 days
    await mock_db.beta_claims.insert_one({
        "email": "eligible@example.com",
        "name": "Eli",
        "claim_number": 1,
        "created_at": now - timedelta(days=61),
        "expires_at": now + timedelta(days=29),
    })
    # Too young: claimed 30 days ago
    await mock_db.beta_claims.insert_one({
        "email": "fresh@example.com",
        "name": "Fresh",
        "claim_number": 2,
        "created_at": now - timedelta(days=30),
        "expires_at": now + timedelta(days=60),
    })
    # Too late: only 3 days left on the beta — don't ask now, the
    # expiry email itself will be the nudge.
    await mock_db.beta_claims.insert_one({
        "email": "tooLate@example.com",
        "name": "Late",
        "claim_number": 3,
        "created_at": now - timedelta(days=88),
        "expires_at": now + timedelta(days=2),
    })

    r = await ac.post(
        "/api/admin/premium/dispatch-review-requests",
        headers={"Authorization": "Bearer test-admin-secret"},
        json={"dry_run": False},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "ok"
    assert body["eligible"] == 1
    assert body["sent_count"] == 1

    review_emails = [e for e in sent_emails if e["slug"] == "premium_review_ask"]
    assert len(review_emails) == 1
    assert review_emails[0]["to"] == "eligible@example.com"
    vars_ = review_emails[0]["vars"]
    assert vars_["name"] == "Eli"
    assert "trustpilot.com" in vars_["trustpilot_url"]
    assert "producthunt" in vars_["producthunt_url"]
    assert vars_["expires_at_human"]
    assert vars_["unsubscribe_url"].startswith("https://")


async def test_review_requests_is_idempotent_per_email(client, sent_emails):
    """Re-running the cron never resends to the same address."""
    ac, mock_db = client
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)

    await mock_db.beta_claims.insert_one({
        "email": "once@example.com",
        "name": "Once",
        "claim_number": 1,
        "created_at": now - timedelta(days=65),
        "expires_at": now + timedelta(days=25),
    })

    headers = {"Authorization": "Bearer test-admin-secret"}
    r1 = await ac.post("/api/admin/premium/dispatch-review-requests", headers=headers, json={"dry_run": False})
    assert r1.json()["sent_count"] == 1
    r2 = await ac.post("/api/admin/premium/dispatch-review-requests", headers=headers, json={"dry_run": False})
    body = r2.json()
    assert body["sent_count"] == 0
    assert body["skipped_existing"] == 1

    sent = [e for e in sent_emails if e["slug"] == "premium_review_ask"]
    assert len(sent) == 1


async def test_review_requests_dry_run_does_not_send(client, sent_emails):
    """dry_run=true counts eligibility but skips Resend + idempotency writes."""
    ac, mock_db = client
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)

    await mock_db.beta_claims.insert_one({
        "email": "dry@example.com",
        "name": "Dry",
        "claim_number": 1,
        "created_at": now - timedelta(days=70),
        "expires_at": now + timedelta(days=20),
    })

    r = await ac.post(
        "/api/admin/premium/dispatch-review-requests",
        headers={"Authorization": "Bearer test-admin-secret"},
        json={"dry_run": True},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["eligible"] == 1
    assert body["sent_count"] == 1
    assert body["dry_run"] is True

    # No real email was dispatched
    assert not any(e["slug"] == "premium_review_ask" for e in sent_emails)
    # And no idempotency row was written, so a subsequent real send still fires
    count = await mock_db.review_requests.count_documents({})
    assert count == 0


# ---------- RSS + Atom feeds ----------
LONG_FEED_CONTENT = ("Plain English sentence. " * 60).strip()


async def _seed_two_published_articles(ac):
    """Helper: create two published articles via the admin API."""
    headers = {"Authorization": "Bearer test-admin-secret"}
    await ac.post("/api/admin/articles", headers=headers, json={
        "title": "Big Three Explained",
        "excerpt": "What Sun, Moon and Rising actually mean.",
        "content": LONG_FEED_CONTENT,
        "author": "Live Astrology Editorial",
        "category": "Astrology Basics",
        "status": "published",
    })
    await ac.post("/api/admin/articles", headers=headers, json={
        "title": "Mercury Retrograde Survival Kit",
        "excerpt": "Plain-English guide to the three weeks of chaos.",
        "content": LONG_FEED_CONTENT,
        "author": "Live Astrology Editorial",
        "category": "Transits",
        "status": "published",
    })
    # And one draft — it must NOT appear in the feeds.
    await ac.post("/api/admin/articles", headers=headers, json={
        "title": "Secret Draft Post",
        "excerpt": "Should not be visible publicly.",
        "content": LONG_FEED_CONTENT,
        "author": "Editor",
        "category": "Drafts",
        "status": "draft",
    })


async def test_rss_feed_returns_valid_xml(client):
    ac, _ = client
    await _seed_two_published_articles(ac)

    r = await ac.get("/api/feed.xml")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/rss+xml")
    assert "max-age=900" in r.headers.get("cache-control", "")

    body = r.text
    # XML preamble + RSS root
    assert body.startswith('<?xml version="1.0"')
    assert '<rss version="2.0"' in body
    assert "<channel>" in body
    assert "<title>Live Astrology — Articles</title>" in body
    # Both published articles present, draft is excluded
    assert "Big Three Explained" in body
    assert "Mercury Retrograde Survival Kit" in body
    assert "Secret Draft Post" not in body
    # Items have canonical URLs and GUIDs
    assert "https://liveastrology.app/articles/big-three-explained" in body
    assert '<guid isPermaLink="true">' in body
    # Self-link advertised
    assert '<atom:link href="https://liveastrology.app/api/feed.xml"' in body

    # Parse with the stdlib to confirm well-formed XML
    import xml.etree.ElementTree as ET
    root = ET.fromstring(body)
    items = root.findall("./channel/item")
    assert len(items) == 2


async def test_atom_feed_returns_valid_xml(client):
    ac, _ = client
    await _seed_two_published_articles(ac)

    r = await ac.get("/api/atom.xml")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/atom+xml")

    body = r.text
    assert body.startswith('<?xml version="1.0"')
    assert 'xmlns="http://www.w3.org/2005/Atom"' in body
    # Both published articles present, draft excluded
    assert "Big Three Explained" in body
    assert "Mercury Retrograde Survival Kit" in body
    assert "Secret Draft Post" not in body
    # Self-link advertised
    assert 'href="https://liveastrology.app/api/atom.xml"' in body

    import xml.etree.ElementTree as ET
    root = ET.fromstring(body)
    ns = "{http://www.w3.org/2005/Atom}"
    entries = root.findall(f"./{ns}entry")
    assert len(entries) == 2
    # Each entry has the required elements
    for entry in entries:
        assert entry.find(f"./{ns}id") is not None
        assert entry.find(f"./{ns}updated") is not None
        assert entry.find(f"./{ns}link") is not None


async def test_feeds_handle_empty_articles_collection(client):
    ac, _ = client
    rss = await ac.get("/api/feed.xml")
    atom = await ac.get("/api/atom.xml")
    assert rss.status_code == 200
    assert atom.status_code == 200
    # Both must still be valid XML with no <item>/<entry>
    import xml.etree.ElementTree as ET
    rss_root = ET.fromstring(rss.text)
    atom_root = ET.fromstring(atom.text)
    assert rss_root.findall("./channel/item") == []
    ns = "{http://www.w3.org/2005/Atom}"
    assert atom_root.findall(f"./{ns}entry") == []


async def test_feeds_escape_xml_special_characters(client):
    """Titles or excerpts with <, >, & must not break the XML."""
    ac, _ = client
    headers = {"Authorization": "Bearer test-admin-secret"}
    await ac.post("/api/admin/articles", headers=headers, json={
        "title": "Sun & Moon — what's the difference?",
        "excerpt": "<script>alert(1)</script> — Plain-English answer.",
        "content": LONG_FEED_CONTENT,
        "author": "Editor",
        "category": "Basics",
        "status": "published",
    })

    rss = await ac.get("/api/feed.xml")
    atom = await ac.get("/api/atom.xml")

    # Must NOT contain unescaped angle brackets from the excerpt
    assert "<script>alert(1)</script>" not in rss.text
    assert "<script>alert(1)</script>" not in atom.text
    assert "&amp;" in rss.text  # the title's ampersand must be encoded
    assert "&lt;script&gt;" in rss.text

    # Both must still parse as valid XML
    import xml.etree.ElementTree as ET
    ET.fromstring(rss.text)
    ET.fromstring(atom.text)


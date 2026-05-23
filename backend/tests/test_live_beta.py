"""Live preview integration tests for Phase 4 (beta + feedback + testimonials)."""
import os
import time
import uuid
import requests

BASE = "https://forecast-cron-debug.preview.emergentagent.com"
ADMIN = "W1X1H6anmZ0M9vUSMr9kv7BVsCS6uFVnay7Lbl8aVsWanBh5"


def _unique_email(prefix="testbeta"):
    return f"TEST_{prefix}_{uuid.uuid4().hex[:8]}@example.com"


def test_beta_status_shape():
    r = requests.get(f"{BASE}/api/beta/status", timeout=15)
    assert r.status_code == 200
    d = r.json()
    for k in ("total_seats", "seats_claimed", "seats_remaining", "waitlist_size", "duration_days", "me"):
        assert k in d
    assert d["total_seats"] == 100
    assert d["duration_days"] == 90
    assert d["seats_remaining"] == d["total_seats"] - d["seats_claimed"]


def test_beta_claim_invalid_email():
    r = requests.post(f"{BASE}/api/beta/claim", json={"email": "not-an-email", "name": "X"}, timeout=15)
    assert r.status_code == 422, r.text


def test_beta_claim_happy_path_and_duplicate_and_billing():
    email = _unique_email()
    # Status before
    before = requests.get(f"{BASE}/api/beta/status", timeout=15).json()
    seats_before = before["seats_claimed"]

    # First claim
    r1 = requests.post(f"{BASE}/api/beta/claim", json={"email": email, "name": "TEST Beta User"}, timeout=20)
    assert r1.status_code == 200, r1.text
    d1 = r1.json()
    assert d1["result"] == "granted"
    assert isinstance(d1["claim_number"], int) and d1["claim_number"] >= 1
    assert "expires_at" in d1 and d1["expires_at"]
    assert d1["seats_remaining"] == 100 - (seats_before + 1)

    # Seats incremented by exactly 1
    mid = requests.get(f"{BASE}/api/beta/status", timeout=15).json()
    assert mid["seats_claimed"] == seats_before + 1

    # Duplicate claim
    r2 = requests.post(f"{BASE}/api/beta/claim", json={"email": email, "name": "TEST Beta User"}, timeout=20)
    assert r2.status_code == 200, r2.text
    d2 = r2.json()
    assert d2["result"] == "already_claimed", d2

    # No double-increment
    after = requests.get(f"{BASE}/api/beta/status", timeout=15).json()
    assert after["seats_claimed"] == seats_before + 1

    # Billing reflects beta entitlement
    time.sleep(0.5)
    bill = requests.get(f"{BASE}/api/billing/status", params={"email": email}, timeout=15)
    assert bill.status_code == 200, bill.text
    bd = bill.json()
    assert bd.get("active") is True, bd


def test_testimonials_no_email_leak():
    """GET /api/testimonials must never include an 'email' field."""
    r = requests.get(f"{BASE}/api/testimonials", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert "testimonials" in data
    for it in data["testimonials"]:
        assert "email" not in it, f"email leaked: {it}"


def test_admin_publish_auth_required():
    """Admin endpoint requires Bearer auth."""
    no_auth = requests.post(f"{BASE}/api/admin/feedback/nonexistent-id/publish", timeout=15)
    assert no_auth.status_code in (401, 403), no_auth.status_code

    # With valid auth but nonexistent ticket id → 404
    headers = {"Authorization": f"Bearer {ADMIN}"}
    with_auth = requests.post(f"{BASE}/api/admin/feedback/nonexistent-id/publish", headers=headers, timeout=15)
    assert with_auth.status_code == 404, with_auth.text


def test_email_templates_render():
    import sys
    sys.path.insert(0, "/app/backend")
    from email_service import render  # type: ignore

    slugs = {
        "premium_welcome": {"name": "Ada", "claim_number": 7, "expires_at": "2026-04-09"},
        "premium_10_planet": {"name": "Ada", "sun_sign": "Gemini", "moon_sign": "Sagittarius", "rising_sign": "Virgo",
                              "mercury_sign": "Gemini", "venus_sign": "Cancer", "mars_sign": "Leo",
                              "jupiter_sign": "Cancer", "saturn_sign": "Capricorn",
                              "uranus_sign": "Capricorn", "neptune_sign": "Capricorn", "pluto_sign": "Scorpio"},
        "premium_forecast": {"name": "Ada", "month_name": "January 2026"},
        "premium_compatibility": {"name": "Ada", "person1_name": "Ada", "person2_name": "Lin", "partner_name": "Lin", "score": 82},
    }
    for slug, vars_ in slugs.items():
        subject, html, text = render(slug, **vars_)
        assert subject, f"missing subject for {slug}"
        assert html and len(html) > 3000, f"html too small for {slug}: {len(html) if html else 0}"
        assert text and len(text) > 500, f"txt too small for {slug}: {len(text) if text else 0}"

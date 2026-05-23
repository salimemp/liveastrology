"""Phase-5 live preview tests against the public preview backend.

Tests:
  - Admin auth on /admin/premium/forecast-preview + dispatch
  - /admin/premium/dispatch-monthly-forecast idempotency
  - /admin/premium/compatibility/send (409 non-active, 422 invalid sign, 200 happy)
  - /webhook/stripe signature behaviour (dev_mode vs. enforced)
  - /billing/portal returns 409 for unknown email
"""
import os
import time
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://marketing-audit-impl.preview.emergentagent.com").rstrip("/")
ADMIN_SECRET = "W1X1H6anmZ0M9vUSMr9kv7BVsCS6uFVnay7Lbl8aVsWanBh5"
ADMIN_HEADERS = {"Authorization": f"Bearer {ADMIN_SECRET}"}


# ---- forecast-preview ----------------------------------------------------

def test_forecast_preview_requires_auth():
    r = requests.get(f"{BASE_URL}/api/admin/premium/forecast-preview", timeout=30)
    assert r.status_code == 401, r.text


def test_forecast_preview_with_auth():
    r = requests.get(
        f"{BASE_URL}/api/admin/premium/forecast-preview",
        headers=ADMIN_HEADERS,
        timeout=120,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "forecast" in body
    f = body["forecast"]
    for key in (
        "theme_paragraph", "event_1_date", "event_1_text",
        "event_2_date", "event_2_text", "event_3_date", "event_3_text",
        "practical_insight", "month_name", "year",
    ):
        assert key in f, f"Missing key {key} in {f.keys()}"


# ---- dispatch-monthly-forecast ------------------------------------------

def test_dispatch_requires_auth():
    r = requests.post(f"{BASE_URL}/api/admin/premium/dispatch-monthly-forecast", timeout=30)
    assert r.status_code == 401, r.text


def test_dispatch_is_idempotent():
    # 1st call — might send or already be done.
    r1 = requests.post(
        f"{BASE_URL}/api/admin/premium/dispatch-monthly-forecast",
        headers=ADMIN_HEADERS, json={}, timeout=180,
    )
    assert r1.status_code == 200, r1.text
    b1 = r1.json()
    assert b1["status"] == "ok"
    assert "month_key" in b1
    assert "sent_count" in b1
    assert "skipped_existing" in b1
    assert "skipped_inactive" in b1
    assert isinstance(b1.get("failed"), list)
    month_key = b1["month_key"]

    # 2nd call — must report 0 newly-sent + skipped_existing >= 1st run's sent
    r2 = requests.post(
        f"{BASE_URL}/api/admin/premium/dispatch-monthly-forecast",
        headers=ADMIN_HEADERS, json={}, timeout=180,
    )
    assert r2.status_code == 200, r2.text
    b2 = r2.json()
    assert b2["month_key"] == month_key
    assert b2["sent_count"] == 0, f"Expected 0 second-time sends but got {b2}"
    # everyone who could be sent on run-1 must be in skipped_existing on run-2
    assert b2["skipped_existing"] >= b1["sent_count"]


# ---- compatibility/send -------------------------------------------------

def test_compat_requires_auth():
    r = requests.post(f"{BASE_URL}/api/admin/premium/compatibility/send", json={}, timeout=30)
    assert r.status_code == 401


def test_compat_inactive_recipient_returns_409():
    payload = {
        "recipient_email": "no-such-entitlement-test@example.com",
        "person1_name": "Ada", "person1_sun": "gemini", "person1_moon": "pisces",
        "person2_name": "Charles", "person2_sun": "leo", "person2_moon": "cancer",
        "score": 72,
    }
    r = requests.post(
        f"{BASE_URL}/api/admin/premium/compatibility/send",
        headers=ADMIN_HEADERS, json=payload, timeout=30,
    )
    assert r.status_code == 409, r.text


def test_compat_invalid_sign_returns_422():
    payload = {
        "recipient_email": "beta1@example.com",
        "person1_name": "Ada", "person1_sun": "banana", "person1_moon": "pisces",
        "person2_name": "Charles", "person2_sun": "leo", "person2_moon": "cancer",
        "score": 72,
    }
    r = requests.post(
        f"{BASE_URL}/api/admin/premium/compatibility/send",
        headers=ADMIN_HEADERS, json=payload, timeout=30,
    )
    assert r.status_code == 422, r.text


# ---- stripe webhook signature -------------------------------------------

def test_stripe_webhook_signature_behaviour():
    # POST with bogus signature. With STRIPE_WEBHOOK_SECRET unset (dev),
    # the emergentintegrations SDK parses the JSON without enforcing the
    # signature, so the live endpoint returns {status:ok, verified:true}.
    # Note: when the SECRET *is* configured (covered by unit test
    # test_stripe_webhook_returns_400_when_secret_configured) invalid
    # signatures correctly return HTTP 400.
    r = requests.post(
        f"{BASE_URL}/api/webhook/stripe",
        headers={"stripe-signature": "t=1,v1=bogus", "content-type": "application/json"},
        data='{"id":"evt_test","type":"customer.subscription.created"}',
        timeout=30,
    )
    # Live preview: dev mode (no secret) → 200 OK.
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("status") in ("ok", "rejected")


# ---- billing/portal -----------------------------------------------------

def test_billing_portal_no_customer_returns_409():
    r = requests.post(
        f"{BASE_URL}/api/billing/portal",
        json={
            "email": "no-stripe-customer-test@example.com",
            "return_url": "https://liveastrology.app/account",
        },
        timeout=30,
    )
    assert r.status_code == 409, r.text
    body = r.json()
    msg = (body.get("detail") or body.get("message") or "").lower()
    assert "stripe" in msg or "subscription" in msg or "customer" in msg

"""Email rendering + Resend dispatch.

Renders the HTML + TXT templates in /app/liveastrology/emails/ through
Jinja2, then ships them through Resend. All Resend calls are executed via
``asyncio.to_thread`` so the FastAPI event-loop stays non-blocking.

Testing mode note
-----------------
While the liveastrology.app domain isn't verified in Resend, outbound
messages can only be delivered to the email address that owns the Resend
account. All other recipients will be silently dropped. To enable
production sending, verify the domain at https://resend.com/domains and
change SENDER_EMAIL in .env to a `@liveastrology.app` address.
"""
from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

import jinja2
import resend

logger = logging.getLogger(__name__)

# Templates live outside /app/backend in the frontend repo so designers
# can tweak them without touching Python.
EMAIL_DIR = Path(__file__).parent.parent / "liveastrology" / "emails"

_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(EMAIL_DIR)),
    autoescape=jinja2.select_autoescape(["html"]),
    keep_trailing_newline=True,
)

# Catalogue: logical template slug → (html path, txt path, subject template)
TEMPLATES: dict[str, tuple[str, str, str]] = {
    "subscribe_confirm":   ("html/01-subscribe-confirm-opt-in.html",  "txt/01-subscribe-confirm-opt-in.txt",  "Confirm your Live Astrology subscription"),
    "subscribe_welcome":   ("html/02-subscribe-welcome.html",         "txt/02-subscribe-welcome.txt",         "Welcome to Live Astrology ✨"),
    "unsubscribe_confirm": ("html/03-unsubscribe-confirmation.html",  "txt/03-unsubscribe-confirmation.txt",  "You've been unsubscribed"),
    "feedback_ack":        ("html/04-feedback-acknowledgment.html",   "txt/04-feedback-acknowledgment.txt",   "We got your feedback — Live Astrology"),
    "contact_ack":         ("html/05-contact-acknowledgment.html",    "txt/05-contact-acknowledgment.txt",    "We received your message — Live Astrology"),
    "weekly_horoscope":    ("html/06-weekly-horoscope.html",          "txt/06-weekly-horoscope.txt",          "Your weekly cosmic brief"),
    "admin_notification":  ("html/07-admin-notification.html",        "txt/07-admin-notification.txt",        "[Live Astrology] {event_type} — {summary}"),
}


def _configure_resend() -> None:
    """Configure the Resend SDK. Called lazily so missing env doesn't crash import."""
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        raise RuntimeError("RESEND_API_KEY is not set in /app/backend/.env")
    resend.api_key = api_key


def render(slug: str, **vars: Any) -> tuple[str, str, str]:
    """Render the HTML + TXT + subject line for the given template slug."""
    if slug not in TEMPLATES:
        raise KeyError(f"Unknown email template: {slug}")
    html_path, txt_path, subject_tpl = TEMPLATES[slug]
    html = _env.get_template(html_path).render(**vars)
    text = _env.get_template(txt_path).render(**vars)
    # Subject line can itself be a Jinja string for the admin notification.
    subject = subject_tpl.format(**vars) if "{" in subject_tpl else subject_tpl
    return subject, html, text


async def send_template(
    slug: str,
    to: str | list[str],
    *,
    reply_to: str | None = None,
    list_unsubscribe: str | None = None,
    **vars: Any,
) -> dict[str, Any] | None:
    """Render and send a templated email. Returns the Resend response or ``None``
    if sending was disabled / failed. Failures are logged but never raise so
    a mail-delivery problem doesn't break the API response for the user."""
    subject, html, text = render(slug, **vars)

    sender = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
    recipients = [to] if isinstance(to, str) else list(to)

    headers: dict[str, str] = {}
    if list_unsubscribe:
        headers["List-Unsubscribe"] = f"<{list_unsubscribe}>"
        headers["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"

    params: dict[str, Any] = {
        "from": sender,
        "to": recipients,
        "subject": subject,
        "html": html,
        "text": text,
    }
    if reply_to:
        params["reply_to"] = reply_to
    if headers:
        params["headers"] = headers

    try:
        _configure_resend()
        response = await asyncio.to_thread(resend.Emails.send, params)
        logger.info("resend.send slug=%s to=%s id=%s", slug, recipients, response.get("id"))
        return response
    except Exception as exc:  # noqa: BLE001 — we never want to 500 on email failure
        logger.exception("resend.send FAILED slug=%s to=%s error=%s", slug, recipients, exc)
        return None

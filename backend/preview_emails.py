"""Email preview CLI.

Usage:
    python -m preview_emails <slug> [output.html]
    python -m preview_emails --list

Renders an email template with realistic sample variables and writes the
result to ``output.html`` (default: ``/tmp/<slug>.html``) so you can open
it in a browser to QA the design without sending through Resend.

Run from /app/backend::

    cd /app/backend && python -m preview_emails subscribe_welcome
    cd /app/backend && python -m preview_emails weekly_horoscope ~/weekly.html
"""
from __future__ import annotations

import sys
import webbrowser
from pathlib import Path

import email_service
from content_generator import build_weekly_vars


SAMPLES: dict[str, dict[str, str]] = {
    "subscribe_confirm": {
        "first_name": "Alex",
        "email": "alex@example.com",
        "confirm_url": "https://liveastrology.app/api/subscribe/confirm?token=example-confirm-token",
        "unsubscribe_url": "https://liveastrology.app/api/unsubscribe?token=example-unsub-token",
    },
    "subscribe_welcome": {
        "first_name": "Alex",
        "email": "alex@example.com",
        "unsubscribe_url": "https://liveastrology.app/api/unsubscribe?token=example-unsub-token",
    },
    "unsubscribe_confirm": {
        "first_name": "Alex",
        "email": "alex@example.com",
    },
    "feedback_ack": {
        "first_name": "Alex",
        "email": "alex@example.com",
        "ticket_id": "FB-8X4A2C",
        "category": "Feature request",
        "rating_stars": "★★★★☆ (4/5)",
        "message_snippet": "Would love to see a transit calendar for the next 6 months. Right now I have to cross-check 3 sites. Would be so nice to have it all here!",
    },
    "contact_ack": {
        "first_name": "Alex",
        "email": "alex@example.com",
        "subject": "Partnership enquiry",
        "received_at": "2026-02-14 09:30 UTC",
        "message_snippet": "Hi — I run a wellness newsletter with 40k subscribers and would love to discuss a content collab...",
    },
    "admin_notification": {
        "event_type": "feedback",
        "summary": "Feature request from Alex",
        "user_display": "Alex Rivera",
        "user_email": "alex@example.com",
        "user_first_name": "Alex",
        "reference_id": "FB-8X4A2C",
        "payload": (
            "ticket_id   : FB-8X4A2C\n"
            "category    : Feature request\n"
            "rating      : ★★★★☆ (4/5)\n"
            "name        : Alex Rivera\n"
            "email       : alex@example.com\n\n"
            "message:\n"
            "Would love to see a transit calendar for the next 6 months..."
        ),
        "source": "/feedback",
        "source_path": "/api/feedback",
        "received_at": "2026-02-14 09:30 UTC",
        "ip": "203.0.113.42",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605 Safari/605",
        "reply_subject": "Re: your feedback (#FB-8X4A2C)",
    },
}


def _sample_vars(slug: str) -> dict[str, str]:
    if slug == "weekly_horoscope":
        return build_weekly_vars(
            first_name="Alex",
            unsubscribe_url="https://liveastrology.app/api/unsubscribe?token=example",
        )
    if slug not in SAMPLES:
        raise KeyError(slug)
    return SAMPLES[slug]


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "--list":
        for slug in email_service.TEMPLATES:
            print(f"  {slug}")
        return 0

    slug = argv[0]
    if slug not in email_service.TEMPLATES:
        print(f"Unknown template: {slug}")
        print("Known slugs:")
        for s in email_service.TEMPLATES:
            print(f"  {s}")
        return 2

    out = Path(argv[1]) if len(argv) > 1 else Path(f"/tmp/{slug}.html")
    out_txt = out.with_suffix(".txt")

    vars_ = _sample_vars(slug)
    subject, html, text = email_service.render(slug, **vars_)

    out.write_text(html, encoding="utf-8")
    out_txt.write_text(text, encoding="utf-8")

    print(f"Subject : {subject}")
    print(f"HTML    : {out}  ({len(html):,} bytes)")
    print(f"Text    : {out_txt}  ({len(text):,} bytes)")

    # Best-effort browser open — silent no-op on headless containers.
    try:
        webbrowser.open(f"file://{out.resolve()}")
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

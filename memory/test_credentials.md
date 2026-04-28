# Live Astrology — admin & integration credentials

> **Updated**: 2026-04-28 (session: Resend webhooks + Email Health card)

## Admin dashboard (Bearer auth)

The admin UI at `/admin` and all `/api/admin/*` HTTP endpoints are protected
by a shared-secret bearer token read from `ADMIN_SECRET` in `/app/backend/.env`.

- **URL**: `https://cosmic-admin-live.preview.emergentagent.com/admin`
- **Secret**: `W1X1H6anmZ0M9vUSMr9kv7BVsCS6uFVnay7Lbl8aVsWanBh5`

Example curl:

    curl -H "Authorization: Bearer W1X1H6anmZ0M9vUSMr9kv7BVsCS6uFVnay7Lbl8aVsWanBh5" \
         https://cosmic-admin-live.preview.emergentagent.com/api/admin/stats

This secret was rotated to a 48-char `secrets.token_urlsafe(36)` value on
2026-04-28. Rotate again before/after handing the project to a new owner
(`openssl rand -hex 32` or `python -c "import secrets; print(secrets.token_urlsafe(36))"`).

There is **no end-user authentication** in the app.

## Resend (transactional email)

- API key already set in `/app/backend/.env` (`RESEND_API_KEY`).
- Domain `liveastrology.app` is verified — sender is `hello@liveastrology.app`.
- **Webhook signing secret** (`RESEND_WEBHOOK_SECRET`): currently empty.
  - Configure at https://resend.com/webhooks → add endpoint
    `https://liveastrology.app/api/webhooks/resend`
    (or the preview URL above for staging),
    subscribe to `email.delivered`, `email.bounced`, `email.opened`,
    `email.clicked`, `email.complained`, copy the `whsec_…` value into
    `RESEND_WEBHOOK_SECRET`, and restart the backend. The Email Health
    card on the Admin Dashboard will flip to "Webhook configured".
  - While the secret is empty, the endpoint accepts unsigned payloads and
    logs a warning (so you can ingest test events from the Resend UI).

## Cloudflare Turnstile

- Site key (public, in frontend bundle): `0x4AAAAAADExRj14IvpGPMYD`
- Secret (in `/app/backend/.env` → `CF_TURNSTILE_SECRET`):
  `0x4AAAAAADExRnUFTnX-fhVqfeVZkrWfEKs`
- Test bypass: set `TURNSTILE_DISABLED=1` (already set in pytest fixtures).

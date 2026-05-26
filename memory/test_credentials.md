# Live Astrology — admin & integration credentials

> **Updated**: 2026-05-09 (session: progress bar + home blog previews + Consent Mode v2 + Articles CMS)

## Admin dashboard (Bearer auth)

The admin UI at `/admin` and all `/api/admin/*` HTTP endpoints are protected
by a shared-secret bearer token read from `ADMIN_SECRET` in `/app/backend/.env`.

- **URL**: `https://forecast-cron-debug.preview.emergentagent.com/admin`
- **Secret**: `W1X1H6anmZ0M9vUSMr9kv7BVsCS6uFVnay7Lbl8aVsWanBh5`

Example curl:

    curl -H "Authorization: Bearer W1X1H6anmZ0M9vUSMr9kv7BVsCS6uFVnay7Lbl8aVsWanBh5" \
         https://forecast-cron-debug.preview.emergentagent.com/api/admin/stats

This secret was rotated to a 48-char `secrets.token_urlsafe(36)` value on
2026-04-28. Rotate again before/after handing the project to a new owner
(`openssl rand -hex 32` or `python -c "import secrets; print(secrets.token_urlsafe(36))"`).

There is **no end-user authentication** in the app.

## Resend (transactional email)

- API key already set in `/app/backend/.env` (`RESEND_API_KEY`).
- Domain `liveastrology.app` is verified — sender is `hello@liveastrology.app`.
- **Webhook signing secret** (`RESEND_WEBHOOK_SECRET`): **configured** ✅
  - Endpoint registered at https://resend.com/webhooks →
    `https://liveastrology.app/api/webhooks/resend`,
    subscribed to `email.delivered`, `email.bounced`, `email.opened`,
    `email.clicked`, `email.complained`. Backend now rejects any unsigned
    or wrongly-signed payload with HTTP 401.

## Cloudflare Turnstile

- Site key (public, in frontend bundle): `0x4AAAAAADExRj14IvpGPMYD`
- Secret (in `/app/backend/.env` → `CF_TURNSTILE_SECRET`):
  `0x4AAAAAADExRnUFTnX-fhVqfeVZkrWfEKs`
- Test bypass: set `TURNSTILE_DISABLED=1` (already set in pytest fixtures).


## IndexNow (Bing / Yandex / Seznam / Naver instant indexing)

- Key (in `/app/backend/.env` → `INDEXNOW_KEY`): `4729c06b46ab6d08e42fea100b787b91`
- Verification file URL (the one IndexNow fetches): `https://liveastrology.app/4729c06b46ab6d08e42fea100b787b91.txt` (static file in `frontend/public/`, returns the key as plain text — the spec-conventional root location).
- Backup verification URL (also serves the key): `https://liveastrology.app/api/indexnow-key.txt`.
- Manual submit endpoint: `POST /api/admin/indexnow/submit` with `{"urls": [...]}` (bearer auth).
- Auto-pings: triggered on `POST /api/admin/articles` (when `status=published`) and on `PATCH` flipping draft → published. Each ping also includes `https://liveastrology.app/sitemap.xml` so Bing re-fetches the whole sitemap.
- Test bypass: set `INDEXNOW_DISABLED=1` (already set in pytest fixtures).
- `robots.txt` carries a discoverable `# IndexNow key:` comment so auditors can verify instant-indexing is live.

## Google Indexing API

- Service-account JSON: `/app/backend/secrets/google-indexing-credentials.json` (gitignored).
- Service-account email: `live-astrology@live-astrology-01.iam.gserviceaccount.com`
- Project ID: `live-astrology-01`
- Path env var: `GOOGLE_INDEXING_CREDENTIALS_FILE` (set in `/app/backend/.env`).
- **One-time manual setup required**: open [Search Console → liveastrology.app → Settings → Users and permissions](https://search.google.com/search-console/users) → **Add user** → paste `live-astrology@live-astrology-01.iam.gserviceaccount.com` → role **Owner** (delegated). Without this, every call returns HTTP 403 "Permission denied. Failed to verify the URL ownership."
- Manual submit endpoint: `POST /api/admin/google-indexing/submit` with `{"url": "https://…", "action": "URL_UPDATED" | "URL_DELETED"}` (bearer auth).
- Auto-pings: fire alongside IndexNow on article publish.
- Quotas: 200 URL notifications per day, 600/min (Google defaults).
- Test bypass: set `GOOGLE_INDEXING_DISABLED=1` (already set in pytest fixtures).

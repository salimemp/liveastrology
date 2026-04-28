# Live Astrology — Product Requirements & Delivery Log

> **Repo**: `/app/liveastrology` (React 18 + Vite + TS, symlinked as `/app/frontend`)
> **Backend**: `/app/backend` (FastAPI + MongoDB + Resend)
> **Preview**: https://transactional-mail-1.preview.emergentagent.com
> **Response language**: English only

---

## Original problem statement

A fork of a public GitHub repo (`salimemp/liveastrology`) — a React + Vite
astrology app that must be migrated, de-bugged, and hardened into a
production-grade SEO-optimised astrology calculator with real astronomical
math, SEO schemas, and transactional emails via Resend.

## User personas

1. **Astrology-curious visitors** — land on `/`, run a free birth chart with
   Sun / Moon / Rising / Mercury / Venus / Mars signs, explore synastry and
   love compatibility, opt-in to the weekly cosmic brief.
2. **Subscribers** — receive double opt-in confirmation → welcome email →
   weekly horoscopes, with one-click unsubscribe.
3. **Feedback senders** — fill the `/feedback` form; receive ack email with
   a ticket reference; team gets an internal notification.

## Core functional requirements

- 100% accurate ephemeris-driven calculations (`astronomy-engine`).
- Client-side SPA: no birth-data leaves the browser for astro math.
- Full Google-ready SEO: `FAQPage`, `BreadcrumbList`, `SoftwareApplication`,
  `Event`, `WebSite`, `AggregateRating` JSON-LD per route.
- Light + Dark cosmic theme with starfield backdrop.
- Production-grade transactional emails:
  - Double opt-in subscription (confirm → welcome).
  - Feedback & contact acknowledgments with ticket IDs.
  - Admin notifications to `notify@liveastrology.app`.
  - Plain-text fallback for every HTML template (multi-part MIME).

---

## Architecture

```
Client (Vite SPA)
│
│  fetch('/api/...')  — same-origin, K8s ingress routes /api/* → backend:8001
▼
FastAPI backend (Python 3.11)
├── server.py              # routes
├── email_service.py       # Jinja2 rendering + Resend async dispatch
├── .env                   # RESEND_API_KEY, SENDER_EMAIL, NOTIFY_EMAIL, MONGO_URL, DB_NAME, APP_ORIGIN
└── /app/liveastrology/emails/
    ├── html/01..07*.html  # Outlook-safe, inline-CSS, 600px table layout
    ├── txt/01..07*.txt    # plain-text fallbacks
    └── README.md          # catalogue + placeholder reference
│
▼
MongoDB (`liveastrology` DB)
├── subscribers    { email, first_name, status: pending|confirmed|unsubscribed, confirm_token, unsub_token, source, timestamps }
├── feedback       { ticket_id, name, email, rating, category, message, created_at }
└── contacts       { ticket_id, name, email, subject, message, created_at }
│
▼
Resend (transactional email provider)
```

## API surface

| Method | Path                            | Purpose | Templates fired |
|--------|---------------------------------|---------|-----------------|
| GET    | `/api/health`                   | Liveness | — |
| POST   | `/api/subscribe`                | Start double opt-in | 01 (user) + 07 (admin) |
| GET    | `/api/subscribe/confirm?token=` | Complete opt-in → 302 redirect `/?subscribed=1` | 02 (user) |
| POST   | `/api/unsubscribe`              | Unsubscribe by email or token | 03 (user) |
| GET    | `/api/unsubscribe?token=`       | One-click (for `List-Unsubscribe` header) | 03 (user) |
| POST   | `/api/feedback`                 | `/feedback` page | 04 (user) + 07 (admin) |
| POST   | `/api/contact`                  | (Future) contact form | 05 (user) + 07 (admin) |

All POST endpoints return `202 Accepted` on success. Validation errors
return 422 with Pydantic detail. Resend delivery failures are logged but
never surface to the user (the API always responds 202).

---

## Implementation log

### 2026-02-14 · Session 2 · Transactional email backend + Resend
- ✅ Finished email templates 06 (Weekly Horoscope) and 07 (Admin Notification)
- ✅ Added plain-text fallbacks for all 7 templates (`/app/liveastrology/emails/txt/`)
- ✅ Wrote `/app/liveastrology/emails/README.md` (catalogue, placeholder reference, QA checklist, Resend testing-mode notes)
- ✅ Real FastAPI backend replacing stub:
  - `POST /api/subscribe` with double opt-in
  - `GET /api/subscribe/confirm` 302 redirect
  - `POST|GET /api/unsubscribe` (Gmail/Yahoo one-click safe)
  - `POST /api/feedback` with ticket IDs (`FB-XXXXXX`)
  - `POST /api/contact` with ticket IDs (`CT-XXXXXX`)
- ✅ Resend async dispatch via `asyncio.to_thread(resend.Emails.send, ...)`
- ✅ Jinja2 template rendering from `emails/` with autoescape
- ✅ MongoDB persistence (`subscribers`, `feedback`, `contacts`)
- ✅ `List-Unsubscribe` + `List-Unsubscribe-Post` headers on subscriber emails
- ✅ New frontend API client at `/app/liveastrology/src/lib/api.ts` (relative `/api` paths, no CORS)
- ✅ Wired `FeedbackPage`, `Footer` newsletter, `BlogList` newsletter from `mailto:` → real backend POSTs with loading and error states
- ✅ E2E verified via preview URL — `/api/feedback` returned 202 + ticket `#FB-E3K8OF` rendered in UI
- ✅ E2E verified subscribe → confirm (302 → `/?subscribed=1`) → unsubscribe flow

### 2026-02-13 · Session 1 (prior fork)
- Migrated repo, real ephemeris calculations, dark-theme visibility fixes.
- Nominatim geocoder, `tz-lookup`, real routing, dynamic SEO + JSON-LD.
- `/feedback` page + `mailto:` newsletter (now superseded by backend).
- Created `_base.html` + templates 01-05.

---

## Known constraints

- **Resend testing mode** — the provided API key can only deliver to the
  account owner's email (`salimmakrana@gmail.com`). Emails to any other
  address are rejected by Resend with a clear error and silently logged;
  the API response remains `202 Accepted` so the user experience is
  uninterrupted. **To unlock production delivery**, verify the
  `liveastrology.app` domain at https://resend.com/domains and change
  `SENDER_EMAIL` in `/app/backend/.env` to e.g. `hello@liveastrology.app`.
- **Frontend serve mode** — supervisor runs `yarn build && serve -s dist`
  (NOT `vite dev`) because the Vite HMR websocket is incompatible with
  the Cloudflare ingress. Code changes therefore require `yarn build`
  (handled automatically by `yarn start`).

## Roadmap

### P0 (shipped)
- ✅ Transactional email templates (7 HTML + 7 TXT + README).
- ✅ Real backend with Resend + MongoDB.
- ✅ Frontend forms wired to backend.

### P1 — Next
- Multi-language support (Phase 0): `react-i18next` + English baseline JSON.
- Weekly horoscope cron: generate content with current transits,
  send template 06 to all confirmed subscribers.
- Verify `liveastrology.app` domain in Resend → enable production sends.
- Backend test suite at `/app/backend/tests/` (pytest + AsyncClient).

### P2 — Backlog
- Houses + aspects calculators.
- `/contact` page with form (endpoint already live at `/api/contact`).
- Admin dashboard (view subscribers, feedback queue, opt-in funnel).
- Abuse protection: per-IP rate limiting on `/api/subscribe` & `/api/feedback`.
- Expand Resend-rendering to an offline preview CLI
  (`python -m backend.preview_emails <slug>` → opens browser).

## Test credentials

No user authentication in the app. Backend testing uses:
- **Resend-deliverable inbox**: `salimmakrana@gmail.com` (testing-mode only).
- **Admin notification recipient**: `notify@liveastrology.app` (configured in `.env`, will start delivering once domain is verified).

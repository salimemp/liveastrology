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

### 2026-02-14 · Session 2c · Real ephemeris + i18n full + admin UI + contact
- ✅ **Real astronomical ephemeris in weekly content**: swapped canned vars for `astronomy-engine` Python calls in `content_generator.py`. `build_weekly_vars()` now computes live Sun/Moon/Mercury/Venus/Mars signs from the ecliptic longitude of each body, plus the Moon's sign progression across the whole week (~6-hour resolution). Falls back to deterministic dummy signs if `astronomy-engine` is absent, so tests still run on minimal environments.
- ✅ **i18n expansion** — full 3-locale set:
  - `en.json` + **`es.json` (Spanish)** + **`hi.json` (Hindi)** covering nav, hero, features, faq, feedback page, contact page, footer newsletter, and common strings.
  - `<LanguageSwitcher>` mounted in the navbar (hidden on mobile for now).
  - Migrated to `useTranslation()`: navigation labels, hero title/subtitle/CTA, FAQ heading, `FeedbackPage` (title/tagline/intro/thank-you/buttons), `ContactPage` (title/intro/submit), `Footer` newsletter (title/body/placeholder/button/success).
  - Live-tested switching EN → ES → HI on the preview: `"Explore Free Astrology Charts"` → `"Descubre tu Carta Astral Gratis"` → `"मुफ्त ज्योतिष चार्ट बनाएँ"`.
- ✅ **Contact page wired to backend** — `/app/liveastrology/src/components/ContactPage.tsx` now POSTs `{name,email,subject,message}` to `/api/contact`, renders the returned `CT-XXXXXX` ticket ID in the success card, handles validation & errors with loading state. Live-verified: HTTP 202 + ticket `#CT-KGXIYN`.
- ✅ **Admin dashboard** at `/admin` — `AdminDashboard.tsx`:
  - Bearer-secret password gate (state-only, never localStorage).
  - Live stats cards: confirmed / pending / unsubscribed / total subscribers, feedback count, contacts count, weekly dispatches count.
  - "Send weekly horoscope now" button (calls `POST /api/admin/dispatch-weekly`).
  - Refresh-stats button.
  - `robots: noindex, nofollow` via new `useSeo({ noIndex: true })` flag.
- ✅ Extended `PageSeo` interface + `useSeo` with `noIndex` option.
- ✅ Live smoke-tested end-to-end on preview: EN/ES/HI language switch, admin login with correct secret, admin dispatch trigger, contact form 202 with ticket ID, pytest 15/15 green.

### 2026-02-14 · Session 2b · Scheduler, rate limits, i18n Phase 0, tests, preview CLI
- ✅ **i18n Phase 0**: `react-i18next` + `i18next-browser-languagedetector` installed; `/src/i18n/index.ts` init module; `/src/i18n/locales/en.json` baseline JSON; language detection with localStorage cache under key `liveastrology:lang`; `<LanguageSwitcher>` component (auto-hides while only one locale registered); nav links + hero title + hero subtitle + CTA + FAQ heading migrated to `useTranslation()`.
- ✅ **Weekly horoscope cron**:
  - `/app/backend/content_generator.py` — deterministic weekly-vars builder (Sun sign lookup, rotating top-3 signs, 6 canned rituals, ISO-week stable content).
  - `/app/backend/scheduler.py` — APScheduler cron running **every Sunday 18:00 UTC** + manual trigger.
  - `POST /api/admin/dispatch-weekly` + `GET /api/admin/stats` (both Bearer-protected).
  - Dispatch history recorded in `db.weekly_dispatches`.
- ✅ **Pytest suite** at `/app/backend/tests/`: 15 tests covering health, subscribe → confirm → welcome, unsubscribe, feedback (with/without email), contact, validation (422), admin auth (401/200), admin weekly dispatch fan-out, and rate-limit enforcement (429 on 6th rapid subscribe). Uses `mongomock-motor` + patched `email_service.send_template` so no Resend or Mongo call leaks into CI.
- ✅ **Per-IP rate limiting** via slowapi: 5/min on `/api/subscribe`, 3/min on `/api/feedback` & `/api/contact`, 120/min global fallback. Custom 429 JSON response. Live-verified on preview: 5 × 202 then 6th → 429.
- ✅ **Email preview CLI** (`python -m preview_emails <slug> [output.html]`) — renders any of the 7 templates with realistic sample vars (weekly_horoscope uses the real generator); writes HTML + TXT side-by-side for browser QA. `--list` enumerates available slugs.
- ✅ Fixed slowapi + `from __future__ import annotations` collision (removed the future import + explicit `Body(...)` declarations).
- ✅ `/app/memory/test_credentials.md` populated with admin Bearer secret.

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
- Houses + aspects calculators (backend model + frontend display).
- Extend i18n to remaining pages (Terms, Privacy, About, Refund, Blog posts) — JSON infra is ready; it's just wiring.
- Verify `liveastrology.app` domain in Resend → swap `SENDER_EMAIL` in `.env` → production delivery unlocked.

### P2 — Backlog
- Cloudflare Turnstile on `/api/subscribe` + `/api/feedback` (needs site key + secret key from user).
- Redis-backed slowapi for multi-replica rate limiting (current: single-pod in-memory).
- Admin dashboard pagination: list recent subscribers / feedback / contacts (currently just counts).
- Weekly-brief editorial layer: human narrative on top of the ephemeris-derived transits.

## Test credentials

No user authentication in the app. Backend testing uses:
- **Resend-deliverable inbox**: `salimmakrana@gmail.com` (testing-mode only).
- **Admin notification recipient**: `notify@liveastrology.app` (configured in `.env`, will start delivering once domain is verified).

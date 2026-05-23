# Live Astrology — Product Requirements & Delivery Log

> **Repo**: `/app/liveastrology` (React 18 + Vite + TS, symlinked as `/app/frontend`)
> **Backend**: `/app/backend` (FastAPI + MongoDB + Resend)
> **Preview**: https://forecast-cron-debug.preview.emergentagent.com
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

### 2026-02-14 · Session 2m · Day-60 review-ask cron + workflow hardening
- ✅ **Day-60 review-ask cron** — new `/app/backend/review_requests.py` finds beta claimants whose `created_at <= now - 60d` AND `expires_at >= now + 7d`, sends a Trustpilot + Product Hunt review request via the new `premium_review_ask` template (`12-day-60-review-request.html/.txt`), and records the dispatch in `review_requests` (idempotent — one email per address, ever). Admin endpoint `POST /api/admin/premium/dispatch-review-requests` with optional `dry_run`. Daily GitHub Action `/app/.github/workflows/day-60-review-request.yml` (10:00 UTC) calls it.
- ✅ **GitHub Actions workflow hardening** — patched `monthly-forecast.yml` to use the same `mktemp + %{http_code} + cat body` pattern as `weekly-horoscope.yml` so failures surface the HTTP code and response body in the Actions log (was silently exiting 22 on `curl -fsS`). Same pattern applied to the new day-60 workflow. Includes a hint that 404s mean production is missing the latest endpoint and needs a redeploy.
- ✅ Test suite: **81 unit tests green** (77 pure unit + 4 new day-60 tests covering auth, eligibility window, idempotency, dry-run).
- 🔁 Live verification against preview: `POST /api/admin/premium/dispatch-review-requests` (dry-run) returns `{eligible:0, sent_count:0, status:ok}`; unauth requests return 401.



### 2026-05-23 · Session 2l · Premium cron + admin compatibility flow + Stripe hardening
- ✅ **Monthly forecast dispatch** — new `forecast.py` module generates the month's transit themes via Claude Sonnet 4.5 (cached per `month_key` in `forecast_dispatches`) and ships the rendered `premium_forecast` email to every active entitlement. Per-email receipts in `forecast_recipients` guarantee at-most-once delivery per month. Admin endpoints: `POST /api/admin/premium/dispatch-monthly-forecast` (with `force` flag) and `GET /api/admin/premium/forecast-preview`. Inactive/expired entitlements are skipped.
- ✅ **GitHub Actions monthly cron** — new `/app/.github/workflows/monthly-forecast.yml` (`'0 9 1 * *'`, 09:00 UTC on the 1st) calls the admin endpoint with `set -euo pipefail` + jq parsing. Requires `LIVEASTROLOGY_URL` + `LIVEASTROLOGY_ADMIN_SECRET` GitHub secrets.
- ✅ **Request-driven Premium compatibility** — new `compatibility_reports.py` generates 6 paragraphs (headline / Sun×Sun / Moon×Moon / Venus×Mars / composite / work) via Claude Sonnet 4.5. Admin endpoint `POST /api/admin/premium/compatibility/send` validates the recipient has an active entitlement (409 otherwise), renders the existing `premium_compatibility` template via Resend, persists an audit row.
- ✅ **Premium admin tab** — new `<PremiumAdmin>` component in the admin dashboard (forecast Preview / Dispatch / Force-regenerate; compatibility form with sun/moon dropdowns + 0-100 score slider).
- ✅ **Stripe webhook signature enforcement** — production-critical: returns **HTTP 400** when `STRIPE_WEBHOOK_SECRET` is configured and signature fails verification. Dev-mode: returns HTTP 200 with `{status:rejected, dev_mode:true}` when the secret is absent AND the `Stripe-Signature` header is missing or malformed.
- ✅ **Stripe Customer Portal + Subscription scaffolding** — new endpoint `POST /api/billing/portal` and env knobs `STRIPE_SUBSCRIPTION_MODE`, `STRIPE_PRICE_MONTHLY`, `STRIPE_PRICE_YEARLY` ready for the post-beta switch. Beta-only users get 409 (no Stripe relationship to manage).
- ✅ Test suite: **88 tests green** (73 unit + 6 live-beta + 9 phase-5 live). Testing agent: 100% backend + 100% frontend, all acceptance criteria pass.

### 2026-05-23 · Session 2k · Beta launch + Premium fulfilment + categorised feedback + testimonials
- ✅ **Beta launch for first 100 users** — new `beta.py` module + endpoints `GET /api/beta/status` and `POST /api/beta/claim`. Stripe payments disabled in the UI for the beta phase; `<BetaClaimCard>` grants free 90-day Premium with idempotent per-email lookup and waitlist fallback at the cap.
- ✅ **4 Resend transactional templates** matching site logo + voice: `08-premium-welcome`, `09-premium-10-planet-report`, `10-premium-monthly-forecast`, `11-premium-compatibility`. Welcome + 10-planet fire automatically on beta grant.
- ✅ **Categorised feedback** (`/feedback`) — 4-axis ratings + opt-in `publish_consent`; explicit message on the form: *"By ticking this box you consent to your review and first name being displayed on liveastrology.app and inside the app."* Admin must still flip `published=true`.
- ✅ **TestimonialsStrip** — admin-approved testimonials on the homepage (hides when empty); `/api/testimonials` strictly excludes the email field.
- ✅ **PNG icon fallbacks** for iOS PWA A2HS.


### 2026-05-22 · Session 2j · Marketing audit — Phase 3 (PWA, GEO landings, Stripe Freemium)
- ✅ **Stripe Freemium** — email-based subscription lookup (no full auth system per user choice 1c). New `billing.py` module with server-side fixed packages (`monthly` $4.99/30d, `yearly` $39/365d). Endpoints: `GET /api/billing/packages`, `POST /api/billing/checkout`, `GET /api/billing/checkout/status/{id}`, `GET /api/billing/status?email=`, `POST /api/webhook/stripe`. Two new collections: `payment_transactions` (one row per Checkout session, idempotent via `last_session_id`) and `entitlements` (one row per email with `expires_at`).
- ✅ **Frontend `/upgrade`, `/upgrade/success`, `/upgrade/manage`** — plan selector with "Save 35%" badge on yearly, email field, Stripe redirect, polling success page (6 attempts × 2s), email-lookup status page. Premium feature list: full 10-planet chart, monthly forecast emails, premium compatibility report, priority AI interpretation, cancel anytime.
- ✅ **PWA** — manifest.webmanifest, sw.js (stale-while-revalidate cache for app shell, network-only for `/api/*`), icon-192.svg + icon-512.svg, `<link rel="manifest">` in index.html, `<PwaInstallPrompt>` component (registers SW + non-intrusive bottom-left install banner with localStorage dismissal). Apple meta tags already present.
- ✅ **3 GEO landing pages** — `/es/carta-natal` (Spanish), `/pt/mapa-astral` (Portuguese), `/hi/janam-kundali` (Hindi). Reusable `<GeoLandingPage>` driven by `lib/geoPages.ts` configs. Each page: localised hero + Big-Three feature cards + promises strip + 4-paragraph long-form intro + 3 FAQ entries (also wired into FAQPage JSON-LD) + dual CTA → `/birth-chart`. `<html lang>` updated per route.
- ✅ Test suite grew to **56 tests** (was 50) — 6 new billing tests (packages, status-unknown, checkout-validation, checkout-creates-pending-row, checkout-grants-entitlement-on-paid, idempotent-double-poll). All green.
- ✅ Testing agent verification: 100% backend + 100% frontend, all 18 acceptance criteria pass, zero issues. Two minor follow-ups flagged for future hardening (see Roadmap).

### 2026-05-20 · Session 2i · Marketing audit — Phase 2 (SEO content, VS/Alternatives pages, HowTo schema, synastry share card)
- ✅ **5 long-form SEO articles** seeded into the Articles CMS via new `POST /api/admin/seed-seo-articles` endpoint. Each article is 1,000+ words (1118–1547), targets a high-intent search query, and contains internal links to `/birth-chart` and `/synastry`:
  - `what-does-moon-in-scorpio-mean-a-plain-english-guide` (1202w)
  - `sun-sign-vs-moon-sign-vs-rising-sign-which-one-actually-matters` (1217w)
  - `free-birth-chart-calculator-no-signup-no-subscription-no-tricks` (1118w)
  - `how-to-read-your-birth-chart-for-the-first-time` (1547w)
  - `what-is-a-birth-chart-the-complete-beginner-s-guide` (1416w)
- ✅ Article payloads live in `/app/backend/seo_articles.py`. Seed endpoint is idempotent by default, supports `?force=true` to overwrite existing slugs. New "Seed SEO articles" button added to Admin → Articles tab.
- ✅ **VS / Alternatives landing pages** — 3 SEO-focused comparison pages with FAQ + JSON-LD: `/vs/nebula`, `/vs/co-star`, `/free-no-signup`. Reusable `<VsPage>` component takes a config (hero, comparison table, FAQ, verdict). 6 JSON-LD scripts per page (Organization, WebSite, SoftwareApplication, BreadcrumbList, FAQPage, WebPage). All carry data-testids `vs-{tag}-cta-{top,bottom}`.
- ✅ **`HowTo` JSON-LD** added on all calculator pages: `/birth-chart` (5 steps) and `/sign-calculators/{sun,moon,rising,mercury,venus,mars}` (4 steps each). New `howToSchema()` builder in `lib/seo.ts`. `Article`/`BlogPosting` schema already existed on `/blog/:id`.
- ✅ **Synastry social share** — new `<SynastryShareCard>` (gradient pink→teal, both names + signs + animated compatibility ring) rendered above the "Calculate Another Pairing" CTA on `/synastry` results. Native-share button (Web Share API) + Copy button with copy-to-clipboard fallback. data-testids `synastry-share-{card,native-btn,copy-btn,section}`.
- ✅ Test suite grew to **50 tests** (was 46) — 4 new tests covering the seed-seo-articles endpoint (insert, idempotency, force-update, auth). All green.
- ✅ Testing agent verification: 100% backend, 100% frontend, zero issues.

### 2026-05-20 · Session 2h · Marketing audit — Phase 1 (AI interpretation, email capture, trust strip, share card, hero rewrite)
- ✅ **AI plain‑English chart interpretation** — new `POST /api/interpret` endpoint generates a 3‑paragraph reading (one per Sun/Moon/Rising) using **Claude Sonnet 4.5** (`anthropic/claude-sonnet-4-5-20250929`) via the Emergent universal key + `emergentintegrations`. Responses are cached in `db.interpretation_cache` by `(sun, moon, rising)` tuple so repeat lookups are free and instant (~0.2s vs ~13.5s cold). Tolerant JSON parser handles fenced/unfenced responses. New `interpretation.py` module isolates the LLM call.
- ✅ **Frontend `<AiInterpretation>`** renders inside `ResultsDisplay` with a spinner while loading, per‑placement glass cards, accent‑coloured glyphs (Sun/Moon/Compass icons), and a "Reading generated by AI from your real birth-chart data" footnote.
- ✅ **Post‑calc email capture** — new `<PostChartEmailCapture>` reuses the existing `/api/subscribe` double‑opt‑in flow with `source=post-chart-capture`. Renders Turnstile widget inline, validates email format client‑side, surfaces backend errors inline, shows a "Check your inbox" success state. Pre‑existing flag `TURNSTILE_DISABLED=0` is respected.
- ✅ **Trust strip on `/`** — new `<TrustStrip>` shows a live "X charts calculated today" counter (backed by new `GET /api/charts-today` endpoint with a deterministic day‑of‑year baseline so the number is always meaningful) + the three audit‑recommended promises (No credit card / No signup / No surprise charges).
- ✅ **Shareable result card** — new `<ShareableResultCard>` renders a 1200×630 Open‑Graph friendly visual with the user's three signs and "LIVE ASTROLOGY" branding. Paired with header Copy/Share buttons (Web Share API with clipboard fallback).
- ✅ **Hero rewrite** — homepage `<HeroSection>` and i18n keys updated in `en/es/hi`:
  - EN: "Free Birth Chart — Sun, Moon & Rising, Explained" / "Get your Sun, Moon and Rising sign in 30 seconds — and a plain-English reading of what each one actually means…"
- ✅ **Bonus fix** — `ElementBreakdown` / Modality chart was double‑normalising the modality balance (showed `1100%`, `2233%`). `Charts.tsx` now uses the percentage directly; `getModalityInterpretation` translates back to a 0/1/2/3 count so the narrative text still works.
- ✅ Test suite grew to **46 tests** (was 42) — 4 new tests covering `/api/interpret` (validation, cached path, runtime‑error surfacing as 503) and `/api/charts-today`. All green.

### 2026-04-28 · Session 2g · Resend webhooks + Email Health dashboard + production cutover
- ✅ **`POST /api/webhooks/resend`** — ingests Resend deliverability events (`email.sent` / `delivered` / `bounced` / `opened` / `clicked` / `complained` / `delivery_delayed`), verifies Svix signature when `RESEND_WEBHOOK_SECRET` is set, and persists each event in `db.email_events` for full auditability. When the secret is empty the endpoint accepts unsigned payloads with a logged warning so the Resend "Send test event" button works during onboarding.
- ✅ **`GET /api/admin/stats`** extended with an `email_health` block: `sent / delivered / bounced / opened / clicked / complained` counts, computed `bounce_rate_pct` and `open_rate_pct`, the most recent event timestamp + type, and a `webhook_configured` flag (true once the signing secret is in `.env`).
- ✅ **Email Health card** on the Admin Dashboard — 6 metric tiles with traffic-light coloring (open rate green ≥25%, amber ≥10%, grey otherwise; bounce rate green <2%, amber 2-5%, red ≥5%), live "Webhook configured" / "Webhook secret missing" badge, plus bounce-rate / open-rate / last-event line. Live-verified on preview after seeding via `POST /api/webhooks/resend` (1 delivered event → card updated instantly).
- ✅ **Production env cutover**:
  - `SENDER_EMAIL=Live Astrology <hello@liveastrology.app>` — domain is verified on Resend.
  - `ADMIN_SECRET` rotated to a 48-char `secrets.token_urlsafe(36)` value (also recorded in `/app/memory/test_credentials.md`).
  - `RESEND_WEBHOOK_SECRET=` slot added to `.env` (paste the `whsec_…` value from https://resend.com/webhooks → endpoint).
- ✅ Test suite grew to **35 tests** (was 30): `test_resend_webhook_unsigned_accepted_in_dev`, `test_resend_webhook_records_each_event_type`, `test_admin_stats_includes_email_health`, `test_resend_webhook_rejects_invalid_signature_when_secret_set`, `test_resend_webhook_accepts_valid_svix_signature` (real svix sign+verify round-trip). All passing.

### 2026-02-14 · Session 2f · Jupiter + Saturn, static-page i18n, admin subscribers, Redis-ready limiter, external cron
- ✅ **Jupiter + Saturn** in Houses + Aspects:
  - Introduced `ChartPlanetName = PlanetName | 'jupiter' | 'saturn'` in `src/lib/astrology.ts` (keeps `PlanetName` narrow for the existing per-planet calculator tool that depends on curated content records).
  - `calculateHousesAndAspects()` now computes 7 planetary positions + up to 21 aspect pairs per chart.
  - Glyphs ♃ ♄ + labels added to `HousesAndAspects.tsx`; grid reflows to 7 columns on wide screens.
- ✅ **Static pages wired to i18n** — TermsOfService / PrivacyPolicy / AboutUs / RefundPolicy titles + intros + back-button labels now pull from `pages.*` + `common.back_to_home` keys. Live-verified in Hindi: navbar + privacy page both render correctly (`गोपनीयता नीति` title, Hindi intro).
- ✅ **Admin — subscribers list + per-subscriber actions**:
  - New `GET /api/admin/subscribers?status=all|pending|confirmed|unsubscribed&limit=&skip=` (tokens stripped from projection for safety).
  - New `POST /api/admin/subscribers/{email}/actions` with actions: `force_unsubscribe`, `delete`, `resend_confirm` (blocks re-send if already confirmed → 400).
  - New "Subscribers" tab in the admin UI with a table view, status pills, and per-row action buttons (`Resend confirm` for pending only, `Unsubscribe`, `Delete` with browser confirm prompt).
  - 6 new tests covering list, all 3 actions, 400/404/401 error paths.
- ✅ **Redis-ready rate limiter** — `slowapi.Limiter` now accepts `storage_uri=os.environ.get("REDIS_URL") or "memory://"`. Drop a `REDIS_URL` into `.env` the moment you scale beyond one pod — zero other code changes required.
- ✅ **External GitHub-Actions cron** — shipped `/app/.github/workflows/weekly-horoscope.yml` that fires every Sunday 18:00 UTC, calls `POST /api/admin/dispatch-weekly` with the admin secret, and fails loudly if the HTTP code isn't 200. Pairs with `ENABLE_SCHEDULER=0` in `.env` to prevent double-fire.
- ✅ Test suite grew to **30 tests** (was 24). All passing.

### 2026-02-14 · Session 2e · Houses + Aspects, Admin CSV, mark-resolved, pagination
- ✅ **Houses + Aspects** (frontend-only, uses existing `astronomy-engine` JS build):
  - New `calculateRisingDegree()` + `calculateHousesAndAspects()` in `src/lib/astrology.ts`.
  - **Whole-sign house system** (Ascendant's sign = House 1; each house exactly one zodiac sign). Chosen over Placidus for polar-latitude safety + simplicity.
  - **5 major aspects** (conjunction, sextile, square, trine, opposition) with astrologically-standard orbs (8°/4°/6°/8°/8°).
  - `AstrologyResult` type extended with `houses`, `planets`, `aspects`.
  - New `HousesAndAspects.tsx` component — 3 sections: planetary positions, 12 houses with themes + activated-planet badges, aspects with glyphs + orb + harmonious/challenging colour-coding.
  - Live-tested with Ada Lovelace's birth data (1990-06-15 14:30 London): 5 planets + 12 houses + Moon sextile Venus aspect all rendered correctly.
- ✅ **Admin subscribers CSV export** — `GET /api/admin/subscribers.csv?status=confirmed|all` returns `text/csv` with `Content-Disposition: attachment` + `X-Subscriber-Count` header. "Download subscribers CSV" button in the admin actions panel, produces a dated filename.
- ✅ **Admin mark-resolved** — `PATCH /api/admin/{feedback,contacts}/{ticket_id}` toggles a `resolved` boolean. Queue items show a line-through title + "resolved" badge when closed; **per-item "Mark resolved" button** flips state in one click. Live-verified on preview.
- ✅ **Admin queue pagination + "show open only" toggle** — both `GET /api/admin/feedback` and `/contacts` now accept `skip`, `limit` (max 100), and `only_open=true`. Response includes `total` + `skip` + `limit` for client pagination. Frontend ships a "Show open only" checkbox above each queue.
- ✅ **i18n extended to static pages** — Terms / Privacy / About / Refund titles & intros added as keys in all 3 locales (`en` / `es` / `hi`). JSON infra is ready; pages that want to adopt these keys just need a `useTranslation()` import and `{t('pages.privacy.title')}`.
- ✅ **`/app/docs/DEPLOYMENT.md`** — comprehensive production cutover guide covering: Resend domain verification (SPF/DKIM/DMARC records), GitHub push via "Save to GitHub", Turnstile key rotation, admin-secret rotation, Redis swap path for multi-replica, external-cron recipe (GitHub Actions) to replace the in-process scheduler, observability recommendations (Sentry, Plausible).
- ✅ Test suite grew to **24 tests** (was 19): added `test_mark_feedback_resolved`, `test_mark_feedback_resolved_404`, `test_subscribers_csv_export`, `test_subscribers_csv_requires_auth`, `test_feedback_pagination`. All passing.

### 2026-02-14 · Session 2d · Cloudflare Turnstile + admin triage queues
- ✅ **Cloudflare Turnstile** on all 4 public forms (subscribe / feedback / contact / blog-newsletter):
  - New `<Turnstile>` component with lazy script loading, explicit-render mode, and imperative `reset()` / `getToken()` via `useImperativeHandle`.
  - Public site key in `/src/lib/turnstileConfig.ts`.
  - Secret in `/app/backend/.env` (`CF_TURNSTILE_SECRET`).
  - Backend `turnstile.py` verifies tokens against `https://challenges.cloudflare.com/turnstile/v0/siteverify` (async via `httpx`). 403 on missing/invalid tokens.
  - Test-env bypass via `TURNSTILE_DISABLED=1` (set by conftest).
  - Live-verified: `POST /api/{subscribe,feedback,contact}` without token → **HTTP 403** with friendly "Human verification failed" detail.
- ✅ **Admin triage queues** — `AdminDashboard` now has 3 tabs: Stats / Feedback queue / Contact queue.
  - Newest-first lists with ticket ID badge (colour-coded), user name + email, category/rating, timestamp, and the full message.
  - **One-click mailto reply** button on each item, pre-filling subject `Re: … (#TICKET-ID)`.
  - Empty-state illustrations.
  - New endpoints `GET /api/admin/feedback?limit=20` and `GET /api/admin/contacts?limit=20` (Bearer-protected, newest-first, `_id` stripped).
- ✅ Test suite grew to **19 tests** (was 15): added admin queue tests (auth + content + `_id` exclusion) and Turnstile enforcement test with mocked verify.
- ✅ Live-verified feedback & contact queues in the admin UI — 6 feedback items + 8 contact items render with working reply mailtos.

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

### P1 — Next (user action required)
- Paste the `whsec_…` signing secret from https://resend.com/webhooks → endpoint `https://liveastrology.app/api/webhooks/resend` into `RESEND_WEBHOOK_SECRET=` in `/app/backend/.env`, then restart backend (`sudo supervisorctl restart backend`). Email Health card will flip to "Webhook configured" and the endpoint will start cryptographically verifying every payload.
- Set `LIVEASTROLOGY_URL` + `LIVEASTROLOGY_ADMIN_SECRET` in GitHub Actions secrets to activate the shipped `weekly-horoscope.yml` external cron, then set `ENABLE_SCHEDULER=0` in `/app/backend/.env` to stop the in-process duplicate.

### P1 — Marketing audit Phase 2 (next session)
- ✅ Seed 5 SEO blog articles — *shipped 2026-05-20 session 2i*
- ✅ Build "VS/Alternatives" landing pages — *shipped 2026-05-20 session 2i (3 pages live)*
- ✅ Enrich JSON-LD — *shipped 2026-05-20 (HowTo on calculators; Article schema already existed on blog posts)*
- ✅ Synastry social-share + cards — *shipped 2026-05-20*

### P2 — Marketing audit Phase 3 (strategic) — ✅ shipped 2026-05-22 session 2j
- ✅ PWA: manifest + service worker + install prompt (push notifications deferred per user choice)
- ✅ Freemium tier ($4.99/mo, $39/yr) — Stripe Checkout, email-based entitlement lookup
- ✅ GEO expansion — Spanish `/es/carta-natal`, Portuguese `/pt/mapa-astral`, Hindi `/hi/janam-kundali`
- Social media launch — TikTok + Instagram (operational, not engineering).

### P1 — Production hardening for Premium (next session)
- ✅ **Premium fulfilment**: 4 Resend templates shipped (welcome + 10-planet + monthly forecast + compatibility). Welcome + 10-planet fire on beta grant. *Remaining*: monthly cron to dispatch `premium_forecast` on the 1st, and the request-driven `premium_compatibility` flow.
- ✅ **iOS PWA icons**: PNG fallbacks added 2026-05-23.
- 🔒 **Stripe webhook signature verification**: when re-enabling Stripe after beta — set `STRIPE_WEBHOOK_SECRET` and switch the handler to 401 on bad signature.
- 🔁 **Stripe true subscriptions**: when re-enabling Stripe, swap one-time charges for true Stripe Subscriptions + Customer Portal.
- 🚀 **PWA push notifications**: deferred per user choice — needs VAPID keys + opt-in UI + push library.

### P2 — Backlog
- Placidus / Koch / Equal house system options (whole-sign is live now; others are larger due to polar-latitude edge cases).
- Declinational aspects (parallel / contraparallel).
- Per-planet interpretations for Jupiter & Saturn on the birth-chart page (glyphs + positions are live; narrative copy is pending).
- Admin row-click drill-downs (view full thread of one subscriber's history).
- Multi-replica deployment ops (Redis already wired — just set `REDIS_URL`).
- Weekly-brief editorial layer: human narrative on top of the ephemeris-derived transits.

## Test credentials

No user authentication in the app. Backend testing uses:
- **Resend-deliverable inbox**: `salimmakrana@gmail.com` (testing-mode only).
- **Admin notification recipient**: `notify@liveastrology.app` (configured in `.env`, will start delivering once domain is verified).

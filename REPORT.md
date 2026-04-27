# Repository Analysis Report

**Repository:** [salimemp/liveastrology](https://github.com/salimemp/liveastrology)
**Analyzed on:** 2026-01 (cloned fresh from `main`)
**Last commit:** `09034bf` — "Initial commit: Sun Moon Rising Sign Calculator" (single commit)
**Total source files:** 45 (26 TypeScript/TSX source files, ~5,880 LOC)

---

## 1. Executive Summary

`liveastrology` is a **single-page, front-end–only React application** that calculates and displays a user's Sun, Moon, and Rising zodiac signs, plus several supporting calculators (Synastry, Love Compatibility, Sign Calculator hub) and static content pages (Blog, About, Privacy, Terms, Refund, Contact).

The project is well-scaffolded with a modern stack (Vite + React 18 + TypeScript + Tailwind + shadcn-style setup), has a clear visual spec (`SPEC.md`), and ships a polished celestial/glass-morphism UI with a dark/light theme toggle and an animated canvas starfield.

However, the codebase is essentially an **MVP/prototype**: there is no backend, no persistence, no tests, and several **functional correctness bugs** — most notably an incorrect Sun-sign mapping for dates in January and early February, and a broken blog-post detail view. The "astrology" math is simplified placeholder logic and should not be presented as accurate.

---

## 2. Repository Structure

```
liveastrology/
├── index.html
├── package.json              # pnpm, Vite, React 18.3, TS 5.6
├── pnpm-lock.yaml
├── vite.config.ts            # React plugin + vite-plugin-source-identifier
├── tailwind.config.js        # Custom space/cosmic/element palette + animations
├── tsconfig.{json,app,node}.json
├── eslint.config.js          # Flat config, TS-ESLint + react-hooks + react-refresh
├── components.json           # shadcn/ui config (New York style, not actually used)
├── README.md                 # Generic Vite+React template readme
├── SPEC.md                   # Excellent product spec (design + features + types)
├── public/
│   └── use.txt               # Placeholder file
└── src/
    ├── main.tsx              # Entry, wraps App in <ErrorBoundary>
    ├── App.tsx               # Central router-by-state for ~11 "pages"
    ├── App.css, index.css    # 674 lines of global CSS incl. CSS vars for theming
    ├── vite-env.d.ts
    ├── context/
    │   └── ThemeContext.tsx  # dark/light theme, localStorage persistence
    ├── hooks/
    │   └── use-mobile.tsx    # shadcn-style mobile breakpoint hook (unused?)
    ├── lib/
    │   ├── astrology.ts      # 469 lines – core data + calculation logic
    │   └── utils.ts          # cn() (classnames)
    └── components/           # 21 components, ~4,800 LOC
        ├── Navigation (inside App.tsx)
        ├── StarfieldBackground.tsx
        ├── InputForm.tsx / LocationSearch.tsx
        ├── ResultsDisplay.tsx / SignCard.tsx / ZodiacSymbol.tsx
        ├── Charts.tsx (ElementBalanceChart, ModalityChart)
        ├── CompatibilitySection.tsx / EducationSection.tsx
        ├── SynastryChart.tsx / LoveCalculator.tsx
        ├── SignCalculatorsPage.tsx
        ├── BlogPost.tsx      (list + detail)
        ├── Footer.tsx
        ├── AboutUs / ContactPage / PrivacyPolicy /
        │   TermsOfService / RefundPolicy (static pages)
        └── ErrorBoundary.tsx
```

---

## 3. Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Build tool | **Vite 6** | Fast HMR, ESM-only. `vite-plugin-source-identifier` injects `data-matrix-*` attributes in dev for instrumentation. |
| Language | **TypeScript 5.6** | Flat ESLint config with `@typescript-eslint`. `no-explicit-any` and `no-unused-vars` disabled. |
| UI framework | **React 18.3** (StrictMode) | No React Router — navigation is implemented via a local `activePage` state in `App.tsx`. |
| Styling | **Tailwind CSS v3.4** + `tailwindcss-animate` | Extensive custom theme (space/cosmic/element palettes, keyframes). Mixed heavy use of **inline `style={}` objects** with theme ternaries. |
| UI primitives | Full **Radix UI** set (~25 packages) + `class-variance-authority`, `clsx`, `cmdk`, `sonner`, `vaul` | `components.json` suggests shadcn/ui but **no `components/ui/` directory exists** — the Radix deps are essentially unused. |
| Forms | `react-hook-form`, `@hookform/resolvers`, `zod` | Declared but **not used** in shipped code (forms are controlled with `useState`). |
| Icons | `lucide-react` 0.364 | Used throughout. |
| Charts | `recharts` | Declared but **not used** — charts are hand-rolled SVG (`Charts.tsx`). |
| Dates | `date-fns` | Declared but **not used** — the code uses native `Date` only. |
| Routing | `react-router-dom` 6 | Declared but **not used**. |
| Package manager | **pnpm** (custom store `/tmp/.pnpm-store`) | `scripts.dev` runs `pnpm install --prefer-offline` before every command. |
| Linting | ESLint 9 (flat), typescript-eslint 8 | |
| Testing | **None** | `playwright@1.57.0` is in `dependencies` (not devDependencies) but there are zero test files. |
| Backend / DB | **None** | Purely client-side; no `.env`, no API calls other than Google Fonts CDN. |

---

## 4. Features Implemented

### Main user-facing flows
1. **Home** (`App.tsx`) — hero, 3 feature cards, a quick-start CTA, and an embedded `InputForm`.
2. **Birth Chart Calculator** (`InputForm` → `calculateAstrology()` → `ResultsDisplay`)
   - Inputs: name, DOB (native `<input type="date">`, bounded 1900-today), birth time, city (autocomplete), "use my location" via `navigator.geolocation`.
   - Validation, a 1.5 s fake "calculating" delay, then reveal.
   - Output: three `SignCard`s (Sun/Moon/Rising) with element badge, ruling planet, traits, strengths, challenges, expandable description; `ElementBalanceChart` (donut) and `ModalityChart` (bars); `CompatibilitySection`; three educational blocks (`WhatIsBirthChart`, `PlanetMeanings`, `FAQSection`); personalised cosmic-identity summary; share-to-clipboard / Web-Share API.
3. **Synastry Chart Calculator** — enter two sets of DOB → simplified Sun-sign-only compatibility score (0-100), colored radial progress, overview, strengths, challenges, romantic + communication insights.
4. **Love Calculator** — pick two zodiac signs from dropdowns → compatibility score with love-languages, relationship advice, long-term potential.
5. **Sign Calculators Page** — aggregator/landing for the above.
6. **Blog** — three hardcoded articles with list view, category chips, fake featured-image gradients, like button, share (Twitter/Facebook/copy-link), "comments coming soon" placeholder. Newsletter sign-up is a no-op.
7. **Static pages** — About, Contact, Privacy, Terms, Refund.
8. **Theme toggle** — floating bottom-right button; persists to `localStorage`.
9. **Starfield background** — 192-line canvas animation: twinkling stars, 3 nebula radial gradients, 3 constellation lines, periodic shooting stars. Runs only in dark mode.

### Supporting domain model (`src/lib/astrology.ts`)
- Complete dataset for the 12 zodiac signs (name, symbol, element, modality, day-of-year range, ruling planet, traits, strengths, challenges, description).
- `calculateSunSign`, `calculateMoonSign`, `calculateRisingSign`, `calculateElementBalance`, `calculateModalityBalance`, `calculateCompatibility`, plus helpers.
- `MAJOR_CITIES` (`LocationSearch.tsx`) — hand-curated list of **~95 cities** worldwide with lat/long/timezone. Search is a simple `.includes()` on name/country, capped at 8 results.

---

## 5. Architecture Notes

- **Single-state pseudo-router:** `App.tsx` holds a `PageType` union (`'home' | 'birth-chart' | 'synastry' | …`) and a big `switch` in `renderPageContent()`. Consequence: no URL routing, no deep-linking, no browser back/forward support, no SEO-friendly paths — each "page" is the same URL.
- **No backend:** every calculation, the entire city DB, and all blog content are bundled into the JS. All "submit" endpoints (newsletter subscription, contact form) are UI-only — they do nothing.
- **Theming:** dual-mechanism. CSS variables (`--text-primary`, `--bg-tertiary`, …) are defined in `index.css`, but many components also read `useTheme()` and inject inline `style` conditionals. This creates **two parallel theming systems** and is the most common source of dark-text-on-dark pitfalls in the codebase.
- **Error boundary:** one global `ErrorBoundary` wrapping `App`; prints stack to screen (`searilizeError` — note typo).
- **Navigation prop drilling:** `handleNavigate` is drilled from `App` through `Footer`, page components, etc.
- **Zero test infrastructure** despite `playwright` being a production dependency.

---

## 6. Code-Quality & Bug Findings

### 🔴 High-severity (functional correctness)

1. **Sun-sign calculator returns the wrong sign for Jan 1 – Feb 18.**
   `src/lib/astrology.ts` lines 123–145 define:
   ```ts
   aquarius: { dates: [1, 19], … }     // wrong range
   pisces:   { dates: [20, 49], … }    // wrong range
   capricorn:{ dates: [357, 365], … }  // only covers Dec 23–31
   ```
   Correct astrological boundaries:
   - Capricorn = Dec 22 – Jan 19 → days 357-365 **and 1-19**
   - Aquarius = Jan 20 – Feb 18 → days **20-49**
   - Pisces = Feb 19 – Mar 20 → days **50-79**

   The function `calculateSunSign`:
   - Maps **days 1-19 (Jan 1-19) → Aquarius** (should be Capricorn).
   - Maps **days 20-49 (Jan 20-Feb 18) → Pisces** (should be Aquarius).
   - Maps days 50-79 → Pisces via the final `else` branch (coincidentally correct).
   - Also does **not account for leap years**, so Feb 29 and dates after it in leap years will shift by one day relative to the hardcoded day-of-year ranges. Effect: birthdays near the cusp of a sign can be off by one sign in leap years.

   **Impact:** Every user born in the first 49 days of any year gets the wrong Sun sign — i.e. the core advertised feature is incorrect for ~13 % of potential users.

2. **Blog detail view is unreachable when `BlogList` is used as `<BlogList />` (no `onSelectPost` prop).**
   `src/components/BlogPost.tsx:306`:
   ```ts
   if (selectedPost && onSelectPost) {
     return <BlogPostView post={selectedPost} onBack={() => setSelectedPost(null)} />;
   }
   ```
   `App.tsx` renders `<BlogList />` without that prop, so clicking an article sets `selectedPost` in state but the `&& onSelectPost` guard prevents rendering. The card click also calls `onSelectPost?.(post)` (no-op) and falls back to the list again. Users can never actually read a blog post.

3. **Moon-sign and Rising-sign "calculations" are purely decorative.**
   - `calculateMoonSign` uses `(dayOfYear * 13) % 360 + 180` with no ephemeris, no timezone, no longitude. It is effectively a deterministic hash of date+time and has no astronomical meaning.
   - `calculateRisingSign` uses `(totalHours * 15 + lat*0.5 + sin(...)*10 + 90) % 360`. Also astronomically invalid; latitude influence is near-zero and longitude is ignored.
   - `timezone` is captured from the city DB but **never applied** to the birth time; the app treats the user's wall-clock time as if it were universal.
   - `SPEC.md` mentions "Swiss Ephemeris principles" — no such library is present.

   This is fine as an entertainment toy, but the UI copy ("accurate reading", "calculated with precision") is misleading. At minimum, a clearer disclaimer belongs next to the headline, not only at the bottom.

4. **Synastry `calculateSimpleSign` has off-by-one cusp logic.**
   The nested `month === sign.end[0] && day <= sign.end[1]` then `month < sign.end[0] && day <= sign.end[1]` branches mis-assign certain edge dates (e.g. Jan 25 → tries to match `Capricorn{end:[1,19]}` where `month===1, day=25>19`; then next iter `Aquarius{end:[2,18]}` where `month<2 && day<=18` is false → falls through). Some late-in-month dates can silently default to `Capricorn` at the end of the loop.

### 🟠 Medium-severity

5. **`activePage` reset logic races with result state.**
   In `App.tsx`:
   ```ts
   const handleNavigate = (page) => {
     setActivePage(page);
     if (page !== 'birth-chart' || result) handleReset();
   };
   ```
   If a user has a result and clicks "Birth Chart Calculator" again, `result` is truthy so `handleReset` runs — but the re-render of `renderPageContent()` still sees the old `result` on the first pass because `setResult(null)` hasn't flushed, then re-renders again. Non-blocking, but a stale-frame flash is possible.

6. **Dead imports / unused dependencies.**
   `react-hook-form`, `zod`, `@hookform/resolvers`, `react-router-dom`, `date-fns`, `recharts`, most `@radix-ui/*`, `vaul`, `cmdk`, `sonner`, `embla-carousel-react`, `input-otp`, `react-day-picker`, `react-resizable-panels`, `next-themes` are all declared but unused. This adds **tens of MB to node_modules** and bloats type-checking. `playwright@1.57.0` is in `dependencies` (should be `devDependencies`).

7. **README is the stock Vite template**, not project documentation. `SPEC.md` is excellent but targeted at designers; nothing tells a new contributor how to run or deploy.

8. **`.npmrc` hard-codes host-specific paths.**
   ```
   store-dir=/tmp/.pnpm-store
   virtual-store-dir=/tmp/sun-moon-rising-calculator/.pnpm
   ```
   Forces every clone on Windows/macOS/CI to use `/tmp/...`, which fails on non-POSIX systems. These paths belong in a machine-local file, not in the repo.

9. **`scripts.dev` runs `pnpm install --prefer-offline` on every invocation.** Slower iteration; on CI this re-resolves the lockfile on each run.

10. **No `lang` / accessibility attributes on some interactive elements.** Many `<button>`s in the nav/footer rely on text-only labels — fine — but the social-media anchors use raw SVGs with only `aria-label` and no `<title>` inside the SVG; should be OK but worth reviewing for screen readers.

11. **Inline styles override theme tokens.** E.g. `SynastryChart.tsx`, `LoveCalculator.tsx`, `BlogPost.tsx` hard-code `color: '#1a1a3a'` (near-black) on headings. In **dark mode** these components render as dark text on dark background and become unreadable. (`App.tsx` does pass `theme` ternaries, but these children components do not consume `useTheme()`.) This is the single biggest dark-mode regression in the app.

12. **`InputForm.tsx` `name` input is captured but there is no visible error styling tie-in for `errors.name`** — the message appears but the input border doesn't change.

### 🟡 Low-severity / hygiene

13. **Typo** — `searilizeError` should be `serializeError` (`ErrorBoundary.tsx`).
14. `TYPE_CONFIG.bgGradient` in `SignCard.tsx` is never consumed.
15. `ESLint` config silences `no-unused-vars` and `no-explicit-any` globally — hides drift.
16. `EducationSection.tsx` (165 LOC) exports three components as named exports from one file — fine, but violates the rest of the one-component-per-file convention in the repo.
17. `@types/react-router-dom` is v5 while `react-router-dom` is v6 — type mismatch.
18. No `robots.txt`, no `sitemap.xml`, no Open Graph / Twitter card metadata in `index.html` (just `description` + `theme-color`) — hurts SEO despite the site being marketing-oriented.
19. No favicon asset file — uses inline SVG emoji, which doesn't render on many browsers/platforms.
20. Animated starfield redraws the full canvas at ~60 fps unconditionally while it is visible (even offscreen). On battery-powered devices this is noticeable.

---

## 7. Security & Privacy

- **No secrets / tokens in the repo.** Good.
- **No server, no database, no auth.** All computation is client-side → no exposure surface beyond XSS.
- **No `dangerouslySetInnerHTML`** usage. Blog content is rendered as plain text split on `\n\n`; safe but brittle (no Markdown parser, so the "##" / "- " parsing is ad-hoc).
- **Geolocation**: uses `navigator.geolocation.getCurrentPosition` only on explicit button click — compliant best practice.
- **localStorage** stores only `theme` — no PII. Privacy page claim of "data processed locally and never stored" is consistent with what the code actually does.
- **Third-party calls**: only Google Fonts (preconnect + stylesheet). No analytics, no tracking pixels. Privacy-friendly by default.
- **Outbound social links**: hard-coded `twitter/facebook/instagram/youtube/tiktok.com/liveastrology` — all use `target="_blank" rel="noopener noreferrer"` ✅.
- **Newsletter and contact forms do nothing** — users are shown a success toast but no email is transmitted. This is *functionally* a dark pattern unless clearly labelled.

---

## 8. Deployment Readiness

- **Build works** (`pnpm build` runs `tsc -b` then `vite build`); output is a static `dist/` — deployable to any static host (Vercel, Netlify, Cloudflare Pages, S3+CloudFront, GitHub Pages with a path fix).
- **Env config**: none required.
- **Caveats:**
  - Hard-coded `/tmp/...` paths in `.npmrc` will break local dev on Windows.
  - No SSR / pre-render → blog & marketing pages are invisible to crawlers (they're all client-rendered under the same URL).
  - No `vercel.json` / `_redirects` — once real routing is added, SPA fallback must be configured.

---

## 9. Recommendations

### Must-fix before any production launch
1. **Correct the Sun-sign lookup.** Replace the fragile `dayOfYear`-in-range chain with a simple `(month, day)` table and add explicit boundary handling for the Dec 22–Jan 19 wrap. Unit-test every boundary and leap-year case. This is a one-hour fix and resolves Bugs #1 and #4.
2. **Fix the blog detail view** by removing the `&& onSelectPost` guard (or always providing the callback), and restore deep-linkable URLs.
3. **Move the "entertainment only" disclaimer to the top** of calculators that use the placeholder Moon / Rising logic — or integrate a real ephemeris (e.g. `astronomia`, `swisseph` via WASM, or a server-side API) before continuing to market accuracy.
4. **Fix dark-mode contrast regressions** in `SynastryChart`, `LoveCalculator`, `BlogPost`, `BlogPostView` — replace hard-coded `#1a1a3a` / `#4a5568` / `#f8f9fa` with CSS-variable tokens (`var(--text-primary)`, etc.) that already exist in `index.css`.

### Strongly recommended
5. Adopt `react-router-dom` (already installed): one route per page, 404 page, real URL sharing for blog posts and calculators.
6. Prune unused dependencies (`zod`, `date-fns`, `recharts`, `next-themes`, most `@radix-ui/*`, `vaul`, `cmdk`, `sonner`, etc.) or actually use them (e.g. `zod` + `react-hook-form` for form validation; `recharts` for charts).
7. Move `playwright` to `devDependencies` and add at minimum one smoke test per calculator.
8. Replace the hand-curated `MAJOR_CITIES` list with a real geocoder (OpenStreetMap Nominatim, Google Places, or a bundled GeoNames dataset) — 95 cities is far too restrictive. Or allow free-text entry with manual timezone offset.
9. Honour the user's birth-time timezone: convert birth time to UTC before using it in calculations.
10. Add Open Graph / Twitter Card meta tags and a real favicon; add `robots.txt` + `sitemap.xml` once routing exists.
11. Rewrite `README.md` with setup, scripts, architecture overview, and deployment notes.
12. Remove `/tmp/...` paths from `.npmrc`.
13. Turn `@typescript-eslint/no-unused-vars` and `no-explicit-any` back **on** (warn-level) to catch dead code and drift.
14. Wire the newsletter and contact forms to a real backend (Mailchimp, ConvertKit, Resend, Formspree) **or** remove them entirely — shipping non-functional forms is a trust killer.

### Nice to have
15. Lazy-split the three calculators with `React.lazy` — they're independent routes and each pulls distinct code paths.
16. Throttle the starfield animation when the tab is not visible (`document.visibilityState`).
17. Extract repeated inline-style button objects in `Footer.tsx` into a reusable `<FooterLink>` component (the file is 370 lines, much of it duplicated).
18. Add basic analytics (Plausible / Umami — privacy-respecting) to see which calculator users actually use.
19. Persist the last result in `localStorage` so users can revisit without re-entering birth data.
20. Produce shareable PNG chart images (there's a disclaimer-shaped hole where this feature was planned in `SPEC.md`).

---

## 10. Verdict

- **Design & UX:** 🟢 Strong — clear product vision, coherent celestial aesthetic, responsive layout, working dark/light toggle, nice animated starfield.
- **Feature breadth:** 🟢 Good — 3 calculators + blog + 5 legal/static pages, covering 90 % of what the `SPEC.md` promises.
- **Domain correctness:** 🔴 Problematic — the headline calculation is wrong for ~13 % of inputs; Moon/Rising are not real astrology.
- **Code quality:** 🟡 Mixed — clean file separation and clear TS types, but substantial dependency bloat, inconsistent theming, no tests.
- **Security/privacy posture:** 🟢 Good — purely client-side, no data collection, no third-party tracking.
- **Production-readiness:** 🟡 Not yet — dark-mode contrast issues, unreachable blog detail, sign-calculation bug, and no real backend for forms.

**Overall:** a promising, design-forward MVP that could become a compelling astrology site with **~1 week** of focused engineering on the four "must-fix" items plus routing and a real geocoder.

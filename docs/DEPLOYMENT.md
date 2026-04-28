# Live Astrology — Deployment & Production Cutover Guide

This document covers the manual actions needed to take Live Astrology from
its current preview state to a fully productionised deployment. Each
section lists what **you** need to do (the agent can't perform DNS,
domain-ownership, or external-service actions on your behalf).

---

## 1. Resend — unlock production email delivery

While testing, Resend only delivers emails to the owner's account email
(`salimmakrana@gmail.com`). To send to anyone on the internet, you need
to verify the `liveastrology.app` domain.

**Steps:**

1. Log in to https://resend.com → **Domains** → **Add Domain** → enter `liveastrology.app`.
2. Resend will show you **DNS records** to add — typically:
   - 1 × `TXT` record (SPF) at `@` or `liveastrology.app`
     - e.g. `v=spf1 include:amazonses.com ~all`
   - 1 × `TXT` record (DKIM) at `resend._domainkey`
     - value provided by Resend
   - 1 × `MX` record at `send` subdomain (if using custom return-path)
   - 1 × `TXT` record (DMARC) — optional but recommended
     - e.g. `v=DMARC1; p=none; rua=mailto:dmarc@liveastrology.app`
3. Add those records in your DNS host (Cloudflare / Namecheap / Google Domains / wherever you bought the domain).
4. Back in Resend, click **Verify**. Verification usually completes within 5–30 minutes.
5. Once the domain shows **Verified**, update `/app/backend/.env`:
   ```
   SENDER_EMAIL=Live Astrology <hello@liveastrology.app>
   NOTIFY_EMAIL=notify@liveastrology.app
   ```
6. Restart the backend: `sudo supervisorctl restart backend`.
7. Test end-to-end: submit the `/feedback` form from a fresh email you own and confirm the acknowledgment arrives.

---

## 2. GitHub — push the current `/app` state to `salimemp/liveastrology`

Click the **"Save to GitHub"** button in the Emergent chat input. Select:
- Your GitHub account
- Repo: `salimemp/liveastrology`
- Branch: `main`

**To completely replace the remote ("remove all previous files"):**
- Delete the repo on GitHub (Settings → Delete this repository).
- Create a new empty repo with the same name.
- Click "Save to GitHub" in Emergent to push everything fresh.

Direct `git push` from the code agent is disabled by design — you stay
in control of exactly what goes up.

---

## 3. Cloudflare Turnstile — production keys

The app currently uses your provided site key `0x4AAAAAADExRj14IvpGPMYD` and
the matching secret in `/app/backend/.env` (`CF_TURNSTILE_SECRET`). No
action needed unless you want to rotate the secret:

1. Generate a new key pair at https://dash.cloudflare.com → Turnstile → Add site.
2. Replace `TURNSTILE_SITE_KEY` in `/app/liveastrology/src/lib/turnstileConfig.ts`.
3. Replace `CF_TURNSTILE_SECRET` in `/app/backend/.env`.
4. Rebuild frontend + restart backend.

---

## 4. Admin secret — rotate before shipping

`/app/backend/.env` ships with `ADMIN_SECRET=change-me-to-a-long-random-string-before-shipping`.

**Generate a strong secret and replace it:**

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Then paste into `/app/backend/.env` as `ADMIN_SECRET=...` and restart the
backend. Share the new secret with your ops team through a password
manager — never commit it anywhere, never share via chat.

---

## 5. Multi-replica deployment — swap to Redis-backed rate limiter

The current `slowapi` limiter keeps counters in-process memory. If you
scale beyond a single pod (or to a multi-worker `uvicorn` setup), a user
could slip past the limit by hitting a different replica each time.

**When that time comes:**

1. Install Redis and expose it at `REDIS_URL=redis://…` in the backend env.
2. In `/app/backend/server.py`, change the limiter init to:
   ```python
   limiter = Limiter(
       key_func=_client_ip,
       default_limits=["120/minute"],
       storage_uri=os.environ["REDIS_URL"],
   )
   ```
3. `pip install "slowapi[redis]"` (already in requirements.txt via the slowapi base).
4. Restart backend. The limiter will now share counters across every replica.

---

## 6. Scheduler — external cron for reliability

The in-process APScheduler weekly cron inside `server.py` fires every
Sunday 18:00 UTC but **will miss its window if the pod restarts during
that minute**. For reliable weekly delivery in production, prefer an
external cron hitting the manual dispatch endpoint:

```bash
# GitHub Actions cron (.github/workflows/weekly.yml):
on:
  schedule:
    - cron: '0 18 * * 0'  # Sundays 18:00 UTC
jobs:
  dispatch:
    runs-on: ubuntu-latest
    steps:
      - run: |
          curl -X POST https://liveastrology.app/api/admin/dispatch-weekly \
            -H "Authorization: Bearer ${{ secrets.LIVEASTROLOGY_ADMIN_SECRET }}"
```

When you switch to external cron, set `ENABLE_SCHEDULER=0` in
`/app/backend/.env` to stop the in-process scheduler from firing a
duplicate send.

---

## 7. Observability — logging & monitoring (recommended)

Nothing is wired yet. Suggested additions once you pick a provider:

- **Sentry** for error tracking (both FE + BE). Grab DSN → add `VITE_SENTRY_DSN` + `SENTRY_DSN`.
- **Plausible / Fathom / Umami** for privacy-respecting analytics (drop-in script in `index.html`).
- **Cloudflare Analytics** is already free if you host DNS there.
- **Healthchecks.io** ping in the scheduler to alert if the weekly job ever fails to fire.

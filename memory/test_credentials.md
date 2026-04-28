admin@liveastrology.app  /  ADMIN_SECRET=change-me-to-a-long-random-string-before-shipping

There is no end-user authentication in the app.

Admin-only HTTP endpoints (`/api/admin/*`) use a **shared-secret Bearer token**
read from `ADMIN_SECRET` in `/app/backend/.env`:

- `POST /api/admin/dispatch-weekly`  — manually fire the weekly horoscope to every confirmed subscriber.
- `GET  /api/admin/stats`            — counts for subscribers / feedback / contacts / weekly dispatches.

Example:

    curl -H "Authorization: Bearer change-me-to-a-long-random-string-before-shipping" \
         https://cosmic-admin-live.preview.emergentagent.com/api/admin/stats

**Before going live**, update `ADMIN_SECRET` in `/app/backend/.env` to a long
random value (`openssl rand -hex 32`) and restart the backend.

For Resend email delivery during testing mode, only the account owner's
inbox (`salimmakrana@gmail.com`) receives emails — everyone else is
silently dropped by Resend with a logged error. Verifying the
`liveastrology.app` domain at https://resend.com/domains unlocks
production delivery.

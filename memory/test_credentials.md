# Maple Journey — Test Credentials

## Admin
- Email: `admin@maplejourney.ca`
- Password: `MapleAdmin!2026`
- Seeded on backend startup via `ADMIN_EMAIL` / `ADMIN_PASSWORD`. Exempt from onboarding gating.

## Test newcomer (user role)
- Email: `newcomer_demo@test.com`
- Password: `Test1234!`
- NOTE: profile IS completed (city=Toronto, express_entry, arrival 2026-04-01) so it lands on the Home briefing / Profile / Jobs. To test onboarding gating, sign up a fresh user.

## Notes
- Auth: JWT (email + password). Token in localStorage key `mj_token`.
- Signup is streamlined to name + email + password; the rest (situation, country, etc.) is captured in the onboarding questionnaire.
- Flow: signup → `/app/onboarding` (gated) → `/app/plans` (choose tier) → `/app`.
- Tiers: Free / Plus ($2.99/mo) / Family ($4.99/mo). Free tier = 8 Maple chats/day; paid = unlimited + deeper personalization.
- Backend `.env` keys: MONGO_URL, DB_NAME, CORS_ORIGINS, JWT_SECRET, ADMIN_EMAIL, ADMIN_PASSWORD, EMERGENT_LLM_KEY, STRIPE_API_KEY (=sk_test_emergent, Stripe test).
- Twilio (phone OTP / WhatsApp) NOT configured — those features error until creds are provided.

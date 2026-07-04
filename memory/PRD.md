
## Implemented (2026-07 — Onboarding redesign + tiers/payments + smart Maple)
Verified by testing agent: iteration_4 (signup/onboarding redesign) and iteration_5 (gating + payments + limits) — 100% backend, all frontend flows pass.
- **Deployed full source into /app** (repo skeleton was incomplete): backend routers/services/core + full frontend src, set backend `.env` (JWT/admin/EMERGENT_LLM_KEY/STRIPE_API_KEY), installed deps. App runs.
- **Sign Up redesign** (`Auth.jsx` + `lib/validation.js`): premium split-panel, streamlined to name+email+password (situation/country moved to onboarding), real-time inline validation, live password checklist + strength meter, autofill/aria/keyboard, trust signals.
- **Onboarding questionnaire redesign** (`Onboarding.jsx`): save-progress/resume via localStorage `mj_onboarding_v2`, focus management, aria roles (radiogroup/checkbox) + aria-live progress with section labels, 44px touch targets, reduced-motion aware, added DOB + gender (blueprint identity), real-time field validation (DOB/postal/number). Fixed DOB inline-error bug (errors show immediately).
- **App gating**: non-admin users must complete onboarding before entering `/app` (AppLayout redirects to `/app/onboarding`).
- **Tiers + Stripe** (`routers/payments.py`, `PlanSelection.jsx`): after onboarding → `/app/plans`. Cheap tiers Free / Plus $2.99 / Family $4.99 (prices server-side only). Stripe Checkout via emergentintegrations, `payment_transactions` collection, poll `/checkout/status`, `/webhook/stripe`, idempotent tier grant (+30 days). Topbar Upgrade button for free users.
- **Smart Maple per tier** (`chat.py`): free = 8 chats/day (`/assistant/usage`, X-Maple-Limit header + upgrade message); paid = unlimited + deeper, profile-aware system prompt. Personalization already reads full profile.
- **Be real / cleanup**: removed fake "Resume Maker (coming soon)" from Landing + Features; cleaned banned-word seed copy (landing hero, announcement "Wings"→"Maple"); marketing Pricing/Landing plans updated to new cheap tiers.

## Next tasks / backlog
- P0: Recurring billing (current Stripe flow is one-time 30-day grant, not a subscription) + tier expiry enforcement/downgrade job.
- P1: Marketing still shows "Journey Timeline" & "Document Vault" but those pages/endpoints aren't built — decide build vs remove for full "be real" alignment.
- P1: Settings page — surface current plan + manage/cancel; show remaining free chats in the Maple dock UI.
- P2: Deploy readiness pass (deployment_agent), then P2/P3 from earlier backlog (Today/Resources/Profile IA, de-bias questionnaire further).

## Implemented (2026-07 — Profile hub + per-profile Jobs + polish)
- **Profile hub** (`Profile.jsx`, replaces Settings) with tabs: My Details (rich editable profile), Immigration Timeline (computed countdowns incl. citizenship ≈1095d after PR), Companion (tone/autonomy + WhatsApp OTP), Subscription (tier + billing history), Data & Privacy (consents, JSON export, account delete), App Settings (theme). Nav item renamed Settings→Profile at /app/profile (/app/settings redirects). Verified: iteration_6 (8/8 backend, all frontend flows).
- **Encrypted sensitive IDs**: IRCC file # / foreign ID via Fernet (`core/crypto.py`, key from JWT_SECRET). Endpoints: GET/PUT /auth/secure-ids, GET /auth/export, DELETE /auth/account, GET /billing/history. Not leaked via /auth/me.
- **Per-profile Jobs matching** (`domain.py job_match_score`): ranks by occupation/title overlap, province (fixed substring bug), LMIA-exempt vs permit category, seeking status; returns match% + match_reasons, sorted. UI shows reason chips. Verified: dev/ON→Software Developer 99%, nurse/BC→Registered Nurse 91%.
- **Polish**: login redirect respects profile_completed (no blank flash); Profile MyDetails field components hoisted (fixes focus loss); removed exposed admin demo creds from login; sticky always-visible Continue on onboarding; deleted dead Settings.jsx; zero compile warnings.
- Fresh source zip served at /maplejourney-source.zip.

## Next tasks / backlog
- P0: Recurring Stripe billing + tier expiry/downgrade job (currently one-time 30-day grant).
- P1: Today/Overview enrichment (IRCC news/holidays/alerts); marketing still lists Timeline/Document Vault as features (Timeline now exists in Profile — align marketing copy).
- P1: Deepen onboarding questionnaire with remaining blueprint fields (NOC, credentials country, spouse status, dependents-as-ages) — keep it clean/short.
- P2: Get Connected sub-pages (eSIM/banking/transit), Communities map/list toggle, admin extras.

## Implemented (2026-07 — Home/Today = grounded morning briefing)
Redesigned Home to the blueprint direction: a localized, grounded morning briefing (was a companion/suggestions screen). Verified iteration_7 (100% backend 3/3, frontend 6/6, no bugs).
- **New endpoint GET /api/overview** (`routers/overview.py`): time-aware greeting ("Good morning, {name}. Here's today's briefing for {city}."); real weather via Open-Meteo (geocode+current, graceful fallback); cited IRCC news from canada.ca atom feed (ranked by immigration_category + province, 5-min cache); upcoming statutory + religion-aware holidays (Easter/nth-weekday computed); days_since_arrival (<365); ads (admin inventory, blank if none). Every item carries a source; nothing generated without retrieval.
- **Home UI** (`WingsHome.jsx`): per-word greeting fade (30ms stagger), weather card, "Today's briefing" cited news cards (external canada.ca links + IRCC source chip), holiday pills, subtle Day-N-in-Canada line, complete-profile banner (empty state), slim sticky "Ask Maple" bar (opens dock). Flat skeletons (no shimmer), reduced-motion aware, no decorative illustrations — per spec.
- Fresh zip served at /maplejourney-source.zip.

## Known limitations / backlog
- overview.py RELIGIOUS holiday dates hardcoded for 2026 — expand or compute for future years (P2).
- External weather/news are best-effort (6s timeout); may be null/empty during upstream flaps.
- Alert banner (Pelmorex NAAD emergency feed) not wired — omitted until a reliable feed/source is added.
- Still pending: recurring Stripe billing + tier expiry; align marketing copy (Timeline now in Profile); Get Connected sub-pages; questionnaire depth (NOC/credentials/spouse).

## Implemented (2026-07 — Ask Maple + PR Assessment tailored to blueprint)
- **Ask Maple** (`Assistant.jsx` + SYSTEM_PROMPT in config.py): grounded, cited, scope-locked companion. Cites official canada.ca/IRCC/CRA/Service Canada URLs inline (auto-linkified in UI); refuses CRS/Express Entry/PNP strategy & Investor/Start-up visas with RCIC/CBA referral (Addendum A); "I don't have current info… canada.ca/ircc / 1-888-242-2100" fallback; IRPA s.91 disclosure banner + mandatory footer; in-scope starter prompts. Verified live (SIN cited answer; CRS request declined).
- **PR Assessment → "Status & Deadlines"** (blueprint PROHIBITS CRS/PR score calculators — Addendum A). Replaced the CRS calculator with a compliant, cited self-check: new `GET /api/status-check` returns informational cards (citizenship eligibility ≈1095d, work/study permit expiry countdowns, SIN todo, provincial health waiting period, PGWP/open-work-permit info) — NO score, NO ranking, each card cited to canada.ca with disclaimers. Nav relabeled "PR Assessment" → "Status & Deadlines".

## Known cleanup
- Legacy POST /questionnaire + services/scoring.py (CRS score) are no longer surfaced in the UI; can be removed for full Addendum A compliance (currently dead).

## Implemented (2026-07 — Jobs tailored to blueprint)
- **Jobs** reworked as a "discovery layer" per blueprint: removed the black-box match% score (v2 forbids it); now shows transparent per-profile relevance tags (Matches your field / In your province / LMIA-exempt), relevant-first ordering. Added discovery-layer disclaimer (no hosted applications, no resumes, no representing applicants), audience-specific work-authorization notes (student on/off-campus, temp worker employer-specific, refugee open-work-permit), complete-profile prompt, and per-job "View & apply" deep-link to Government of Canada Job Bank search. Honest source note (curated sample + link to full Job Bank). Backend GET /api/jobs now returns {jobs, audience_note, has_profile}; job_match_score → job_relevance (tags only).

## Fix (2026-07 — Onboarding questionnaire UI polish)
- Root cause: Tailwind `brand` palette only defined shades 50/100/500/600, but Onboarding (and Auth/MapleHome/etc.) used `brand-400/700/900`. Those classes were undefined → the cinematic dark backdrop (`from-brand-600 via-brand-700 to-brand-900`), the footer nav bar (`bg-brand-900/70`), and glow blobs (`bg-brand-400/30`) rendered transparent → washed-out white background, floating/low-contrast "Continue" button, invisible Back/Skip.
- Fix: added full brand scale (200/300/400/700/800/900) in `tailwind.config.js`. All onboarding scenes now render a clean deep-blue gradient, aligned white content card, and a solid always-visible footer bar (Back / Skip / Continue) — no overlap, consistent across every question screen. Layout structure (scroll area + shrink-0 footer) was already correct; only the palette was broken.
- Verified visually across scene types: fields (name/money), single-select options (pathway), multi-select chips (languages), consent, on 1920x800.

# MapleJourney MVP Page-Perfection Plan (Hour-by-Hour)

Goal: move from working prototype to MVP-grade product quality with clear scope, acceptance checks, and implementation order.

## Phase 0 (Stability First) - 6h

### 1) Local Runtime Reliability - 2h
- Backend starts cleanly from venv.
- Frontend starts from this repo (not old extract path).
- MongoDB service verified on startup.
- Env validation and startup error messages improved.

Done when:
- `GET /api/` returns 200.
- `/app` loads without runtime crash.

### 2) Auth + Session Hardening - 2h
- Login/register errors are human-friendly.
- Token-expired flow redirects correctly.
- Route guards verified for user/admin roles.

Done when:
- Login, logout, refresh session all work in browser and mobile browser.

### 3) Citation/Compliance Guard - 2h
- Assistant output must include valid source citation tags.
- Disallowed source domains replaced by compliant fallback.

Done when:
- Assistant never returns uncited legal guidance.

---

## Phase 1 (Core User App Pages) - 26h

### /app (MapleHome) - 3h
What to perfect:
- Clear next-step cards (Onboarding, Chat, Jobs, Legal).
- Progress snapshot and urgency labels (today/this week).
- Mobile-first spacing and readable hierarchy.

Create:
- Priority action rail component.
- Empty-state variants (new user, returning user).

Done when:
- First-time user immediately understands the next action in under 10 seconds.

### /app/onboarding - 5h
What to perfect:
- Sectioned multi-step flow with save/resume.
- Validation that is helpful and non-blocking.
- Consent and privacy clarity.

Create:
- Onboarding completion meter.
- Required-field inline hints.
- Resume banner on return.

Done when:
- New user can finish onboarding once without confusion or data loss.

### /app/chat (Assistant) - 5h
What to perfect:
- Fast response UX with loading state.
- Citation display that is readable on mobile.
- Error/fallback response tone + retry UX.

Create:
- Message-level citation card UI.
- "What to watch next" section rendering.
- Chat rate/usage indicator.

Done when:
- User can ask 3 legal questions and receive grounded, cited answers each time.

### /app/assessment (Questionnaire) - 2h
What to perfect:
- Clarify role of this page (assessment vs profile overlap).
- Tie outputs to actionable next steps.

Create:
- Result summary panel.
- Link-out actions to legal/jobs pages.

Done when:
- Assessment yields concrete, understandable actions.

### /app/jobs - 3h
What to perfect:
- Filter/sort UX (location, category, relevance).
- Job card hierarchy (title, match, visa relevance).

Create:
- Empty-state with suggestions.
- Saved jobs lightweight local state.

Done when:
- User can find and save suitable jobs in under 2 minutes.

### /app/accessibilities - 2h
What to perfect:
- Reduce static list feel, increase practical actionability.

Create:
- "Top picks for me" section based on profile.
- Region-aware cards.

Done when:
- User sees at least 3 clearly useful resources for their context.

### /app/legal - 3h
What to perfect:
- Legal boundaries and disclosure clarity.
- Trusted resource prominence.

Create:
- Severity/urgency triage block.
- Regulated representative quick links.

Done when:
- User can identify whether they need official legal representation.

### /app/communities - 2h
What to perfect:
- Action-first card design (join/contact/eligibility).

Create:
- Region + language filters.
- Quick contact actions.

Done when:
- User can find one relevant community and one contact path quickly.

### /app/profile - 1h
What to perfect:
- Edit confidence and account control clarity.

Create:
- Last-updated indicators.
- Profile completeness mini-widget.

Done when:
- User can edit key fields and understand what changed.

---

## Phase 2 (Admin Quality) - 12h

### /admin - Dashboard - 2h
- KPIs for active users, failed chats, citation fallbacks, feature flags.

### /admin/users - 3h
- Safer destructive actions + confirmation + audit stamps.

### /admin/features - 2h
- Feature toggles with explanation and immediate propagation checks.

### /admin/content - 2h
- Content edit preview and publish state visibility.

### /admin/announcements - 3h
- Draft vs send flow, target audience, send confirmation summary.

---

## Phase 3 (MVP Launch Readiness) - 8h

### Testing + Acceptance - 4h
- Smoke scenarios for auth, onboarding, chat, jobs, admin.
- Mobile browser QA pass (small/medium/large screens).

### Polish + Instrumentation - 4h
- Error toasts consistency.
- Empty/loading/success states all pages.
- Basic analytics events for key conversion steps.

---

## Total Estimated Time
- Stability: 6h
- User App Pages: 26h
- Admin: 12h
- Launch Readiness: 8h
- Total: 52h

## Suggested Execution Order
1. Stability (must-pass)
2. Onboarding + Chat + Home (highest product value)
3. Jobs + Legal
4. Admin core controls
5. Final mobile QA and acceptance sign-off

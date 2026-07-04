# Maple Journey — Principal Product Architecture Audit

**Reviewer role:** Principal Product Architect
**Scope:** Entire product (marketing → auth → app → admin), reviewed against the v2 Blueprint and the shipped codebase.
**North-star metric:** A first-time newcomer feels the app is *simple*, even though a powerful ecosystem sits underneath.
**Method:** Read the full blueprint (`maple-journey-v2-blueprint.md`) and every route, layout, page, context, and backend router in the project. Recommendations preserve the feature set — they **merge, consolidate, rewire, contextualize, and simplify**. Nothing is deleted unless it actively damages the product.

Each recommendation states: **(1)** the problem it solves, **(2)** why it improves the newcomer experience, **(3)** why it preserves the product vision, **(4)** implementation complexity (Low / Medium / High).

---

## 0. The Single Most Important Finding

The shipped product and the blueprint are **two different products wearing the same name.**

| Dimension | Blueprint intent | What the code ships |
|---|---|---|
| Product identity | "Maple Journey" — a **grounded, cited newcomer companion**. Not an immigration app. | "MapleJourney" — an **"AI immigration assistant"** ("guided by AI", "Powered by Maple AI", "Newcomers in Canada Wingman, reimagined"). |
| Companion identity | One companion named **"Maple"** (🍁), continuous across app + WhatsApp. | **Three names** for one thing: *Maple*, *Maple Wingman*, and *"Maple AI Assistant · Powered by Claude"*. |
| Personalization | 40-field lifecycle profile; **"never assume Express Entry."** | An 8-question **CRS / Express Entry score calculator** as the primary questionnaire. |
| Home screen | **Overview** — a cited daily briefing (weather, IRCC news, alerts, holidays). | **Maple Wingman Home** — a proactive nudge feed + PR-score stat cards. No briefing. |
| Voice | Banned words: *AI, GPT, smart, seamless, powered by, intelligent, magic.* | Marketing leads with **"AI", "Powered by", "IQ"** — the exact banned words. |

**This is the root cause of most cognitive load.** Before optimizing any individual screen, the product must resolve *which product it is*. Every recommendation below assumes the answer is the blueprint's: **one calm, cited, lifelong companion named Maple.** "Maple Wingman" is treated as an alias to retire.

> This is not a request to reduce functionality. Every capability below is preserved. We are giving the ecosystem **one identity, one companion, and one spine.**

---

## 1. Architecture Audit (Current State)

### 1.1 Route & surface inventory

**Marketing** (`MarketingLayout`): `/` Landing · `/features` · `/resources` · `/pricing` · `/about`
**Auth**: `/login` · `/signup` (magic-link/OTP promised in blueprint; code uses email+password JWT)
**App** (`AppLayout`, 7 sidebar items + a topbar chat icon):
- `/app` — **Maple WingmanHome** (greeting, "Ask Maple Wingman" input, 3 stat cards, nudge feed)
- `/app/chat` — **Assistant** (full-screen "Maple AI Assistant" chat) *— not in the sidebar; reached via topbar icon and via redirects*
- `/app/assessment` — **Questionnaire** (CRS calculator)
- `/app/jobs` — **Jobs** (catalog + search + save)
- `/app/accessibilities` — **Accessibilities / "Get Connected"** (eSIM + banking + transit links)
- `/app/legal` — **LegalHelp** (legal-aid directory + filters)
- `/app/communities` — **Communities** (6 category tiles → OpenStreetMap search)
- `/app/settings` — **Settings** (profile + Maple Wingman config + WhatsApp/OTP + theme + module status)

**Admin** (`AdminLayout`): `/admin` Overview · `/users` · `/features` · `/content` · `/announcements`

### 1.2 What's healthy

- **Feature-flag spine is excellent.** `FEATURE_KEYS` in `core/config.py`, effective-flags endpoint (`global AND per-user`), `FeatureGate`, and `features.js` registry driving the sidebar is a clean, scalable pattern. **Keep and build on this.**
- **Layout separation** (marketing / app / admin) is correct and conventional.
- **Backend is a tidy composition root** — routers (`auth, wings, messaging, domain, chat, admin`), `services/`, `core/`. Good bones.
- **Catalog pages are consistent** (Jobs, Legal, Accessibilities, Communities all follow *header → filter → card grid*). This is a reusable pattern already latent in the code.
- **Grounding discipline exists in the AI prompt** (`SYSTEM_PROMPT`: stay in scope, no hallucination, cite official sources). It just isn't surfaced in the UI.

### 1.3 Structural problems (ranked by impact)

| # | Problem | Evidence | Impact |
|---|---|---|---|
| P1 | **Three identities for one AI.** | `Maple WingmanHome` "Ask Maple Wingman", `Assistant` = "Maple AI Assistant · Powered by Claude", `Settings` "Your Maple Wingman", WhatsApp = "Maple". | Highest — the user can't form a single mental model of their companion. |
| P2 | **Two AI entry points that don't share state.** | Home's "Ask Maple Wingman" input `onFocus`/submit just `navigate('/app/chat')`, discarding typed text; `Assistant` keeps its own `session_id` in `localStorage`. | High — typing on home loses your words; chat feels like a separate app. |
| P3 | **Chat is hidden.** | `/app/chat` is not in `FEATURES`/sidebar; only a small topbar icon + scattered redirects (`legal-ask-wings`, home input). | High — the flagship capability is the least discoverable. |
| P4 | **Express Entry bias contradicts the vision.** | `Questionnaire` is a CRS calculator; `Maple WingmanHome` shows "PR score" as a top-level stat; Landing hero card says "478 CRS". Blueprint: *"never assume Express Entry."* | High — alienates students, workers, refugees, families (the majority). |
| P5 | **No Overview/briefing surface.** | Blueprint E.1 (weather, IRCC news, alerts, holidays, days-since-arrival) is absent; `Maple WingmanHome` covers only nudges. | Medium-High — the daily "why I open the app" reason is missing. |
| P6 | **Voice violates the brand's own rules.** | Landing: "guided by AI", "Powered by Maple AI", "Newcomers in Canada Wingman, reimagined", Assistant subtitle "Powered by Claude". | Medium-High — breaks trust positioning and the banned-word canon. |
| P7 | **Timeline is fragmented.** | Permit-days on Home, PR score on Home + Assessment, citizenship/PR dates only in blueprint. No single timeline. | Medium — the "where am I in my journey" question has no home. |
| P8 | **Settings is a junk drawer.** | One page = identity edit + Maple Wingman config + phone verification + theme + module list. | Medium — mixes account, companion, and connectivity concerns. |
| P9 | **Nudge → destination mismatch.** | Every `Maple WingmanHome` suggestion routes to `/app/assessment` or `/app/jobs`, never opens Maple to *act* on the nudge. | Medium — proactivity that can't be acted on in place. |

---

## 2. User Journey Review (per-page interrogation)

For each page: *Why does it exist? Is this the best place? Does another page already solve part of it? Could it merge? Does it add cognitive load? Can it be contextual? Does it move the journey forward?*

- **Maple WingmanHome** — *Exists* as the daily anchor. *Best place?* Yes, but it's under-powered: it's a nudge feed, not the blueprint's cited briefing. *Merge:* absorb the Overview briefing (weather/news/alerts/holidays) **and** the top of the Immigration Timeline here. *Contextual:* the "Ask Maple Wingman" input should open the real companion with the text preserved, not throw it away.
- **Assistant (`/app/chat`)** — *Why hidden?* No reason. *Merge:* this is not a separate product; it's Maple. Promote it to a **persistent companion dock** available on every app screen, seeded with page context. The standalone full-screen view remains as the "expanded" state.
- **Questionnaire** — *Why CRS-only?* Legacy bias. *Rewire:* generalize into a **Profile Setup** that branches by `arrival_status` + `immigration_category`; CRS becomes **one contextual module** shown only to PR-track users. Preserves the calculator, removes the assumption.
- **Jobs / Accessibilities / Legal / Communities** — *Why exist?* Each is a distinct settlement vertical; all justified. *Merge screens?* No — but they should merge **as a pattern** (one `<ResourceHub>` shell) and each should expose a "**Ask Maple about this**" affordance that carries the vertical's context.
- **Settings** — *Merge:* split into **Profile** (identity + timeline + questionnaire answers) and **Account & Companion** (Maple behavior, WhatsApp, plan, theme, privacy) per blueprint E.6.
- **Admin (all 5)** — Healthy and correctly separated. *Future:* add the blueprint's Weekly Digest / citation-failure view, but not required for the simplification pass.

---

## 3. Improved User Flow

### 3.1 Current flow (as coded)

```
Signup ──► /app (Maple WingmanHome)
             │ stat cards ─────────► /app/assessment (CRS calc)
             │ "Ask Maple Wingman" input ──► /app/chat (loses typed text)
             │ nudge: assessment ──► /app/assessment
             │ nudge: jobs ────────► /app/jobs
             │ nudge: legal ───────► /app/legal
             topbar chat icon ─────► /app/chat  (only real doorway to AI)
Sidebar: Maple Wingman · PR Assessment · Jobs · Get Connected · Legal · Communities · Settings
```
*Symptoms:* AI is a dead-end destination; every "next step" dumps the user into a form; the companion has no memory of where the user came from.

### 3.2 Improved flow (companion-centric, progressive)

```
Signup (language ► entry ► arrival status ► city)  ── 90s, no gating ──►
   /app (Today)  ◄── ONE home: greeting + cited briefing + timeline peek + nudges
       │
       └─ Maple dock (persistent, every screen) ── carries page + profile context
              ├─ acts in place (open renewal steps, draft a checklist)
              └─ expands to full chat when needed

   Resources (progressive-disclosure hub)
       ├─ Jobs        ─┐
       ├─ Connect     ─┤ same shell, each with "Ask Maple about this" → dock pre-seeded
       ├─ Legal & Gov ─┤
       └─ Community    ─┘

   Profile
       ├─ My details (formerly Settings identity + questionnaire answers)
       ├─ Timeline (permit / PR / citizenship — one place)
       └─ Account & Companion (Maple behavior, WhatsApp, plan, privacy, theme)
```

**Navigation depth drops from "7 flat siblings + 1 hidden" to 3 primary destinations (Today · Resources · Profile) with Maple omnipresent.** Every capability is still one tap away; advanced ones (CRS, timeline math, monetization) appear contextually.

- **Problem solved:** eliminates dead-ends and the "which of the 7 tabs?" scan tax.
- **Newcomer benefit:** the app answers "what do I do today?" on open, and the companion is always within reach to help *do* it.
- **Preserves vision:** momentum + one-decision-per-screen; Maple is one continuous companion.
- **Complexity:** Medium (nav shell + dock), High if the full briefing data pipeline is built at once (stage it — see roadmap).

---

## 4. Screens That Should Merge

| Merge | From → To | Problem solved | Newcomer benefit | Vision fit | Complexity |
|---|---|---|---|---|---|
| **M1. One companion** | `Assistant (/app/chat)` + Home "Ask Maple Wingman" input + WhatsApp companion → **one "Maple" surface** (persistent dock ⇄ full view) sharing a single session. | P1/P2/P3: three identities, lost text, hidden chat. | The companion feels like one being that remembers context across app and WhatsApp. | "Maple feels like one continuous companion, never a separate product." | High |
| **M2. Today = briefing + nudges + timeline peek** | `Maple WingmanHome` + (new) Overview briefing + top of Timeline → **`/app` "Today"**. | P5/P7: no briefing, fragmented timeline. | One screen answers "what's true today and what's next." | Overview as the daily anchor; momentum. | Medium (shell) / High (live data) |
| **M3. Resources hub** | `Jobs` + `Accessibilities` + `Legal` + `Communities` → **`/app/resources`** with 4 sub-sections behind one nav item, each rendered by a shared `<ResourceHub>`. | 4 near-identical top-level tabs inflate the nav. | Fewer top-level choices; consistent muscle memory. | Reduce navigation depth without removing capability. | Medium |
| **M4. Profile = identity + timeline + questionnaire answers** | `Settings` (identity part) + `Questionnaire` (stored answers) + Timeline → **`/app/profile`**. | P4/P8: junk-drawer settings, orphaned CRS. | "My situation" lives in one coherent place. | Blueprint E.6 Profile as the control centre. | Medium |
| **M5. Account & Companion** | `Settings` (Maple Wingman + WhatsApp + theme + modules + plan) → **one sub-tab of Profile**. | P8: mixed concerns. | Clear split between "who I am" and "how the app behaves." | Restraint; one concept per surface. | Low |

---

## 5. Components That Should Merge / Consolidate

| Consolidation | Detail | Problem | Benefit | Complexity |
|---|---|---|---|---|
| **C1. `<ResourceHub>` shell** | One component renders header + filter bar + responsive card grid + empty state. Jobs/Legal/Accessibilities/Communities pass data + a card renderer. | 4 pages re-implement the same layout with drift (some use `PageHeader`, some hand-roll headers). | Consistency, less code, one place to improve. | Medium |
| **C2. `<ResourceCard>` + one `primaryAction`** | Unify `job-*`, `legal-*`, `esim-*`, `service-*`, `community-cat-*` cards into one card that accepts exactly one `primaryAction` (blueprint B.2 `<PrimaryAction>` rule). | Five bespoke card styles; multiple CTAs per card in places. | "One decision per screen/card"; visual coherence. | Medium |
| **C3. `<MapleDock>` + `useMaple()`** | Single chat state (session, history, streaming) in context; dock and full view are two presentations of it. Replaces the isolated `Assistant` state and the fake home input. | P2: duplicated/again-lost chat state. | Continuity; typed text never lost; context-seeded. | High |
| **C4. `<StatTile>` / `<TimelineItem>`** | The PR-score / permit-days / pathway tiles on Home and the Landing dashboard preview are re-coded twice; extract one tile + one timeline row. | Duplicated stat UI across Landing + Home. | Single source of truth for "journey stats." | Low |
| **C5. `<CitedItem>` (source chip)** | A shared inline citation chip (`Source · date · ↗`) used by briefing cards, legal cards, and Maple answers. | Blueprint's #1 trust signal (inline citations) is currently absent from the UI. | Makes "we cite everything" visible and reusable. | Low (component) / Medium (wiring data) |
| **C6. Retire the "Maple Wingman" token** | Rename `wings*` UI strings/test-ids to `maple*` (keep backend `wings` service names to avoid churn, or alias). | P1: dual branding. | One name end-to-end. | Low |

---

## 6. Features That Should Become Contextual (Progressive Disclosure)

| Feature | Today | Make it contextual as… | Problem solved | Complexity |
|---|---|---|---|---|
| **CRS / PR score** | Standalone `/app/assessment` + top-level Home stat for everyone. | A **module inside Profile**, and a Today card **only** when `immigration_category` is PR-track (Express Entry / PNP). Students/workers/refugees never see CRS. | P4 Express-Entry bias. | Medium |
| **eSIM marketplace** | Full top-level tab. | Surfaced **on Today for `arrival_status = just_arrived/planning`** ("get connected in your first week"), plus its Resources sub-section. | Restraint; right thing at the right time. | Low |
| **Legal-aid emphasis** | Same for all. | Already refugee-aware in `LegalHelp`/`wings.py` — extend: refugees see "free legal aid" as a **Today priority**; others see it in Resources. | Momentum; specificity. | Low |
| **WhatsApp / phone verification** | A card in Settings. | A **one-time nudge** on Today after first value moment, then it lives in Account & Companion. | Reduces first-run clutter. | Low |
| **Monetization / plans** | Marketing only; tiers not enforced in-app. | Contextual **upgrade prompts** at the natural limit (e.g., companion daily cap, unlimited jobs) per blueprint J. | Aligns app with the revenue model without a pricing wall up front. | Medium |
| **Weather / holidays** | Absent. | **Today briefing** widgets, city-scoped; never a separate screen. | Delivers Overview value contextually. | Medium |

---

## 7. Navigation Redesign

### 7.1 Primary navigation (from 7+1 to 3 + omnipresent companion)

```
┌───────────────────────────────────────────────┐
│  Today        Resources        Profile          │   ← 3 primary
│                                    (Maple dock)  │   ← persistent, every screen
└───────────────────────────────────────────────┘
        │             │                │
     briefing      Jobs             My details
     timeline      Connect          Timeline
     nudges        Legal & Gov      Account & Companion
                   Community
```

- **Today** absorbs Maple WingmanHome + Overview briefing + timeline peek.
- **Resources** is one nav item with 4 in-page sections (Jobs / Connect / Legal & Gov / Community), each a `<ResourceHub>`.
- **Profile** absorbs Settings + questionnaire answers + timeline detail.
- **Maple** is not a tab — it's a docked companion present on all screens, seeded with the current page's context.

**Feature flags still govern visibility:** if `jobs` is off, the Resources sub-tab hides; if all Resources sub-features are off, the nav item hides. The existing `features.js` + `FeatureGate` spine drives this with minimal change.

- **Problem solved:** the 7-way scan tax and the hidden-chat problem.
- **Newcomer benefit:** three obvious doors + a companion always at hand.
- **Vision fit:** reduced depth, merged experiences, power preserved.
- **Complexity:** Medium.

### 7.2 Mobile

Bottom tab bar: **Today · Resources · Maple · Profile** (Maple center, elevated). Matches the blueprint's app-first, tab-bar cross-fade model (H.3).

---

## 8. Areas Causing Cognitive Overload (and the fix)

| Overload source | Fix | Complexity |
|---|---|---|
| **Naming soup** (Maple / Maple Wingman / "Maple AI Assistant · Claude" / MapleJourney). | One name: **Maple** (companion) inside **Maple Journey** (product). Drop "Maple Wingman", "Claude", "AI/IQ" from UI copy. | Low |
| **7 flat sidebar items + a hidden chat.** | 3 primary + docked Maple (§7). | Medium |
| **Home stat cards imply everyone is on Express Entry.** | Contextual stats by `immigration_category`; CRS only for PR-track. | Medium |
| **"Ask Maple Wingman" input that discards your text.** | Wire input into `<MapleDock>` with the text preserved. | Low |
| **Settings doing five jobs.** | Split into Profile / Account & Companion (§4 M4-M5). | Low-Med |
| **Multiple CTAs per card in spots; five card styles.** | `<ResourceCard>` with one `primaryAction` (§5 C2). | Medium |
| **No visible trust/citation layer despite it being the core promise.** | `<CitedItem>` chips inline on briefings, legal, and Maple answers (§5 C5). | Low-Med |

---

## 9. Technical Simplifications

| # | Simplification | Rationale | Complexity |
|---|---|---|---|
| T1 | **Single `useMaple()` chat context** (session, history, stream) consumed by dock + full view; delete the duplicated fetch/session logic in `Assistant.jsx` and the fake home input handler. | One source of truth for companion state; kills P2. | Medium |
| T2 | **`<ResourceHub>` + `<ResourceCard>`** replace 4 bespoke page layouts and 5 card variants. | Less code, consistent behavior, one place to add filters/empty-states. | Medium |
| T3 | **Generalize `Questionnaire` → `ProfileSetup`** with a branch map keyed by `immigration_category`; keep `compute_pr_score` as one branch's module. | Removes Express-Entry assumption without losing the CRS calculator; aligns to blueprint D. | Medium-High |
| T4 | **Promote feature registry to include `today`, `resources`, `profile`, `companion`** as first-class keys so nav + gating stay declarative after the merge. | Keeps the (good) flag-driven nav intact post-restructure. | Low |
| T5 | **Introduce a `sources` collection + `<CitedItem>` contract** (title, url, published_at) so briefing/legal/Maple all read the same shape; enforce the blueprint's citation-required output. | Makes "cite everything" real and testable (regex on AI output, G.3). | Medium |
| T6 | **Consolidate briefing data behind one `/api/today` endpoint** aggregating greeting + nudges + (staged) weather/news/holidays + timeline peek, replacing the single-purpose `/wings/briefing`. | One call powers the home; easier caching; matches Today merge. | Medium |
| T7 | **Copy lint / banned-word check** in CI for the marketing + app strings (AI, GPT, smart, seamless, powered by, intelligent, magic). | Enforces the voice canon automatically; prevents regression. | Low |
| T8 | **Keep JWT auth but align to blueprint's magic-link/OTP later** (phone OTP scaffolding already exists via Twilio in `messaging.py`). Treat as a documented follow-up, not a blocker. | Avoids destabilizing auth now; path already partly built. | Medium (deferred) |

---

## 10. Reusable Design Patterns (the system)

1. **`<ResourceHub>`** — header + optional filter bar + card grid + empty state + "Ask Maple about this". Every settlement vertical uses it.
2. **`<ResourceCard>`** — media/icon, title, meta chips, exactly one `primaryAction`. Enforces B.2.
3. **`<CitedItem>`** — inline source chip (`Source · date · ↗`). The visible trust primitive.
4. **`<MapleDock>` / `useMaple()`** — one companion, two presentations, context-seeded, session-shared with WhatsApp.
5. **`<StatTile>` + `<TimelineItem>`** — journey metrics rendered identically wherever they appear.
6. **`<PageHeader>`** — already exists; standardize *all* pages on it (Jobs/Legal currently hand-roll headers).
7. **`FeatureGate` + `features.js`** — keep as the declarative visibility spine; extend to the new IA.
8. **Motion budget** — adopt blueprint H (≤300ms, cross-fade tabs, no shimmer; note `Maple WingmanHome` uses `mj-shimmer`, which the blueprint bans — replace with flat skeletons).

---

## 11. Final Information Architecture

```
Maple Journey
│
├── Public (marketing)
│   ├── Landing              (rewrite voice: drop AI/IQ/"powered by"; lead with "cited, from IRCC")
│   ├── Features · Resources · Pricing · About
│
├── Auth
│   └── Sign up  (language ► entry ► arrival status ► city)   [magic-link/OTP = follow-up]
│
├── App  (companion-centric)
│   ├── Today            ← briefing (weather/news/alerts/holidays) + timeline peek + Maple nudges
│   ├── Resources        ← one hub, feature-flagged sub-sections:
│   │     ├── Jobs
│   │     ├── Connect (eSIM · banking · transit)
│   │     ├── Legal & Government (+ IRPA s.91 disclosure, cited)
│   │     └── Community (worship · groceries · food banks · shelters · centres · health)
│   ├── Profile
│   │     ├── My details            (identity + situation, formerly Settings + Questionnaire answers)
│   │     ├── Timeline              (permit · PR · citizenship — one place)
│   │     └── Account & Companion   (Maple behavior · WhatsApp · plan · privacy · theme · modules)
│   └── Maple (dock)     ← persistent on every screen; expands to full view; shared session
│
└── Admin  (unchanged spine)
    └── Overview · Users · Feature Toggles · Content · Announcements
        [+ future: Weekly Digest, citation-failure dashboard per blueprint K]
```

- **Problem solved:** collapses 7+1 app surfaces into 3 + companion, gives the timeline a home, restores the daily briefing, and makes trust visible.
- **Newcomer benefit:** fewer decisions, a clear daily anchor, and one companion everywhere.
- **Vision fit:** every blueprint capability is retained; complexity is hidden behind progressive disclosure.

---

## 12. Prioritized Implementation Roadmap

Sequenced so the product *feels* simpler quickly, then deepens. Each phase is shippable.

### Phase 0 — Identity & voice (fast wins) · **Low**
- Retire "Maple Wingman" and "AI/IQ/Powered by/Claude" from UI copy; unify on **Maple / Maple Journey** (§8, C6, T7).
- Wire the home "Ask Maple" input to preserve typed text into chat (§8, precursor to C3).
- Replace `mj-shimmer` with flat skeletons to honor the motion budget.
- **Why first:** near-zero risk, immediately reduces the naming confusion that drives most overload.

### Phase 1 — One companion · **High**
- Build `useMaple()` + `<MapleDock>`; make chat persistent & context-seeded; keep full view as expanded state (M1, C3, T1).
- Promote Maple into the nav model (center on mobile).
- **Why:** delivers the core vision ("one continuous companion") and fixes the hidden-chat + lost-text defects.

### Phase 2 — Navigation & Resources hub · **Medium**
- Introduce **Today / Resources / Profile**; fold Jobs/Connect/Legal/Community into `<ResourceHub>` + `<ResourceCard>` (M3, C1, C2, T2, T4).
- Split Settings → Profile + Account & Companion (M4, M5).
- **Why:** the visible "3 doors instead of 7" simplification.

### Phase 3 — De-bias personalization · **Medium-High**
- Generalize Questionnaire → ProfileSetup branched by `immigration_category`; CRS becomes a PR-track-only module; contextual Today stats (T3, §6).
- **Why:** honors "never assume Express Entry"; serves students/workers/refugees/families properly.

### Phase 4 — Trust & Today briefing · **Medium → High**
- Ship `<CitedItem>` + `sources` contract; add IRPA s.91 disclosure to Legal & Maple (C5, T5).
- Stage the Today briefing: (a) greeting + nudges + timeline peek (now), (b) holidays/weather, (c) IRCC news + alerts via `/api/today` (T6).
- **Why:** makes the "cite everything" promise visible and gives users a daily reason to open the app.

### Phase 5 — Monetization & admin depth (contextual) · **Medium**
- Contextual upgrade prompts at natural limits (companion cap, unlimited jobs) per blueprint J.
- Admin Weekly Digest + citation-failure view per blueprint K.
- **Why:** aligns to the revenue model and the learning loop without adding user-facing complexity.

---

## 13. Success Check

If these ship, a first-time newcomer experiences: **three obvious destinations, one companion that's always there and remembers context, a daily briefing that's specifically theirs, and visible citations that earn trust** — while Jobs, eSIM, Legal, Communities, CRS, WhatsApp, timeline, monetization, and admin **all remain**. Smaller surface area; same (larger, better-organized) power. That is the Apple-style outcome the brief asks for: *the power stays, the complexity disappears.*

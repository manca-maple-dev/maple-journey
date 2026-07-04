# Maple Journey — v2 Product & Integration Blueprint
## Merged with Structure Brief v1

**Document version:** 2.0.0  
**Status:** Specification — Ready for Engineering Review  
**Target scale:** 10,000,000 registered users  
**Prepared:** 2025  

---

## Table of Contents

- [A. Executive Summary](#a-executive-summary)
- [B. Rebrand Pillars](#b-rebrand-pillars)
- [C. Sign-Up Flow](#c-sign-up-flow)
- [D. Questionnaire Schema](#d-questionnaire-schema)
- [E. Page-by-Page Specification](#e-page-by-page-specification)
- [F. Maple Companion Architecture](#f-maple-companion-architecture)
- [G. Grounded-AI System](#g-grounded-ai-system)
- [H. Motion & Launch Animation Spec](#h-motion--launch-animation-spec)
- [I. Data & Scale Architecture](#i-data--scale-architecture)
- [J. Monetization](#j-monetization)
- [K. Admin Console](#k-admin-console)
- [L. Legal & Compliance](#l-legal--compliance)
- [M. Rollout Plan](#m-rollout-plan)
- [N. Acceptance Checklist](#n-acceptance-checklist)

---

## A. Executive Summary

### What This Document Is

This blueprint is the authoritative product and engineering specification for **Maple Journey v2** — the full mobile and web application that the marketing site (governed by Structure Brief v1) advertises and drives downloads toward. The marketing site has its own voice rules, typography canon, motion budget, and conversion targets. This document does **not** replace those constraints; it extends them into the product surface that users inhabit after they click "Download."

Structure Brief v1 establishes: a documentary-journalistic voice ("from IRCC," "cited," "verified"), a strict banned-word list (AI, GPT, smart, seamless, powered by, intelligent, magic), IRPA s.91 disclosure obligations on every government-adjacent surface, Lighthouse ≥ 90 on all four metrics, and a download-first conversion hierarchy. Every one of those constraints carries forward unchanged into this spec.

### What Changes From Structure Brief v1

| Topic | Structure Brief v1 | This Document Adds |
|---|---|---|
| Scope | Marketing site only | The full in-app product |
| Personalization | Implied by "localized briefing" | Defined via 40-field questionnaire schema |
| Companion | Mentioned as concept | Full iMessage + WhatsApp architecture |
| eSIM | Referenced as "Accessibilities" | Partner API comparison table, revenue model |
| Jobs | Referenced | 7 sources, scraping legal risk register, tailoring algorithm |
| Communities | Referenced | OSM + curated dataset hybrid, taste-matching logic |
| Animation | Motion budget rule only | Screen-by-screen keyframe spec |
| Scale | Not addressed | 10M-user stack, cost envelope, replica strategy |
| Monetization | Not addressed | Three subscription tiers, ARPU model |
| Legal | IRPA s.91 only | PIPEDA, Quebec Law 25, AODA, scraping ToS |

### Core Philosophy

Maple Journey is a **companion service for newcomers to Canada** — not a legal firm, not an immigration consultant, not a financial adviser. Every surface must reflect this boundary. The app surfaces verified, cited information and connects users to authoritative institutions. The "Maple" leaf mark that appears throughout the app represents a **grounded advisor** that retrieves real documents and cites them — it does not conjure answers. When it does not know, it says so.

The rebrand targets a user in their first 90 days in Canada: overwhelmed, time-poor, possibly language-limited, navigating multiple bureaucracies simultaneously. Speed, specificity, and restraint are not aesthetic choices; they are welfare requirements.

---

## B. Rebrand Pillars

Six principles, restated from Structure Brief v1 for the app surface. The marketing site expresses these principles through typography and copy; the app expresses them through behaviour, data density, and interaction design.

### B.1 Trust — "We cite everything, claim nothing extra"

Every data point surfaced in the app must have a traceable source. The Overview briefing cites weather from Environment Canada ([weather.gc.ca](https://weather.gc.ca/)), holidays from the provincial scheduler, and news from IRCC's official RSS feed ([api.io.canada.ca/io-server/gc/news/en/v2?dept=departmentof…](https://www.canada.ca/en/immigration-refugees-citizenship/news/rss.html)). Job listings cite the originating board. eSIM plans cite the carrier's published rate card. Legal information cites the statute number and IRCC page URL. The UI must expose citations inline — not buried in a "sources" drawer — because buried citations are not trust signals.

**Concrete example:** On the Legal & Government page, a card about Express Entry draws says: *"Draw #295 — CRS cutoff 491, issued 2025-06-11. Source: IRCC Rounds of Invitations [canada.ca/en/immigration-refugees-citizenship/corporate/mandate/policies-operational-instructions-agreements/ministerial-instructions/express-entry-rounds.html]"* — link is tappable and opens in an in-app browser.

### B.2 Clarity — "One decision per screen"

The app does not aggregate five calls to action on a single screen. The Overview page has one primary action: read more or tap to source. The Jobs page has one primary action per card: deep-link to apply. The Accessibilities page has one primary action: compare and purchase an eSIM plan. This is enforced in the component library as a `<PrimaryAction>` rule: each card component accepts exactly one `primaryAction` prop.

### B.3 Speed — "Perceived load under 1.2 s on a mid-range Android device"

Skeleton screens appear within 150 ms of navigation. Server-side rendering via TanStack Start ([tanstack.com/start](https://tanstack.com/start/latest)) ensures the first meaningful paint lands before JavaScript hydrates. Background workers pre-fetch the next likely page based on tab order. The Jobs page, which aggregates multiple sources, uses incremental streaming: cards stream in as sources resolve, rather than blocking on the slowest scraper.

### B.4 Specificity — "Your city, your visa class, your language"

Maple Journey is useless if it serves Toronto content to a user in Saskatoon, or Express Entry content to someone on a spousal Open Work Permit. The questionnaire (Section D) captures enough signal that every page's agent prompt, every filter default, and every notification targets the user's actual situation. A Syrian refugee claimant and a TN-visa American professional in Vancouver have almost zero overlapping information needs — the app must reflect that.

### B.5 Restraint — "Nothing on screen that is not actionable or informative today"

No decorative illustrations that do not carry content. No loading spinners beyond the initial skeleton. No empty promotional banners. Ad slots on the Overview page are filled with locally relevant newcomer services (transit passes, bank account promotions, SIN appointment services) or left blank — never filled with generic display advertising that a newcomer would find irrelevant or predatory. The motion budget from Structure Brief v1 (no continuous animations, no parallax, all transitions under 300 ms, `prefers-reduced-motion` kills all non-essential animation) applies to every screen.

### B.6 Momentum — "Every interaction should leave the user one step closer to settled"

The app is designed around forward motion. Empty states are never dead ends — they are guides. A user with no jobs matched is shown a prompt to update their NOC code. A user with no eSIM plan is shown the cheapest plan for their destination. A user who hasn't filed for their SIN yet sees a card counting down the days they have left to do so (based on their arrival date from the questionnaire). The Maple companion proactively sends a WhatsApp message when a new IRCC draw happens that matches the user's Express Entry profile.

---

## C. Sign-Up Flow

### C.1 Design Philosophy

Friction at sign-up is the primary cause of drop-off in newcomer apps. Users arrive via the marketing site or word of mouth in a moment of stress. The sign-up flow must be completable in under 90 seconds with zero mandatory fields beyond email or phone number, and must offer a path to the questionnaire immediately after — but not gate the app on questionnaire completion.

### C.2 Screen-by-Screen Breakdown

**Screen 1 — Language Selection**  
Before any account creation, the user selects their preferred language from: English, French, Mandarin (Simplified), Cantonese (Traditional), Tagalog, Hindi, Punjabi, Arabic, Spanish, Portuguese, Korean, Vietnamese, Tamil, Urdu. This selection is stored immediately in `localStorage` (pre-auth) and synced to the user record post-auth. It drives all UI strings and — critically — the language in which the Maple companion responds.

**Screen 2 — Entry Method**  
Three options, vertically stacked:
- **Email with magic link** (recommended — label says "No password to forget")
- **Phone number with OTP** (for users without reliable email access, common among recent arrivals)
- **Passkey / biometric** (for returning users on a new device; shown only if WebAuthn is available)

No social OAuth (Google, Apple Sign-In) in v2.0. Rationale: newcomers frequently share devices, social accounts may be in a foreign-language region, and OAuth introduces a dependency on third-party session management. Passkeys are the long-term trajectory; magic links are the v2 default. Authentication layer: **Supabase Auth** with magic links via SMTP and OTP via Twilio Verify ([twilio.com/docs/verify/api](https://www.twilio.com/docs/verify/api)).

**Screen 3 — Arrival Status**  
Single question, large tap targets:  
*"Where are you in your Canadian journey?"*  
- 🛬 Just arrived (within 90 days)  
- 🗓️ Arrived recently (3–12 months ago)  
- 📋 Planning to arrive  
- 🏠 Settled (1+ years)  

This single field dramatically changes the default content priorities across all five pages and is used immediately — before the questionnaire — to set the Overview briefing baseline.

**Screen 4 — City**  
Type-ahead city selector (top 30 Canadian cities pre-loaded, then open search backed by the Statistics Canada Census Metropolitan Areas list). This field is mandatory because city is the minimum required to serve weather, holidays, and local amenities. Users who select "Planning to arrive" are asked for their intended city.

**Screen 5 — Confirmation + Questionnaire Prompt**  
After email/phone verification:  
*"You're in. Maple needs a few more details to personalize your briefings — takes about 3 minutes."*  
Two CTAs: **"Set up my profile"** (→ questionnaire) and **"Explore first"** (→ Overview page with partial personalization). The questionnaire can be completed any time from the Profile page.

### C.3 Validation Rules

| Field | Validation | Error Copy |
|---|---|---|
| Email | RFC 5322, MX record check | "That address doesn't look right — double-check and try again." |
| Phone | libphonenumber, Canadian prefix preferred but international accepted | "We need a full number with country code." |
| City | Must match known CMA or be flagged as "other" | "We don't recognise that city yet — tap 'other' and we'll do our best." |
| Magic link | Expires in 15 minutes, single-use | "This link has expired. We'll send a fresh one." |

---

## D. Questionnaire Schema

### D.1 Grouping and Purpose

The questionnaire is the personalization backbone. It is presented as a **progressive, conversational flow** — not a form. Each group appears on its own screen with a progress indicator. Completion of each group unlocks richer personalization on specific pages. Fields are individually optional beyond a documented minimum set.

### D.2 Full Field List

#### Group 1 — Identity
| Field | Type | Why It Matters |
|---|---|---|
| `preferred_name` | string | Used in greetings, Maple companion salutations |
| `date_of_birth` | date | Age-gated content (youth programs, senior services) |
| `gender_identity` | enum (Man / Woman / Non-binary / Prefer not to say) | Gendered service filtering (women's shelters, etc.) |
| `pronouns` | string (free text) | Maple companion tone |

#### Group 2 — Immigration Status
| Field | Type | Why It Matters |
|---|---|---|
| `immigration_category` | enum | Master routing variable — determines which agent prompts are loaded |
| `visa_subtype` | enum (depends on category) | E.g., PGWP vs. OWP vs. Spousal; determines CIC processing queue, work authorization |
| `ircc_file_number` | string (optional, encrypted at rest) | Allows tracking of application status via IRCC's GCMS notes guidance |
| `ucis_or_foreign_id` | string (optional, encrypted) | For cross-border workers (TN, H-1B → Canada) |
| `pr_received_date` | date (optional) | Triggers PR milestone reminders (5-year renewal, citizenship eligibility countdown) |
| `citizenship_eligibility_date` | date (computed) | 3 of 5 years rule; surfaced on Profile |
| `work_permit_expiry` | date (optional) | Triggers 6-month, 3-month, 30-day renewal reminders |
| `study_permit_expiry` | date (optional) | Same reminder cadence |

`immigration_category` enum values: `express_entry` | `provincial_nominee` | `spousal_family` | `student` | `temp_foreign_worker` | `refugee_claimant` | `protected_person` | `visitor_work_permit` | `tn_visa` | `other`.

#### Group 3 — Origin
| Field | Type | Why It Matters |
|---|---|---|
| `country_of_birth` | ISO 3166-1 | Source-country-specific community groups, food markets, places of worship |
| `country_of_citizenship` | ISO 3166-1 (array, max 3) | Visa implications; bilateral agreements |
| `languages_spoken` | array of BCP 47 tags | Language filter for jobs, services, community |
| `religion` | enum + "prefer not to say" | Places of worship matching, halal/kosher grocery, religious holidays on Overview calendar |
| `ethnicity_community` | free text (optional) | Cultural grocery matching ("Afro-Caribbean market") |

#### Group 4 — Household
| Field | Type | Why It Matters |
|---|---|---|
| `marital_status` | enum | Spousal program eligibility |
| `spouse_immigration_status` | enum (mirrors immigration_category) | Dual-stream reminders |
| `dependents` | array of `{age: int, school_age: bool}` | Schools, childcare, child benefit (CCB) reminders |
| `household_size` | int (computed) | Food bank eligibility thresholds |

#### Group 5 — Location
| Field | Type | Why It Matters |
|---|---|---|
| `current_city` | CMA code | All page defaults |
| `current_postal_prefix` | FSA (first 3 of postal) | Hyper-local amenity matching |
| `intended_province` | ISO 3166-2:CA | Provincial benefit programs |
| `arrival_date_canada` | date | Days-in-Canada counter, SIN deadline (90 days), MSP/OHIP waiting period start |
| `housing_status` | enum (renting / hotel / shelter / family / own) | Housing resources surfacing |

#### Group 6 — Work
| Field | Type | Why It Matters |
|---|---|---|
| `current_occupation_noc` | NOC 2021 5-digit code | Job feed filtering; NOC codes sourced from Statistics Canada open data ([open.canada.ca/data/dataset/1feee3b5…](https://open.canada.ca/data/dataset/1feee3b5-8068-4dbb-b361-180875837593)) |
| `target_occupation_noc` | NOC 2021 5-digit code (optional) | Career transition job matching |
| `years_experience` | int | Seniority filtering |
| `credentials_country` | ISO 3166-1 | Foreign credential recognition routing |
| `licensing_body` | string | E.g., CPSBC for physicians; surfaces credential recognition pathway |
| `employment_status` | enum (employed / seeking / student / not seeking) | Jobs page priority |
| `work_authorization` | computed from visa_subtype | Open work permit vs. employer-specific |

#### Group 7 — Money
| Field | Type | Why It Matters |
|---|---|---|
| `has_canadian_bank_account` | bool | Surfaces newcomer banking offers |
| `banking_status` | enum (none / basic / full service) | Newcomer bank promotion targeting |
| `has_sin` | bool | SIN application urgency card |
| `credit_history_country` | ISO 3166-1 | Credit transfer programs (e.g., Nova Credit) referral |
| `estimated_monthly_income_cad` | range enum | Food bank / government benefit eligibility |

#### Group 8 — Health
| Field | Type | Why It Matters |
|---|---|---|
| `province_of_residence` | ISO 3166-2:CA | Provincial health plan (MSP in BC, OHIP in ON, RAMQ in QC) |
| `health_coverage_status` | enum (provincial / employer / none / waiting period) | MSP/OHIP waiting period countdown; private insurance referral |
| `has_family_doctor` | bool | Walk-in clinic and virtual care surfacing |

#### Group 9 — Interests & Taste
| Field | Type | Why It Matters |
|---|---|---|
| `cuisine_preferences` | array of tags | Grocery, restaurant, food bank filtering |
| `faith_practice` | enum (mirrors religion, more specific) | Place of worship matching by denomination |
| `community_affiliations` | array of free text | Cultural association surfacing |
| `hobbies` | array of tags | Community event matching (low priority) |

#### Group 10 — Consent Flags
| Field | Type | Legal Basis |
|---|---|---|
| `consent_data_personalization` | bool (default true, must be affirmative) | PIPEDA s.7; required for personalization |
| `consent_maple_companion` | bool | WhatsApp/iMessage opt-in; CAN-SPAM + CASL compliant |
| `consent_marketing_emails` | bool | CASL express consent |
| `consent_aggregated_analytics` | bool | Anonymous platform improvement |
| `data_export_requested` | bool (action) | PIPEDA right of access |
| `deletion_requested` | bool (action) | PIPEDA s.11 right of withdrawal |

### D.3 JSON Schema Sketch

```jsonc
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "UserProfile",
  "type": "object",
  "required": ["user_id", "preferred_language", "current_city", "arrival_status"],
  "properties": {
    "user_id": { "type": "string", "format": "uuid" },
    "preferred_language": { "type": "string", "pattern": "^[a-z]{2}(-[A-Z]{2})?$" },
    "current_city": { "type": "string" },
    "arrival_status": {
      "type": "string",
      "enum": ["just_arrived", "recent", "planning", "settled"]
    },
    "immigration": {
      "type": "object",
      "properties": {
        "category": { "type": "string" },
        "visa_subtype": { "type": "string" },
        "work_permit_expiry": { "type": "string", "format": "date" },
        "pr_received_date": { "type": "string", "format": "date" }
      }
    },
    "work": {
      "type": "object",
      "properties": {
        "current_noc": { "type": "string", "pattern": "^[0-9]{5}$" },
        "target_noc": { "type": "string", "pattern": "^[0-9]{5}$" },
        "licensing_body": { "type": "string" }
      }
    },
    "consents": {
      "type": "object",
      "properties": {
        "personalization": { "type": "boolean" },
        "maple_companion": { "type": "boolean" },
        "marketing": { "type": "boolean" }
      }
    }
  }
}
```

### D.4 Field-to-Page Mapping

| Page | Primary fields consumed |
|---|---|
| Overview | `current_city`, `immigration.category`, `religion`, `arrival_date_canada`, `preferred_language` |
| Jobs | `current_noc`, `target_noc`, `employment_status`, `work_authorization`, `languages_spoken`, `current_city` |
| Accessibilities | `current_city`, `intended_province`, `has_canadian_bank_account` |
| Legal & Government | `immigration.category`, `immigration.visa_subtype`, `province_of_residence`, `health_coverage_status`, `has_sin` |
| Communities | `current_postal_prefix`, `cuisine_preferences`, `faith_practice`, `religion`, `ethnicity_community` |
| Profile | All fields (display + edit) |

---

## E. Page-by-Page Specification

### E.1 Overview — Personalized Daily Briefing

**Purpose:** The first page a user sees every day. Functions as a localized, grounded morning briefing: weather, news, government alerts, upcoming holidays and days-off, and community announcements. Every item is specific to the user's city and immigration status. Nothing is generated without a source.

**Data Sources:**
- **Weather:** Environment and Climate Change Canada API ([weather.gc.ca/api/](https://weather.gc.ca/)), JSON-LD format. No third-party weather middleman — the government source is authoritative and free. Fallback: Open-Meteo ([open-meteo.com](https://open-meteo.com/)) for locations with gaps.
- **IRCC News:** Official IRCC RSS feed ([api.io.canada.ca/io-server/gc/news/en/v2?dept=departmentofimmigration...](https://www.canada.ca/en/immigration-refugees-citizenship/news/rss.html)). Polled every 15 minutes by background worker. Each item is chunked, embedded, and stored in the vector DB. The Overview agent retrieves only items relevant to the user's `immigration_category` and `province_of_residence`.
- **Government Emergency Alerts:** Pelmorex NAAD System ([npas.ca/distributors/naad/](https://npas.ca/distributors/naad/)) — Maple Journey must register as a Last Mile Distributor (LMD) to receive the CAP (Common Alerting Protocol) XML feed. Alerts are filtered by the user's `current_city` geocoordinate bounding box and surfaced as full-width red cards that cannot be dismissed until read.
- **Holidays & Days Off:** Statutory holidays sourced from the Open Government data portal ([open.canada.ca](https://open.canada.ca/data/en/organization/cic)) and provincial scheduler APIs. Religious holidays sourced from HebCal API (Jewish), IslamicFinder calendar export (Islamic), and Calverter (Hindu/Buddhist) — mapped against the user's `religion` field.
- **Ad Slots:** Two per scroll view, max. Ad content is restricted to newcomer-relevant services: bank newcomer offers, transit pass promotions, credential evaluation services, SIN appointment services, language schools. Ads are served via a direct-sold inventory system in v2 — no programmatic DSP, which would introduce GDPR/PIPEDA complexity and predatory ad categories. Ad policy is enforced by the admin console.

**Agent Grounding Strategy:** The Overview agent is a retrieval-augmented summarizer. It receives: (1) user profile slice, (2) retrieved IRCC news chunks, (3) current weather, (4) alert feed. It is instructed to produce a briefing in the user's `preferred_language`, cite every claim, and not add information beyond what was retrieved. Prompt template includes hard stop: *"If you do not have a retrieved source for a claim, do not make the claim."*

**Key Components:**
- `<WeatherCard>` — temperature, precipitation, wind; tap to full forecast
- `<AlertBanner>` — full-width, red, sticky until dismissed with explicit tap
- `<BriefingCard>` — headline + 2-sentence summary + source URL + timestamp
- `<HolidayPill>` — upcoming holidays in a horizontal scroll strip
- `<AdTile>` — max 2, clearly labelled "Sponsored · Newcomer Service"
- `<DaysSinceArrival>` — subtle counter shown to users < 365 days in Canada

**Empty States:** New user with no questionnaire: shows city weather + top 3 IRCC news items + a "Complete your profile to personalize this" banner. No questionnaire = no immigration-specific content.

**Personalization Signals:** `current_city` (weather, alerts), `religion` (holiday calendar), `immigration_category` (IRCC news filter), `arrival_date_canada` (days counter, SIN deadline card), `preferred_language` (all copy).

**Monetization Slots:** 2 ad tiles per session (not per refresh). Ad impressions logged with `ad_tile_impression` telemetry event. Tap logged as `ad_tile_tap`. No auto-play video.

**Telemetry Events:** `overview_load`, `briefing_card_tap`, `alert_dismiss`, `ad_tile_impression`, `ad_tile_tap`, `holiday_strip_scroll`, `weather_card_expand`.

**Edge Cases:** User is in a city without Environment Canada coverage → fallback to Open-Meteo. User has no religion set → secular calendar only. Emergency alert while app is backgrounded → push notification bypassing all rate limits. IRCC RSS unavailable > 15 min → show last-cached items with staleness indicator.

---

### E.2 Jobs — Canadian Employment Discovery

**Purpose:** Surface relevant Canadian job opportunities tailored to the user's NOC code, work authorization, city, and language. Maple Journey is a **discovery layer only** — we deep-link out to the originating board. We do not host job applications, do not store resumes, and do not represent applicants.

**The 7 Sources:**

| Source | Ingestion Method | Legal Basis | Notes |
|---|---|---|---|
| **Job Bank (ESDC)** | Official open data feed — [open.canada.ca/data/en/dataset/ea639e28…](https://open.canada.ca/data/en/dataset/ea639e28-c0fc-48bf-b5dd-b8899bd43072) | Open Government Licence - Canada | **Preferred — use the dataset, not scraping.** Updated daily. Includes NOC 2021 codes natively. |
| **LinkedIn** | No public API for job listings. Scraping violates ToS (hiQ v. LinkedIn notwithstanding). **Do not scrape.** Use LinkedIn's official Job Postings API (partner program required): [linkedin.com/help/linkedin/answer/a415420](https://linkedin.com/help/linkedin/answer/a415420) | Partner agreement | Apply for LinkedIn Jobs API partnership. Reject scraping entirely — legal risk is not worth it. |
| **Indeed CA** | Indeed Publisher Programme ([publisher.indeed.com](https://publisher.indeed.com/)). XML job feed available to approved publishers. No scraping. | Publisher agreement | Apply for publisher status; XML feed is structured and reliable. |
| **Glassdoor** | No public API. Glassdoor's job listings are syndicated via Indeed. Capture via Indeed feed to avoid duplication. | Via Indeed | Glassdoor direct scraping is ToS violation. |
| **Workopolis / Jobillico** | Workopolis is now defunct (acquired, content migrated). Jobillico ([jobillico.com](https://www.jobillico.com/)) offers a partner XML feed for approved aggregators — apply directly. | Partner agreement | Strong for Quebec-based bilingual roles. |
| **Eluta.ca** | Canadian-only aggregator. Offers an employer RSS/XML partnership feed. Email partnership@eluta.ca for partner access. | Partner agreement | Good for mid-market Canadian employers not on Job Bank. |
| **WoodGreen / Immigrant Employment Councils** | Newcomer-specific job boards operated by settlement agencies. Varies by city. Secure RSS or CSV export agreements with: ACCES Employment ([accesemployment.ca](https://accesemployment.ca/)), Immigrant Employment Council of BC, Ontario Immigrant Employment Council. | Partnership / MOU | These are mission-aligned partners, not commercial relationships. |

**Scraping Risk Register:** Any source not above — including direct HTML scraping of Indeed, LinkedIn, or Glassdoor — carries cease-and-desist and CFAA (or Canadian equivalent) risk. The 2022 hiQ v. LinkedIn Circuit Court ruling is U.S. law and does not bind Canadian courts. **Policy: Maple Journey scrapes nothing. All seven sources are accessed via official feeds, partner APIs, or dataset downloads.**

**Tailoring Algorithm:**
1. Filter by `work_authorization` (open permit = all jobs; employer-specific = flag employer-locked postings)
2. Filter by `current_noc` and `target_noc` (exact match + 1-level NOC tree expansion)
3. Filter by `current_city` (radius: 25 km default, user-adjustable to 50 km or "remote")
4. Filter by `languages_spoken` (French-only postings flagged for non-French speakers)
5. Rank by freshness (posted_at desc) — no black-box relevance score in v2
6. Dedup by normalized job title + employer name + city hash (prevents same posting appearing from Job Bank and Indeed)

**Apply-Out UX:** Each card has a single "View & Apply" CTA that opens the originating URL in an in-app browser with a referral parameter for partner tracking. We do not intercept the application. A "Saved" bookmark stores the deep link locally (not on our server — no resume data is handled).

**Empty States:** No NOC code set → prompt to complete questionnaire. No results in city → expand radius prompt. Work permit is employer-specific and listing is for a different employer → card is shown but flagged with "⚠ Verify your work permit allows this employer."

**Telemetry:** `jobs_load`, `job_card_view`, `job_card_apply_tap`, `job_card_save`, `jobs_filter_change`, `jobs_noc_prompt_shown`.

---

### E.3 Accessibilities — eSIM Marketplace & Onboarding Services

**Purpose:** Help newcomers get essential services activated: phone connectivity (eSIM), banking onboarding, transit pass registration. In v2, eSIM is the primary vertical; banking and transit are surfaced as curated links with affiliate context, not full integrations.

#### eSIM Partner Comparison

| Provider | API Docs | Coverage | Revenue Model | Notes |
|---|---|---|---|---|
| **Airalo Partner Platform** | [developers.partners.airalo.com](https://developers.partners.airalo.com/) | 200+ countries; Canada domestic plans available | Reseller margin (typically 15–25% below retail) | REST API, OAuth2 access token (3 req/min, 24h token validity). Order endpoint: `POST /v2/orders`. Best for international data plans for users still roaming. |
| **Gigs** | [developers.gigs.com](https://developers.gigs.com/api/introduction) | 200+ countries, domestic Canada included | SaaS per-subscription fee + carrier margin | Full subscription lifecycle: porting, top-ups, upgrades. OpenAPI 3.1 spec. Best for users who want a primary Canadian number via eSIM. |
| **1GLOBAL (formerly Truphone)** | [docs.connect.1global.com](https://docs.connect.1global.com/apireference/) | Global, strong European + Canada coverage | Wholesale reseller | REST, OAuth. White-label capable. Strong compliance posture. Best for enterprise referrals (employers buying plans for newcomer employees). |
| **Telna** | [telna.com/esim-api](https://telna.com/) | 200+ countries | Reseller | Emerging; competitive on price. Evaluate post-launch. |
| **Canadian MVNOs** (Petro-Canada Mobility, Public Mobile, Lucky Mobile) | No public API — affiliate link only | Canada domestic only | CPA affiliate (typically $25–$75 per activation) | No eSIM API available from these providers as of 2025. Surface as curated links with affiliate tracking, not API integration. Users who want a Canadian number on a budget get a curated comparison table with deep links. |

**Opinionated Recommendation:** Integrate **Airalo** for international/roaming eSIMs (new arrivals still connected to home networks) and **Gigs** for Canadian domestic eSIM plans with a real Canadian number. These two cover 90%+ of newcomer connectivity needs. 1GLOBAL is the enterprise/B2B expansion path. Canadian MVNOs are affiliate links only.

**Component Spec:**
- `<eSIMPlanCard>` — provider logo, data amount, validity, price in CAD, "Get Plan" CTA
- `<ProviderFilterBar>` — tabs: International / Canadian / Compare All
- `<CoverageCheckWidget>` — enter home country or destination, shows compatible plans
- `<ActivationGuide>` — step-by-step eSIM install instructions (device-specific, iOS vs. Android)

**Banking & Transit (v2 — Affiliate Links):**
- Newcomer banking: TD, RBC, Scotiabank, BMO, CIBC all have newcomer banking programs with no-fee periods. Surface comparison table with affiliate deep links (bank affiliate programs are available via CJ Affiliate and Impact.com networks).
- Transit: Presto (ON), Compass (BC), OPUS (QC) — link to each card's sign-up page with newcomer discount information pulled from municipal transit authority pages.

**Monetization:** Airalo reseller margin + Gigs per-subscription fee + Canadian MVNO CPA affiliate. Projected eSIM revenue: $12–$18 per converting user in the first 90 days.

---

### E.4 Legal & Government

**Purpose:** The highest-stakes page in the app. Users make consequential decisions based on what they read here. Every claim must be grounded, cited, and accompanied by the IRPA s.91 disclosure. This page connects users to authoritative sources, government services, legal aid clinics, and newcomer discounts — it does not provide legal advice.

**IRPA s.91 Disclosure Banner** (pinned, non-dismissible on this page):  
> *"Maple Journey provides cited information from government sources. We are not a law firm, immigration consultant, or regulated representative. For advice on your specific application, consult a member of a provincial law society or a registered ICCRC/CICC member. [IRPA s.91 — laws-lois.justice.gc.ca/eng/acts/i-2.5/section-91.html]"*

**Data Sources by Vertical:**

| Vertical | Primary Source | Ingestion |
|---|---|---|
| IRCC Draws & Updates | IRCC RSS + Open Government data ([open.canada.ca/data/en/organization/cic](https://open.canada.ca/data/en/organization/cic)) | Polled every 15 min, embedded |
| CRA / Tax | CRA newsroom RSS ([canada.ca/en/revenue-agency/news/newsroom.html](https://www.canada.ca/en/revenue-agency/news/newsroom.html)) + CRA My Account API (read-only, OAuth, for future auth integration) | Polled daily |
| Service Canada (SIN, EI, CPP) | Service Canada press releases RSS | Polled daily |
| Provincial Services | Province-specific RSS and open data portals (BC, ON, QC, AB, SK, MB) | Polled weekly; low change velocity |
| Legal Aid Clinics | Community Legal Education Ontario ([cleo.on.ca](https://cleo.on.ca/)), Legal Aid BC ([lss.bc.ca](https://lss.bc.ca/)), Aide juridique Québec. No API — curated dataset updated monthly. | Manual curation + quarterly refresh |
| Newcomer Discounts | Bank newcomer program pages, transit authority pages — curated manually, linked with version date | Manual curation |

**Agent Grounding:** The Legal & Government agent receives: (1) user's `immigration_category`, `visa_subtype`, `province_of_residence`, (2) retrieved chunks from the relevant source corpus (IRCC for immigration questions, CRA for tax questions, etc.), (3) hard instruction: *"You must cite the specific page URL for every piece of information. If the user's question falls outside retrieved context, respond: 'I don't have current information on that — please contact IRCC directly at canada.ca/ircc or call 1-888-242-2100.'"*

**Filter & Sort:** User can filter by: Immigration | Tax | Health | Employment | Housing | Discounts. Default sort is by relevance to `immigration_category`. A "What's new this week" section surfaces IRCC changes published in the last 7 days.

**Key Components:**
- `<LegalCard>` — title, 2-sentence summary, source URL, publication date, "Read full source" CTA
- `<DisclaimerBanner>` — IRPA s.91, pinned
- `<AgentChatDrawer>` — slides up from bottom; grounded Q&A with citation requirement; no freeform speculation
- `<DeadlineCard>` — computed from questionnaire (SIN deadline, MSP waiting period end, permit expiry)
- `<LegalAidDirectory>` — city-filtered list of clinics with phone, hours, eligibility notes

---

### E.5 Communities & Help

**Purpose:** Help newcomers find physical and community infrastructure: places of worship, ethnic groceries, food banks, shelters, cultural centres, community organizations. The "Chinese market / African shop / Indian grocery" use case is explicitly primary. This page is taste-aware using questionnaire data.

**Data Sources:**

**OpenStreetMap (OSM) via Overpass API** ([overpass-api.de](https://overpass-api.de/)) is the primary data layer. Rationale over Google Places API:
1. OSM's Overpass API is free with no per-request cost. Google Places API (New) eliminated its $200/month free credit in February 2025 and now bills per field mask request — at 10M users making place searches, Google Places becomes prohibitively expensive.
2. OSM has superior coverage of ethnic grocery stores, places of worship by denomination, food banks, and community centres — categories that commercial datasets underrepresent.
3. OSM data is available under ODbL licence — permissive for this use case.

However, OSM coverage is uneven in smaller cities and for businesses that have recently opened. **Hybrid approach:** OSM as the base layer, supplemented by a **Maple-curated dataset** for the top 15 immigrant-density cities. The curated dataset is maintained by a community data team (a human role in the admin org) who verify and add listings quarterly.

**Taste-Matching Logic:**
- `cuisine_preferences` → maps to OSM `cuisine=*` tags and curated store categories
- `religion` + `faith_practice` → maps to OSM `amenity=place_of_worship` + `religion=*` + `denomination=*`
- `ethnicity_community` → free-text fuzzy match against curated store tags
- Example: user with `religion=islam`, `cuisine_preferences=["halal", "middle_eastern"]`, `current_postal_prefix=M5V` → first results are halal groceries and mosques within 2 km of M5V postal area

**Map Component:** MapLibre GL JS ([maplibre.org](https://maplibre.org/)) with OpenMapTiles as the tile source. No Google Maps SDK dependency. MapLibre is MIT-licensed, OSM tile hosting can be self-managed on Cloudflare R2 for large scale or use a commercial tile provider (Maptiler, Stadia Maps) at manageable cost.

**Categories:**
- 🕌 Places of Worship (by religion, denomination, language of service)
- 🛒 Ethnic Groceries (by cuisine/culture tag)
- 🍱 Food Banks & Meal Programs (with eligibility notes from curated dataset)
- 🏠 Shelters & Housing Help
- 👥 Cultural Centres & Newcomer Organizations
- 💊 Community Health Centres (flagged if interpretation services available)

**Empty States:** City not in curated dataset → OSM-only results with quality disclaimer. No POIs matching taste profile → show generic nearby results + "Help us improve — suggest a place" CTA that writes to a community-submissions Supabase table for admin review.

**Telemetry:** `communities_load`, `place_card_tap`, `map_pin_tap`, `category_filter_change`, `suggest_place_tap`, `directions_tap`.

---

### E.6 Profile

**Purpose:** Display and editing of all questionnaire fields, subscription management, companion settings, data export, and account deletion. This page is the control centre for the user's relationship with Maple Journey.

**Sections:**
1. **My Details** — edit any questionnaire field; changes trigger re-personalization within 60 seconds
2. **Immigration Timeline** — visual countdown: permit expiry, PR eligibility, citizenship eligibility; sourced purely from questionnaire fields, never from external data fetches about the user's case
3. **Maple Companion** — toggle WhatsApp / iMessage; shows connected phone number / Apple ID; manage notification frequency
4. **Subscription** — current tier, upgrade/downgrade, billing history (ChatGPT-style tier cards: Free / Settler / Citizen)
5. **Data & Privacy** — export data (PIPEDA s.8 right of access, delivered as JSON within 30 days), delete account (7-day grace period before hard deletion), consent toggles
6. **App Settings** — language, notification preferences, display (system/light/dark)

---

## F. Maple Companion Architecture

### F.1 What Is the Maple Companion?

The Maple Companion is an out-of-app messaging agent that users interact with via **WhatsApp** or **iMessage (Apple Messages for Business)**. It is represented by the maple-leaf mark (🍁) and named "Maple." It behaves like a Wingman-for-immigration (cf. [getwingman.com](https://getwingman.com)) — a knowledgeable, cited, patient companion that proactively alerts users to changes affecting their case and responds to their questions.

The companion is **not a chatbot with scripted flows**. It is a retrieval-augmented agent with access to the same source corpus as the in-app agents, plus the user's full profile (with consent). Every answer cites a source. Every response includes a footer: *"Maple Journey provides cited information only. For advice on your application, consult a regulated representative."*

### F.2 WhatsApp Business Platform

**Integration path:** WhatsApp Business Platform Cloud API, hosted by Meta — no BSP (Business Solution Provider) required; Maple Journey connects directly.  
**Docs:** [developers.facebook.com/docs/whatsapp/cloud-api/overview/](https://developers.facebook.com/docs/whatsapp/cloud-api/overview/)

**Setup requirements:**
1. Create a Meta Business Account and complete Business Verification (legal entity documents, business phone number, website matching the Meta-registered business)
2. Create a WhatsApp Business Account (WABA) — [developers.facebook.com/docs/whatsapp/business-management-api/get-started/](https://developers.facebook.com/docs/whatsapp/business-management-api/get-started/)
3. Register a dedicated phone number for Maple (e.g., a Canadian toll-free number via Twilio or Vonage, ported to the WABA)
4. Meta Business Verification typically takes 3–7 business days; begin at Week 1 of the rollout plan

**Messaging Limits:** Without verification: 250 business-initiated conversations/day. After Business Verification + approval: tier-based limits scaling to unlimited with volume. In v2 launch, 250/day is sufficient for early adopters; scale trigger is Month 2.

**Session Windows:** WhatsApp enforces a 24-hour customer service window. Within 24 hours of a user message, any template or free-form response is allowed. Outside the window, only approved Message Templates (MTPs) may be sent. Proactive alerts (new IRCC draw, permit expiry warning) must be pre-approved MTPs.

**Template Examples (must be submitted to Meta for approval):**
- `ircc_draw_alert`: *"🍁 New IRCC Express Entry draw: CRS {{1}}, {{2}} invitations issued {{3}}. Tap to see full details: {{4}}"*
- `permit_expiry_reminder`: *"🍁 Reminder: Your {{1}} expires in {{2}} days ({{3}}). Review renewal steps: {{4}}"*

### F.3 iMessage / Apple Messages for Business

**Integration path:** Apple Messages for Business requires selecting an approved Messaging Service Provider (MSP). Maple Journey cannot connect directly to iMessage without an MSP.

**Approved MSPs include:** Quiq ([quiq.com](https://quiq.com/)), LivePerson ([liveperson.com](https://liveperson.com/)), Sinch ([sinch.com](https://sinch.com/)), Nuance. **Recommendation: Sinch** — it supports both WhatsApp Business Platform and Apple Messages for Business under one SDK, reducing routing complexity and vendor count.

**Approval flow:**
1. Register at Apple Business Register ([register.apple.com](https://register.apple.com/resources/messages/messaging-documentation/register-your-acct))
2. Select Sinch as MSP (estimated approval: 30–45 minutes for account creation; 1–4 weeks for Apple review)
3. Configure a business ID tied to the app's bundle ID (so "Business Chat" button appears in iOS search, Maps, Siri)
4. Apple does not charge per message; MSP charges apply (Sinch pricing: metered per message or monthly platform fee)

**MSP Onboarding docs:** [register.apple.com/resources/messages/msp-onboarding](https://register.apple.com/resources/messages/msp-onboarding)

### F.4 Per-User Leaf Identity & Admin Single-Key Model

Each user who opts into the companion is assigned a `companion_session_id` (UUID). The companion system maintains a **conversation context store** in Supabase (encrypted, PII-isolated), keyed by `companion_session_id`. The session stores:
- Last 20 message turns (user + Maple)
- Retrieved chunks from the last 5 queries (for follow-up continuity)
- Profile snapshot (subset of questionnaire relevant to the companion's domain)

**Admin Single-Key Model:** The LLM inference API key is held exclusively by the admin — never exposed to end users, never transmitted to the client. All companion inference happens server-side via a Cloudflare Worker or Supabase Edge Function. Per-user rate limits are enforced at this layer: **20 messages/day on Free tier, 50/day on Settler, unlimited on Citizen.** Rate limit state is stored in Redis (Upstash) keyed by `companion_session_id`.

### F.5 Learning Loop — Aggregated, PII-Safe

Every companion interaction is logged in a `companion_events` table with `companion_session_id` (not `user_id` — deliberately decoupled for PII safety). The event schema:
```json
{
  "session_id": "uuid",
  "turn_index": 3,
  "user_message_embedding": "[1536-dim vector]",
  "retrieved_source_ids": ["ircc-draw-295", "ircc-faq-ee"],
  "response_cited": true,
  "user_follow_up": true,
  "thumbs_down": false,
  "timestamp": "2025-06-15T14:22:00Z"
}
```

User message content is **not stored in plain text** after embedding. The embedding is stored; the raw message is discarded after processing. This satisfies PIPEDA data minimization.

A weekly **Admin Digest** job (Supabase cron, every Sunday 06:00 UTC) runs:
1. Clusters `user_message_embedding` vectors by topic (k-means, k=20)
2. For each cluster, generates a natural-language label: *"472 users asked about PGWP renewal this week"*
3. Identifies the 10 clusters with highest `thumbs_down` rate (unanswered or poorly answered questions)
4. Sends the digest to the admin console (Section K)

### F.6 Law-Change Ingestion Pipeline

When IRCC publishes a new policy bulletin, regulation change, or operational instruction:
1. IRCC RSS feed is polled every 15 minutes by a background worker (Supabase pg_cron or Cloudflare Worker cron trigger)
2. New items are chunked (512 token chunks, 64 token overlap), embedded, and inserted into the vector DB with metadata: `{source: "ircc", published_at, url, category: "policy_change"}`
3. The companion's system prompt is updated to include: *"A new IRCC policy change was published on [date]. When the user asks questions that may be affected by [topic], note this update and cite [URL]."*
4. Proactive WhatsApp MTPs are dispatched to users whose `immigration_category` matches the policy change, filtered by `consent_maple_companion: true`

---

## G. Grounded-AI System

### G.1 Source Registry

Each page's agent has a defined, bounded source registry. Sources outside the registry cannot be cited; retrieval is restricted to indexed chunks from approved sources only.

| Vertical | Approved Sources | Freshness SLA | Embedding Cadence |
|---|---|---|---|
| Overview (news) | IRCC RSS, Environment Canada, Pelmorex NAAD, provincial holiday APIs | 15 min (alerts), 1 hr (news), 24 hr (weather forecast) | On ingest |
| Jobs | Job Bank open data, Indeed feed, Jobillico feed, partner settlement org feeds | 6 hr | On ingest |
| Legal & Government | IRCC open data, CRA newsroom, Service Canada, provincial government portals, legal aid clinic curated dataset | 15 min (IRCC), 24 hr (others) | On ingest |
| Communities | OSM Overpass (weekly tile refresh), Maple curated dataset | 7 days | Weekly batch |
| Maple Companion | All of the above + user profile snapshot | As above | As above |

### G.2 Retrieval Stack

**Vector Database:** **pgvector** on Supabase Postgres (extension enabled). At 10M users and ~500K embedded chunks (estimated corpus), pgvector with an HNSW index handles this comfortably without a dedicated vector DB service. At 5M+ chunks, migrate to Qdrant (self-hosted on a dedicated VM) for better ANN performance at scale. The threshold trigger is > 2M chunks or p95 retrieval latency > 150 ms.

**Embedding Model:** OpenAI `text-embedding-3-small` (1536 dimensions, $0.02/1M tokens) for the initial corpus and all new ingest. At 10M users scale, evaluate switching to a self-hosted model (e.g., BGE-large via Ollama on a dedicated GPU instance) to reduce per-query cost.

**Retrieval Pipeline per Query:**
1. Embed user query → 1536-dim vector
2. `SELECT ... ORDER BY embedding <=> query_vector LIMIT 10` from pgvector, filtered by `source_registry` whitelist and `freshness_cutoff`
3. Cross-encoder rerank top 10 → top 3 (using Cohere Rerank API: [cohere.com/rerank](https://cohere.com/rerank) or a self-hosted cross-encoder)
4. Top 3 chunks passed to LLM with instruction: *"Answer using only the provided context. Cite the source URL for every claim. If the answer is not in the context, say: 'I don't have verified information on that — please check [authoritative URL].'"*

### G.3 Citation-Required Output Contract

Every agent response **must** include at least one citation in the form `[Source: {URL}, published {date}]`. The response parser validates this regex before delivery. If the regex fails (no citation found), the response is replaced with a fallback: *"I wasn't able to find a verified answer to that. Please check IRCC directly: canada.ca/ircc."* This fallback is logged as a `citation_failure` event for admin review.

### G.4 Hallucination Guardrails

- **Context stuffing:** System prompt always includes: *"You are Maple, a grounded information advisor for newcomers to Canada. You have access ONLY to the following retrieved context. Do not add information not present in the context."*
- **Refusal patterns:** Hard-coded refusal triggers for: specific legal advice ("Should I submit my application?"), financial advice ("Should I invest in…"), medical diagnosis. These trigger the canned redirect response.
- **Confidence floor:** If retrieval returns 0 chunks with cosine similarity ≥ 0.75, the agent does not attempt to answer and serves the fallback response.

### G.5 Evaluation Harness

A monthly automated evaluation run uses a curated set of 200 test questions (50 per vertical) with known correct answers drawn from official sources. Each question is run through the full retrieval + generation pipeline. Metrics tracked:
- Citation accuracy (% responses with valid URL that resolves to claimed content)
- Refusal rate on out-of-scope questions (target: 100%)
- Hallucination rate (% responses containing claims not in retrieved context, assessed by a second LLM judge)
- p95 latency from query to response delivery

---

## H. Motion & Launch Animation Spec

All animations obey the Structure Brief v1 motion budget: no transition > 300 ms, no continuous animations, no parallax, `prefers-reduced-motion` kills all non-essential animation.

### H.1 App Open Sequence (Cold Launch)

**Total duration:** 1,400 ms (or 0 ms if `prefers-reduced-motion`)

| Frame | Duration | Description |
|---|---|---|
| 0–200 ms | 200 ms | Solid maple-red (`#C41E3A`) splash background, no content |
| 200–600 ms | 400 ms | Maple leaf outline traces itself via `stroke-dashoffset` animation (SVG, 24×24 dp, eased with `cubic-bezier(0.22, 1, 0.36, 1)`). Fill floods inward from the stem. |
| 600–900 ms | 300 ms | Wordmark "Maple Journey" fades up (`opacity: 0 → 1`, `translateY: 8px → 0`). Tagline beneath: *"Your Canadian beginning, briefed."* |
| 900–1100 ms | 200 ms | Background transitions from maple-red to the app's surface colour (`#F9F7F4` light / `#0F0F0F` dark). Leaf and wordmark remain. |
| 1100–1400 ms | 300 ms | Leaf mark shrinks to tab-bar size and flies to its resting position in the header. Page content fades in behind it. |

`prefers-reduced-motion` override: skip directly to the wordmark visible on the surface colour at frame 0. Total duration: 0 ms.

### H.2 Personalized Greeting Reveal (First Load After Questionnaire)

After the questionnaire is completed, the next Overview load plays a one-time greeting:
- The `<WeatherCard>` slides up first (150 ms, `translateY: 24px → 0`, `opacity: 0 → 1`)
- Then the greeting: *"Good morning, [preferred_name]. Here's today's briefing for [city]."* — each word fades in sequentially with a 30 ms stagger (total: ~600 ms for a 20-word sentence)
- Only plays once. Stored in `localStorage` as `greeting_shown: true`.

### H.3 Page Transitions

Tab-bar navigation: **cross-fade** with `opacity: 0 → 1` over 220 ms. No sliding. No scale. Rationale: sliding implies directionality that tab bars do not have; cross-fade is cognitively neutral and reduces motion sickness risk.

Modal / sheet presentation: Standard iOS bottom sheet spring (`spring(mass: 0.8, stiffness: 300, damping: 28)`). On Android: Material `BottomSheetBehavior` at `PEEK_HEIGHT` 0 with `expandedOffset` 0.

### H.4 Skeleton → Content Reveal

Skeletons use a single-colour flat fill (`#E8E3DC` light / `#2A2A2A` dark) — **no shimmer animation** (shimmer violates the motion budget as a continuous animation). Content replaces skeletons via opacity cross-fade (180 ms). If content arrives in < 150 ms (cache hit), skeleton is skipped entirely.

---

## I. Data & Scale Architecture for 10M Users

### I.1 Stack Choices

| Layer | Choice | Rationale |
|---|---|---|
| Frontend framework | **TanStack Start** ([tanstack.com/start](https://tanstack.com/start/latest)) | Full-stack SSR, TanStack Router, typed route tree, server functions, Vite-based build, adapters for Cloudflare Workers and Node. RC-stable as of 2025 with strong momentum (14M+ weekly downloads on router). |
| Database | **Supabase (Postgres + pgvector)** | Managed Postgres with pgvector for retrieval, Row Level Security for user data isolation, Realtime for live updates (alert banner), Edge Functions for serverless compute. Pro/Enterprise plans support read replicas ([supabase.com/docs/guides/platform/read-replicas](https://supabase.com/docs/guides/platform/read-replicas)). |
| Read Replicas | 3 replicas: ca-central-1 (primary), us-east-1, eu-west-2 | Canadian primary ensures PIPEDA data residency. US replica for diaspora users. EU replica for planning-stage users still in Europe. |
| Auth | Supabase Auth (magic link + OTP via Twilio Verify) | Integrated with Postgres RLS, passkey support via WebAuthn. |
| File Storage | Supabase Storage (backed by S3-compatible object storage) | User data exports, curated dataset CSVs |
| Edge / CDN | **Cloudflare** (Workers + R2 + Cache API) | Workers handle rate limiting, webhook fanout, eSIM API proxying. R2 for OSM tile storage (zero egress cost). Cache API for weather/holiday responses. |
| Vector DB | **pgvector** (HNSW index) until 2M chunks, then **Qdrant** | pgvector is sufficient and eliminates an external dependency for v2. Qdrant migration is a defined scaling gate, not a surprise. |
| Background Workers | Supabase pg_cron + Cloudflare Workers cron triggers | RSS polling, Job Bank dataset refresh, companion digest job |
| Message Queue | **Upstash Redis** (serverless, per-request billing) | Rate-limit counters for companion, webhook dedup, job dedup |
| Mobile | React Native (Expo) sharing TanStack Router primitives | Code-share with web for data layer and routing types. Expo EAS for OTA updates and build pipeline. |
| Push Notifications | Expo Notifications (APNs + FCM) | Emergency alert bypass, companion message notifications |
| Analytics / Telemetry | **PostHog** (self-hosted or cloud) | PIPEDA-compliant, EU/CA data residency option, session recording with PII masking |
| Error Monitoring | Sentry | Standard; Expo Sentry SDK |
| LLM Inference | OpenAI API (admin-held key, server-side only) | No user-facing key exposure. Rate limit per user enforced at Edge. |
| Embedding | OpenAI `text-embedding-3-small` | Cost: ~$0.02/1M tokens. At 500K chunks of 512 tokens average, initial index cost ≈ $5. |
| Reranking | Cohere Rerank API | $1/1000 searches. At 10M users × 3 searches/day = 30M/day = $30,000/day at scale — switch to self-hosted cross-encoder at 1M daily active users. |

### I.2 Cost Envelope Estimate (at 10M registered, ~500K DAU)

| Line Item | Monthly Cost Estimate |
|---|---|
| Supabase Enterprise (primary + 3 replicas, 32 CPU, 128 GB) | ~$2,500 |
| Cloudflare Workers + R2 + Cache | ~$500 |
| OpenAI inference (companion + retrieval) | ~$8,000 (assumes 10 calls/DAU/day avg) |
| Cohere Rerank (at 500K DAU × 3 queries) | ~$1,500 (or $0 after self-hosted migration) |
| Twilio Verify (OTP) | ~$1,000 |
| Expo EAS + push | ~$500 |
| WhatsApp Cloud API | $0 (Meta charges per conversation template, ~$0.005–$0.014 per conversation) → ~$500 at 50K companion conversations/month |
| Sinch (iMessage MSP) | ~$800 at estimated volume |
| Upstash Redis | ~$200 |
| PostHog cloud | ~$400 |
| Sentry | ~$200 |
| **Total estimated** | **~$16,100/month at 500K DAU** |

At $4–$6 ARPU/month from subscriptions + eSIM + affiliate (see Section J), break-even is approximately 3,200–4,000 paying users — achievable within 3 months of launch.

### I.3 Data Residency

All primary Postgres data is stored in `ca-central-1` (AWS Canada). Read replicas are additive, not substitutive — writes always go to the Canadian primary. Supabase Enterprise contracts include data processing agreements. This satisfies PIPEDA's accountability principle for cross-border transfers.

---

## J. Monetization

### J.1 Subscription Tiers

| Feature | Free | Settler ($6.99/mo) | Citizen ($14.99/mo) |
|---|---|---|---|
| Overview briefing | ✅ | ✅ | ✅ |
| Jobs discovery | ✅ (10 cards/day) | ✅ (unlimited) | ✅ (unlimited) |
| eSIM marketplace | ✅ (browse) | ✅ (purchase) | ✅ (purchase + white-glove setup guide) |
| Legal & Government cards | ✅ (5/day) | ✅ (unlimited) | ✅ (unlimited) |
| Communities | ✅ | ✅ | ✅ |
| Maple Companion (WhatsApp/iMessage) | ❌ | ✅ (50 msgs/day) | ✅ (unlimited) |
| Proactive law-change alerts | ❌ | ✅ (weekly digest) | ✅ (real-time) |
| Immigration timeline tracker | ❌ | ✅ | ✅ |
| Data export | ✅ | ✅ | ✅ |
| Ad-free Overview | ❌ | ✅ | ✅ |
| Priority companion response | ❌ | ❌ | ✅ (< 10 s vs. < 30 s) |

### J.2 eSIM & Affiliate Revenue

- **Airalo reseller margin:** 15–25% on each eSIM package sold. At average $15 CAD package price × 20% margin = $3.00/converting user.
- **Gigs per-subscription fee:** Negotiated wholesale; target $2–$5/active subscription/month.
- **Canadian MVNO CPA:** $25–$75/activation via CJ Affiliate or direct bank affiliate programs.
- **Bank newcomer offers:** $50–$150 CPA per successful account opening (TD, RBC newcomer programs have affiliate arrangements available).

### J.3 Ad Inventory

Free tier Overview shows 2 ad tiles per day. Ads are **direct-sold only** in v2 — no programmatic DSP. Ad categories permitted: banking, telecommunications, credential evaluation (WES, IQAS), language schools, government-adjacent services. Minimum CPM: $12 (premium newcomer demographic). At 500K DAU free users × 2 impressions × $12 CPM = ~$12,000/day = ~$360,000/month from ad inventory at scale.

### J.4 Projected ARPU

| Cohort | Est. % Users | Revenue/User/Month |
|---|---|---|
| Free (ad-supported) | 70% | $0.24 (ad revenue share) |
| Settler | 22% | $6.99 |
| Citizen | 8% | $14.99 |
| eSIM + affiliate (all users) | 15% converting | $3–$5 one-time |
| **Blended ARPU** | | **~$4.20/user/month** |

---

## K. Admin Console

### K.1 Purpose

The admin console is a private web dashboard (same TanStack Start codebase, protected route, admin role in Supabase RLS) for the Maple Journey operations team. Its primary purpose is to surface insights from the Maple learning loop and allow the team to improve the product without looking at individual user data.

### K.2 Weekly Digest View

Every Monday morning, the console shows:
- **Top 10 question clusters** from the companion (clustered by embedding similarity): topic label, volume, % with `thumbs_down`, example phrasing (generated, not a real user message)
- **Citation failure rate by vertical** — which verticals had the most fallback responses (signal of corpus gaps)
- **Source freshness dashboard** — which RSS/API sources haven't updated in > 48 hours (potential integration failure)
- **New law changes ingested this week** — list of IRCC/CRA items with category tags

### K.3 Content Moderation Queue

- Community-submitted place suggestions (from the Communities page) appear here for review before publication
- Flagged companion responses (user-reported) appear here with anonymized context for quality review

### K.4 Ad Management

Direct-sold ad campaigns managed here: flight dates, creative upload, placement (which cities/immigration categories see which ads), impression cap, CTR reporting.

### K.5 Operational Alerts

- Companion error rate > 5% in rolling 1 hour → PagerDuty
- IRCC RSS feed silent > 30 min → Slack alert
- Supabase connection pool > 80% saturation → Slack alert
- eSIM API (Airalo/Gigs) error rate > 2% → Slack alert

---

## L. Legal & Compliance

### L.1 IRPA s.91 — Immigration Representation

Section 91(1) of the *Immigration and Refugee Protection Act* ([laws-lois.justice.gc.ca/eng/acts/i-2.5/section-91.html](https://laws-lois.justice.gc.ca/eng/acts/i-2.5/section-91.html)) prohibits anyone not licensed (lawyer, notary, or CICC/ICCRC member) from representing or advising a person for consideration in connection with an immigration proceeding or application.

Maple Journey's position: **we provide information, not advice.** The distinction is:
- ✅ "IRCC requires 12 months of full-time skilled work experience for CEC eligibility. [Source: IRCC, canada.ca/…, updated 2025-06-01]" — this is information.
- ❌ "Based on your situation, you should apply for CEC" — this is advice and is prohibited.

The IRPA s.91 disclosure banner appears on every Legal & Government screen, every Maple Companion session start, and in the app's Terms of Service. The CCRC's May 2025 FAQ ([ccrweb.ca/sites/ccrweb.ca/files/2025-05/CCR_FAQs_S91_2025.pdf](https://ccrweb.ca/sites/ccrweb.ca/files/2025-05/CCR_FAQs_S91_2025.pdf)) notes IRCC's updated interpretation — Maple Journey legal counsel must review this document before launch and update the disclosure language accordingly.

### L.2 PIPEDA & Quebec Law 25

**PIPEDA** ([priv.gc.ca/en/privacy-topics/…/pipeda_brief/](https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/pipeda_brief/)) applies to all private-sector commercial activities in Canada. Key obligations:
- Meaningful consent before collection (questionnaire consent group)
- Purposes must be disclosed at or before collection (Privacy Policy, plain language)
- Right of access (data export, 30-day delivery SLA)
- Right of withdrawal (account deletion, 7-day grace period)
- Security safeguards appropriate to sensitivity

**Quebec Law 25** (Act to Modernize Legislative Provisions as Regards the Protection of Personal Information) applies to any organization processing personal information of Quebec residents. Additional requirements beyond PIPEDA:
- Privacy by default: strictest privacy settings must be the default. Maple Journey must default all optional consents to `false`.
- Privacy impact assessments (PIA) required before deploying any technology that processes personal information (the AI/companion system requires a PIA before Quebec launch)
- Explicit consent for sensitive information — religion, health status, immigration status are all "sensitive" under Law 25. Each field in those questionnaire groups requires a separate, granular consent toggle.
- Data localization preference: Law 25 does not mandate in-province storage but requires written safeguard agreements for cross-border transfers. Supabase's data processing agreement + `ca-central-1` primary satisfies this.

### L.3 CASL (Canadian Anti-Spam Legislation)

All commercial electronic messages (including proactive companion WhatsApp messages about new IRCC draws) require **express consent** — checked via the `consent_maple_companion` and `consent_marketing_emails` flags. Consent records must be retained indefinitely. An unsubscribe mechanism must be included in every commercial message and must function within 10 business days.

### L.4 Accessibility — AODA & WCAG 2.2 AA

The *Accessibility for Ontarians with Disabilities Act* (AODA) applies to any digital product serving Ontario residents. As Maple Journey serves all of Canada, **WCAG 2.2 Level AA** is the baseline for the app and marketing site.

Key requirements:
- All images have `alt` text; decorative images have `alt=""`
- Tap targets minimum 44×44 dp
- Colour contrast minimum 4.5:1 for normal text, 3:1 for large text (the maple-red `#C41E3A` on white passes 5.2:1)
- All interactive elements keyboard-navigable and focus-visible
- Screen reader testing with VoiceOver (iOS) and TalkBack (Android) before each release
- The MapLibre map component must include a list-view fallback for screen reader users (map pins are not accessible to screen readers)
- Time-limited content (emergency alerts) must not auto-dismiss; must be manually dismissed

### L.5 Scraping ToS Considerations

As documented in Section E.2, Maple Journey **does not scrape any job board**. All data sources are official feeds, partner APIs, or open government datasets. This is both an ethical and a legal position. The Job Bank Terms of Use ([jobbank.gc.ca/termsofuse-seeker.xhtml](https://www.jobbank.gc.ca/termsofuse-seeker.xhtml)) permits use of the public dataset; scraping the HTML interface is not required. LinkedIn's ToS explicitly prohibits automated scraping by non-authorized parties.

---

## M. Rollout Plan — 8-Week Phased Build

### M.1 Phase Overview

| Phase | Weeks | Focus | Gate to Next Phase |
|---|---|---|---|
| 0 — Setup | 1 | Repo, CI/CD, Supabase project, Apple MfB + Meta WA Business verification submitted | Verification submissions confirmed |
| 1 — Core Auth & Questionnaire | 2–3 | Sign-up flow, magic link, questionnaire schema, Supabase RLS, Profile read/write | Sign-up + questionnaire completable end-to-end |
| 2 — Overview & Data Pipelines | 3–4 | Weather, IRCC RSS, holidays, alerts pipelines; Overview page with skeletons; NAAD LMD registration | Overview renders with live data in staging |
| 3 — Jobs Page | 4–5 | Job Bank open data ingestion, Indeed publisher XML, Jobillico partner feed; Jobs page with filter | 7-source jobs page functional, dedup working |
| 4 — Accessibilities | 5–6 | Airalo partner API integration, Gigs API integration, eSIM comparison UI; banking/transit affiliate links | eSIM purchase flow end-to-end in sandbox |
| 5 — Legal & Communities | 6–7 | Legal agent + IRCC source corpus; OSM Overpass integration; curated dataset v1 (top 5 cities); Communities map | Both pages functional with grounded agent |
| 6 — Maple Companion | 7–8 | WhatsApp Cloud API webhook + send; iMessage via Sinch; per-user leaf routing; law-change pipeline; admin digest job | Companion sends and receives on both channels |
| 7 — Polish & Launch | 8 | Launch animations, motion QA, accessibility audit, Lighthouse audit, penetration test, IRPA disclosure review, soft launch (TestFlight + Play Store internal) | All acceptance checklist items green |

### M.2 Dependencies & Critical Path

- Apple Messages for Business approval (1–4 weeks) — **start Week 1**; it is the longest external dependency
- Meta Business Verification (3–7 days) — **start Week 1**
- Airalo Partner API access request — **start Week 1** (requires business documentation)
- Gigs API key — **start Week 1**
- Job Bank open data: available immediately via open.canada.ca (no approval)
- Indeed Publisher Programme: 1–2 week approval — **start Week 1**
- NAAD LMD registration with Pelmorex: contact alerts@pelmorex.com — **start Week 2**; 1–3 week setup

### M.3 Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Apple MfB approval delayed > 4 weeks | Medium | High | Launch WhatsApp-only companion; iMessage as v2.1 feature |
| IRCC RSS feed structure changes | Low | Medium | Abstract RSS parser behind adapter; unit-test feed shape weekly |
| eSIM API partner rejects application | Low | High | Airalo and Gigs both have self-serve partner programs; rejection is unlikely if entity is legitimate |
| Companion inference cost exceeds budget | Medium | Medium | Per-user rate limits + context window truncation; switch to cheaper model for Free tier |
| Quebec Law 25 PIA delays Quebec launch | Medium | Low | Launch in other provinces first; Quebec launch gated on PIA completion |
| Job board partner feed quality is poor | Medium | Medium | Job Bank open data is always the fallback; other sources are additive |
| pgvector retrieval latency degrades at scale | Low | Medium | HNSW index + read replicas; Qdrant migration path is pre-planned |

---

## N. Acceptance Checklist

Format mirrors Structure Brief v1 §07.

### N.1 Sign-Up & Questionnaire
- [ ] Sign-up completable in < 90 seconds with email or phone only
- [ ] Magic link expires in 15 minutes and is single-use
- [ ] Questionnaire skippable; app is functional with city + arrival_status only
- [ ] All questionnaire consent fields default to `false` (Quebec Law 25 privacy-by-default)
- [ ] IRPA s.91 disclosure present in Terms of Service and Legal page

### N.2 Overview Page
- [ ] Weather data sourced from Environment Canada or Open-Meteo fallback; source cited in card
- [ ] IRCC RSS items filtered by `immigration_category`; each card links to source URL
- [ ] Emergency alert cards are full-width, red, non-dismissible until tapped
- [ ] No Overview content claims something that is not in a retrieved, cited source
- [ ] Ad tiles capped at 2 per session; labelled "Sponsored · Newcomer Service"
- [ ] `prefers-reduced-motion` disables all animations including skeleton shimmer (shimmer is not used anyway)

### N.3 Jobs Page
- [ ] Zero HTML scraping; all sources via official feed, open dataset, or partner API
- [ ] Dedup logic removes duplicate listings from multiple sources
- [ ] "View & Apply" deep-links to originating board, not to Maple Journey application form
- [ ] Work-authorization mismatch warning shown on employer-specific permit cards

### N.4 Accessibilities Page
- [ ] Airalo Partner API (`POST /v2/orders`) functional in sandbox before production
- [ ] Gigs subscription creation (`POST /subscriptions`) functional in sandbox
- [ ] eSIM plan prices displayed in CAD with date of last refresh
- [ ] eSIM install guide shown post-purchase, device-aware (iOS / Android)

### N.5 Legal & Government Page
- [ ] IRPA s.91 disclosure banner is pinned, non-dismissible
- [ ] Every agent response includes at least one cited URL (regex validated before delivery)
- [ ] Citation failure fallback redirects to IRCC contact page, not to a generated answer
- [ ] Legal aid clinic directory filtered by `province_of_residence`

### N.6 Communities Page
- [ ] OSM Overpass query returns results in < 2 seconds for top 15 cities (cached)
- [ ] Map has accessible list-view fallback for screen reader users
- [ ] "Suggest a place" submissions go to admin review queue, not directly to production

### N.7 Maple Companion
- [ ] WhatsApp MTP templates approved by Meta before proactive sends
- [ ] iMessage channel live via Sinch MSP (or companion launches WhatsApp-only if delayed)
- [ ] User raw message content not stored after embedding (PII minimization)
- [ ] Per-user rate limits enforced: 20/day Free, 50/day Settler, unlimited Citizen
- [ ] Companion session starts with IRPA s.91 disclosure
- [ ] Admin weekly digest generated every Sunday without manual intervention

### N.8 Grounded-AI System
- [ ] Source registry enforced: no out-of-registry URL can be cited
- [ ] Hallucination guardrail: confidence floor of cosine similarity ≥ 0.75 enforced
- [ ] Monthly evaluation harness run produces citation accuracy ≥ 95%, refusal rate = 100% on out-of-scope questions
- [ ] Reranking in production (Cohere or self-hosted cross-encoder)

### N.9 Motion & Animation
- [ ] Cold-launch sequence total duration ≤ 1,400 ms
- [ ] `prefers-reduced-motion` reduces cold launch to 0 ms (wordmark shown immediately)
- [ ] No page transition exceeds 300 ms
- [ ] No continuous animation on any screen (no shimmer, no looping, no parallax)
- [ ] Greeting reveal plays exactly once per account lifetime

### N.10 Performance & Accessibility
- [ ] Lighthouse scores ≥ 90 on Performance, Accessibility, Best Practices, SEO (web surfaces)
- [ ] First Meaningful Paint ≤ 1.2 s on a Moto G Power (mid-range Android baseline) on 4G
- [ ] All tap targets ≥ 44×44 dp
- [ ] Colour contrast ≥ 4.5:1 for all body text
- [ ] VoiceOver (iOS) and TalkBack (Android) tested on every page before each release

### N.11 Legal & Privacy
- [ ] PIPEDA data access request (export) delivered within 30 days of request
- [ ] Account deletion executes within 7-day grace period with no residual PII in primary DB
- [ ] Quebec Law 25 PIA completed before Quebec-resident targeting
- [ ] CASL unsubscribe mechanism in every commercial companion message, functional within 10 business days
- [ ] All data at rest encrypted (Supabase AES-256); all data in transit via TLS 1.3

### N.12 Admin Console
- [ ] Weekly companion digest generated by Sunday 08:00 ET without manual intervention
- [ ] Source freshness dashboard shows red for any source silent > 48 hours
- [ ] Community place suggestion queue accessible and actionable
- [ ] PagerDuty alert fires on companion error rate > 5% in rolling 1 hour

---

*End of Maple Journey v2 Product & Integration Blueprint.*  
*Document maintained in /docs/blueprint-v2.md in the product monorepo. Version-control history is the source of truth for changes. All external URLs were verified at time of writing; re-verify before engineering sprint kickoff.*

---

# Addendum A — Audience Scope Lock (post-review clarification)

**Effective:** supersedes any broader audience mention earlier in this document.

Maple Journey serves **five audiences only**. Any feature, questionnaire branch, agent knowledge base, or Jobs filter that references anything outside this list is out of scope for v2.

| # | Audience | Canonical status codes |
|---|---|---|
| 1 | **Visitors** | Visitor Record, Super Visa, eTA-entry visitors |
| 2 | **Students** | Study Permit holders (incl. co-op work permit, PGWP applicants) |
| 3 | **Workers** | Open Work Permit, Employer-Specific (LMIA-backed), IMP work permits, PGWP holders |
| 4 | **Refugees / Protected Persons** | Convention refugees, Protected Persons, refugee claimants, PRRA applicants, resettled refugees (GAR/PSR/BVOR) |
| 5 | **Permanent Residents** | New PRs (landed ≤ 5 yrs), PR card renewal cohort, PR sponsors of family |

## Explicitly out of scope for v2
- Express Entry pool strategy, CRS score optimization, profile ranking
- Provincial Nominee Program *strategy* (we still surface PNP info as reference under Legal & Government, but no "which PNP should I pick" advisor)
- Citizenship test prep (defer to v3)
- Business/Investor immigration streams
- Any pathway selection advice for people not yet in Canada beyond the Visitor/Student/Worker/Refugee/PR pre-arrival prep

## Impact on prior sections

**Questionnaire (§D):** `immigration_status` enum is locked to exactly `{visitor, student, worker, refugee, permanent_resident}`. Remove any "prospective applicant / EE candidate" option. Sub-questions branch off these five only.

**Overview (§E.1):** Personalized briefings pull deadlines relevant to the user's status only — e.g. study permit expiry, work permit renewal windows, PR card renewal, refugee claim hearing dates, IFHP coverage windows. Never surface EE draw results.

**Jobs (§E.2):** Postings are filtered by work eligibility derived from the user's permit type:
- Visitors → hidden (Jobs tab shows "Your visitor status doesn't permit work in Canada. Here's what you can do to prepare." with links to Legal & Government).
- Students → on/off-campus rules surfaced; only postings within permitted hours flagged as compliant.
- Workers → employer-specific permit holders see a warning on postings outside their authorized employer/NOC.
- Refugees → work-permit-pending users get a "You may be eligible for an open work permit" advisor card linking to IRCC form IMM 5710.
- PRs → unrestricted.

**Legal & Government (§E.4):** Agent knowledge scope trimmed to:
- Status maintenance & extensions (visitor extension, study permit extension, work permit renewal, PR card renewal)
- IFHP (refugees) & provincial health coverage waiting periods
- Refugee claim process, hearing prep, PRRA, H&C basics (referral to legal aid, never advice)
- SIN application, CRA newcomer filing, benefits (CCB, GST/HST credit)
- Family sponsorship basics for PRs
- Provincial services (driver's licence exchange, MSP/OHIP/RAMQ enrolment)

Remove: EE profile creation, CRS calculators, PNP eligibility quizzes, Investor/Start-up Visa content.

**Maple Companion (§F):** System prompt gets a hard scope guardrail:

```
You serve visitors, students, workers, refugees, and permanent residents in Canada.
If asked about Express Entry, CRS scores, PNP selection strategy, Investor Visa,
or Start-up Visa, respond: "That's outside what Maple covers. For pathway
selection, an RCIC or immigration lawyer is the right call — try the CBA
referral service or Legal Aid in your province." Do not attempt to answer.
```

**Grounded-AI registry (§G):** Retire any source feed exclusively about EE draws (e.g. `ircc.canada.ca/english/immigrate/skilled/rounds.asp`). Keep IRCC operational-bulletins feeds, CRA newcomer pages, provincial ministry feeds, IFHP updates, and refugee-support NGO feeds.

**Monetization (§J):** Ad inventory on Overview must not accept immigration-consultant or "get PR faster" ads — brand-safety filter required. eSIM, banking, transit, and settlement-service ads only.

**Acceptance checklist addition (§N):**
- [ ] Grep repo for `express entry`, `CRS`, `PNP strategy`, `investor visa`, `start-up visa` — zero product-copy hits (reference mentions in Legal directory allowed).
- [ ] Questionnaire enum has exactly 5 status values.
- [ ] Jobs page renders the correct empty/warning state for each of the 5 audiences.
- [ ] Maple companion refuses EE/CRS/PNP-strategy prompts in eval harness.

End of Addendum A.

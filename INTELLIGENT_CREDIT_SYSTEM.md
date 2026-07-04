"""Intelligent Credit System for Maple Chat
==============================================

A nuanced credit metering system that replaces the blunt daily-message counter.

ARCHITECTURE
============

Tier Pricing:
- Free tier:   10 credits/day, metered (blocks chats when depleted)
- Plus tier:   150 credits/day, unlimited in practice
- Family tier: 300 credits/day, unlimited in practice

Daily Auto-Regeneration:
- First message of each calendar day automatically refills credits
- Atomic operation (only runs once per day per user)
- Tracked in wallet via last_daily_refill timestamp

Query Complexity Classifier (Intelligent Cost):
Instead of "1 credit per message", we classify by complexity:
  1 credit  = Simple (greetings, yes/no, one-word answers)
  2 credits = Standard (single-topic immigration question)
  3 credits = Research (multi-step, timeline, eligibility check)
  5 credits = Deep (full case analysis, CRS calc, strategy)

Classification uses NLP regex patterns:
- Simple: matches "Hi", "Thanks", "OK", "?", etc.
- Deep:   matches "calculate", "full analysis", "CRS score", "strategy", "appeal", etc.
- Research: matches "how long", "deadline", "express entry", "work permit", etc.
- Standard: everything else

CREDIT FLOW
===========

User sends chat message:
  ↓
1. Classify query complexity → cost (1-5 credits)
2. Check if user is free-tier (metered)
3. If metered:
   - Auto-refill if first message of day (add 10 credits)
   - Check balance >= cost
   - If insufficient: block chat, show upsell
4. Debit cost from wallet (atomic)
5. Process chat (Claude response)
6. Store ledger entry (audit trail)
7. Return response with credit headers
8. If balance is critically low: append upsell nudge

Credit Headers (sent to frontend):
- X-Maple-Credits: current balance after debit
- X-Maple-Cost: cost of this message
- X-Maple-Complexity: classification (simple/standard/research/deep)

DATABASE
========

credit_wallets collection:
{
  "_id": ObjectId,
  "id": UUID,
  "user_id": ObjectId,
  "balance": 8,
  "lifetime_earned": 20,
  "lifetime_spent": 12,
  "tier": "free",
  "last_daily_refill": "2026-07-04",
  "created_at": "2026-07-01T12:00:00Z",
  "updated_at": "2026-07-04T08:15:00Z"
}

credit_ledger collection (append-only):
[
  {
    "id": UUID,
    "user_id": ObjectId,
    "kind": "grant" | "debit",
    "amount": 10,
    "reason": "daily-refill" | "chat-standard" | "signup-starter",
    "meta": { "tier": "free", "complexity": "standard", ... },
    "created_at": "2026-07-04T08:15:00Z"
  },
  ...
]

API ENDPOINTS
=============

GET /api/companion/credits
  Returns current wallet summary with metering status.
  Response:
  {
    "balance": 8,
    "tier": "free",
    "lifetime_earned": 20,
    "lifetime_spent": 12,
    "daily_limit": 10,
    "last_daily_refill": "2026-07-04",
    "refilled_today": true,
    "metering_active": true,
    "policy": "subscription-first: paid tiers are unlimited"
  }

GET /api/companion/credits/classify?message="..."
  Preview cost BEFORE sending. Lets UI show "This will cost 3 credits".
  Response:
  {
    "complexity": "research",
    "cost": 3,
    "balance": 8,
    "can_afford": true,
    "metered": true
  }

GET /api/companion/credits/history?limit=50
  Full audit trail of all credits earned/spent.
  Response: Array of ledger entries with timestamps.

POST /api/assistant/chat
  Send message to Maple. Deducts credits (if metered).
  Request: { "message": "...", "session_id": "..." }
  Response headers include X-Maple-Credits, X-Maple-Cost, X-Maple-Complexity.
  Response body includes optional upsell nudge at end (if balance < 3).

USAGE SCENARIOS
===============

Scenario 1: Free user, typical day
  Morning (08:00): Send "Hi" → Classify: simple (1 credit) → Balance: 9 (was 10)
  Later (14:00): Send "How do I qualify for PR?" → Classify: standard (2) → Balance: 7
  Evening (20:00): Send "Calculate my CRS score" → Classify: deep (5) → Balance: 2
  Alert shown: "You have 2 credits remaining. Upgrade to Plus for 150/day."

Scenario 2: Free user runs out
  (At end of day, balance = 0)
  Send: "What is an open work permit?" → Cost: 3 credits
  Response: "You need 3 credits but have 0. Refills tomorrow or upgrade to Plus."

Scenario 3: Plus user (metered=false)
  - All credit operations skipped
  - No balance checking
  - Unlimited chats
  - X-Maple-Credits header still sent (for UI awareness) but doesn't gate

UPSELL MECHANICS
================

Balance > 2: No nudge
Balance = 2: Yellow nudge: "You have 2 credits left. Upgrade for 150/day."
Balance <= 0: Red block: "All credits used. Upgrade to Plus."

Nudge includes:
- Current situation ("You have X credits")
- Value prop ("Plus: 150 credits/day")
- CTA ("Tap Upgrade")

ANALYTICS & METRICS
====================

From credit_ledger, we can compute:
- Daily active users (distinct user_ids)
- Total credits issued vs consumed
- Churn risk (users running out daily)
- Feature adoption (deep analysis usage)
- Upsell effectiveness (% of out-of-credits users who upgrade)
- Revenue per user (map consumed credits to LTV)

Example queries:
  db.credit_ledger.aggregate([
    { $match: { created_at: { $gte: ISODate("2026-07-01") } } },
    { $group: { _id: "$user_id", spent: { $sum: "$amount" } } },
    { $sort: { spent: -1 } }
  ])
  // Top spenders (power users who do deep analysis)

IMPLEMENTATION NOTES
====================

1. Atomic Operations:
   - Use MongoDB atomic updates (find_one_and_update) to prevent race conditions
   - Debit only succeeds if balance >= cost (no overdraft)
   - Daily refill only happens once per calendar day (last_daily_refill check)

2. Timezone Handling:
   - All timestamps are UTC (datetime.now(timezone.utc))
   - Daily refill triggered on first message of calendar day (date.today().isoformat())
   - Handles timezone-aware clients correctly

3. Fallback for Non-LLM:
   - If LLM provider fails, response is grounded fallback
   - Credits still deducted (user consumed request bandwidth)
   - Ledger entry recorded for debugging

4. Integration with chat.py:
   - Query classified before LLM call
   - Credits checked/deducted before processing
   - Response includes credit headers
   - Upsell nudge appended to response (if needed)

5. Frontend Integration:
   - Call GET /companion/credits/classify before sending
   - Show cost in UI ("This will cost 3 credits")
   - Disable send button if insufficient credits
   - Display balance in header/widget
   - Handle 402 Payment Required response (if we add that status)

TESTING
=======

Unit tests (test_credits.py):
  ✅ classify_query: various message types → correct cost
  ✅ ensure_wallet: creates wallet with correct starter balance
  ✅ auto_refill_daily: refills only once per day
  ✅ debit_credits: atomic debit with balance check
  ✅ grant_credits: adds credits + ledger entry
  ✅ upsell_nudge: returns correct nudge based on balance

Integration tests:
  ✅ POST /assistant/chat with metered user → deducts credits
  ✅ GET /companion/credits → returns correct balance
  ✅ GET /companion/credits/classify → predicts cost correctly
  ✅ Free user runs out → blocks next message
  ✅ Plus user → no credit checks
  ✅ Ledger audit trail → all entries recorded

MIGRATION PATH (from old system)
================================

Old: Message counter (daily limit: 10 messages)
New: Credit system (daily limit: 10 credits, variable cost 1-5)

Migration steps:
  1. Create credit_wallets & credit_ledger collections
  2. For each existing user: create wallet with "free" tier, balance = 10
  3. Update chat.py: replace message counter with classify_query + debit
  4. Add companion_ops endpoint with /companion/credits endpoints
  5. Update frontend: add credit meter, show cost preview
  6. Monitor: check daily churn, upgrade conversion

FUTURE ENHANCEMENTS
====================

1. Referral Bonuses: +5 credits for each friend referred
2. Quiz Rewards: +3 credits for completing settlement quiz
3. Social Sharing: +2 credits per blog post shared
4. Loyalty Multipliers: 1.2x credits for users 6+ months active
5. Seasonal Promotions: Double credits during December
6. Competitive Pricing: Dynamic pricing based on demand (surge pricing)
7. Credit Expiry: Credits expire after 90 days (force engagement)
8. Credit Marketplace: Pay per credit (micro-transactions)
9. Enterprise Plans: Fixed monthly cost (unlimited everything)
10. API Credits: Separate tier for Maple API consumers

COMPLIANCE & PRIVACY
====================

- All credit transactions logged for tax purposes
- Ledger entries immutable (audit trail)
- User can request data export (PIPEDA)
- Free tier users get upgrade reminders (max 1/day)
- No dark patterns (clear pricing, easy cancellation)
- Plus/Family tier auto-renews with 14-day cancellation window
"""

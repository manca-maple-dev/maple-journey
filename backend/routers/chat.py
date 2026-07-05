"""Maple AI chat — RAG-grounded OpenAI generation, persisted per session.

Implements the 'Sovereign Authority' + 'Omniscience' pattern: every response is grounded in
retrieved IRCC/IRPA documents with mandatory deep-linked citations, augmented by Live Web
Search when internal knowledge relevance is insufficient.

Model: OpenAI chat model with parameters optimized for legal reasoning:
- Max Tokens: 4096 (full-depth legal analysis with citations)
- Top-P: 0.92 (focused but not overly deterministic — allows nuanced legal interpretation)
- Temperature: 0.3 (low creativity, high factual precision for immigration law)

Free tier is credit-metered daily; paid tiers get unlimited chats and deeper,
profile-aware guidance with full RAG retrieval + Omniscience Live Web Search.
"""
import os
import uuid
import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from core.db import db, clean
from core.config import SOVEREIGN_SYSTEM_PROMPT, PAID_TIERS, CHAT_RETENTION_DAYS
from core.security import get_current_user
from models import ChatIn
from services.companion_memory import CompanionMemory
from services.profile import profile_summary, conversation_language_instruction
from services.rag import (
    rag_search,
    enforce_citation_policy,
    grounded_fallback_response,
    attach_verified_citations_if_missing,
)
from services.credits import (
    ensure_wallet, auto_refill_daily, debit_credits, wallet_summary,
    classify_query, upsell_nudge, should_meter_tier,
)
from services.prompt_security import (
    detect_injection_attempt,
    sanitize_query,
    filter_response_for_leaks,
    check_rate_limit,
)
from services.community_rag import build_community_context

logger = logging.getLogger("maplejourney.chat")
router = APIRouter(tags=["chat"])
companion_memory = CompanionMemory(db)


def _env_value(*keys: str) -> str:
    """Return the first non-empty environment variable value with loose normalization."""
    for key in keys:
        raw = os.environ.get(key)
        if not raw:
            continue
        value = raw.strip().strip('"').strip("'")
        if value:
            return value
    return ""


async def _openai_chat_response(system_prompt: str, user_message: str) -> str:
    """Direct OpenAI fallback when EMERGENT routing is unavailable.

    Keeps Maple chat usable with OPENAI_API_KEY only.
    """
    openai_key = _env_value(
        "OPENAI_API_KEY",
        "OPENAI_KEY",
        "OPENAI_API_TOKEN",
        "EMERGENT_LLM_KEY",
    )
    if not openai_key:
        return ""
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=openai_key)
        preferred = _env_value("OPENAI_CHAT_MODEL") or "gpt-4.1"
        candidates = []
        for m in [preferred, "gpt-4o-mini", "gpt-4o"]:
            if m not in candidates:
                candidates.append(m)
        last_error = None
        for model in candidates:
            try:
                resp = await client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS,
                    top_p=TOP_P,
                )
                text = (resp.choices[0].message.content or "").strip()
                if text:
                    return text
            except Exception as model_err:
                last_error = model_err
                logger.warning("openai model failed: %s", model)
                continue

        if last_error:
            logger.exception("openai fallback failed across all models", exc_info=last_error)
        return ""
    except Exception:
        logger.exception("openai fallback failed")
        return ""


async def _anthropic_chat_response(system_prompt: str, user_message: str) -> str:
    """Secondary fallback when OpenAI is unavailable."""
    anthropic_key = _env_value("ANTHROPIC_API_KEY")
    if not anthropic_key:
        return ""
    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=anthropic_key)
        model = _env_value("ANTHROPIC_CHAT_MODEL") or "claude-3-5-sonnet-latest"
        resp = await client.messages.create(
            model=model,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        chunks = []
        for block in getattr(resp, "content", []) or []:
            if getattr(block, "type", "") == "text" and getattr(block, "text", ""):
                chunks.append(block.text)
        return "\n".join(chunks).strip()
    except Exception:
        logger.exception("anthropic fallback failed")
        return ""


def _retention_cutoff_iso(tier: str):
    """ISO timestamp before which chats are hidden for this tier (None = keep all)."""
    days = CHAT_RETENTION_DAYS.get(tier, CHAT_RETENTION_DAYS["free"])
    if days is None:
        return None
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

# ---------------------------------------------------------------------------
# Model Configuration — Super-Intelligence Tier
# Optimized for legal reasoning: high precision, full depth, focused distribution
# ---------------------------------------------------------------------------
MODEL_PROVIDER = "anthropic"
MODEL_NAME = "claude-sonnet-4-6"  # Highest tier: Claude Sonnet 4.6
MAX_TOKENS = 4096               # Full legal analysis depth with room for citations
TOP_P = 0.92                     # Focused distribution — legal reasoning needs precision
TEMPERATURE = 0.3                # Low temperature for factual accuracy in law


def _quality_directive(complexity: str, tier: str) -> str:
    """Return response-quality instructions tuned to query complexity.
    
    OPTIMIZED FOR COST-EFFICIENCY + BEST COMPANION EXPERIENCE:
    - Minimize token usage without sacrificing quality
    - Use smart response tiers based on user tier
    - Prioritize actionable, concise reasoning
    """
    
    # COST OPTIMIZATION: Base directive emphasizes efficiency
    base = (
        "\n\nCOMPANION QUALITY FRAMEWORK (COST-OPTIMIZED):\n"
        "Your response should feel like advice from a trusted mentor—thoughtful but efficient.\n"
        "Never waste tokens on unnecessary elaboration. Every sentence should earn its place.\n\n"
        
        "STRUCTURE (Optimized for 500-1000 words max):\n"
        "1. DIRECT ANSWER: Lead with the immediate answer (1-2 sentences)\n"
        "2. WHY IT MATTERS: Explain the legal/practical reasoning (2-3 sentences)\n"
        "3. YOUR NEXT STEP: Specific action they take this week (numbered, 3-5 items)\n"
        "4. RISK WARNING: One critical mistake to avoid\n"
        "5. WHAT HAPPENS NEXT: The phase after this one (1-2 sentences)\n\n"
        
        "TONE (Professional, Warm, Efficient):\n"
        "• Use concrete details, not abstractions\n"
        "• Cite sources with deep links (but don't explain the citation)\n"
        "• Define terms once, briefly, inline\n"
        "• Use sub-headings to make it scannable\n"
        "• Example: 'Under IRPR R.189, you maintain implied status during processing.' "
        "(Not: 'There is a regulation called IRPR R.189 which states that...')\n\n"
        
        "LENGTH TARGET (By Tier):\n"
        "• Free tier: 400-600 words (efficient, direct)\n"
        "• Plus tier: 600-900 words (deeper reasoning)\n"
        "• Family tier: 900-1200 words (comprehensive, proactive)\n"
        "DO NOT exceed 1200 words. Quality > Length.\n\n"
    )
    
    # Tier-specific optimizations
    if tier == "free":
        base += (
            "FREE TIER OPTIMIZATION:\n"
            "• Give the direct answer immediately\n"
            "• Include only the essentials: legal basis, action steps, one risk warning\n"
            "• Deep links to 2-3 authoritative sources\n"
            "• Skip alternatives; recommend the best path only\n"
            "• Focus on this week's action, not future scenarios\n"
            "• Omit emotional framing; keep it factual\n"
            "TARGET: 400-600 words, maximum impact per token\n\n"
        )
    elif tier in {"plus", "premium"}:
        base += (
            "PLUS/PREMIUM TIER OPTIMIZATION:\n"
            "• Include the reasoning framework: 'Here's the legal basis... Here's why it matters... Here's what you do...'\n"
            "• Provide 2-3 realistic options with trade-offs\n"
            "• Surface 2-3 hidden risks/opportunities\n"
            "• Anticipate the next phase after this one\n"
            "• Include actionable alternatives\n"
            "TARGET: 600-900 words, deeper companion experience\n\n"
        )
    elif tier == "family":
        base += (
            "FAMILY TIER OPTIMIZATION:\n"
            "• Maximum depth: provide scenario branches, tactical alternatives, risk ranking\n"
            "• Proactive prescience: surface the next challenge before they ask\n"
            "• Provide a 3-month roadmap: this month → next month → preparation phase\n"
            "• Deep legal analysis with citations\n"
            "• Emotional intelligence: acknowledge their situation warmly\n"
            "TARGET: 900-1200 words, VIP companion experience\n\n"
        )
    
    # Complexity-specific optimizations
    if complexity == "simple":
        base += (
            "SIMPLE QUERY OPTIMIZATION:\n"
            "• Answer directly (1 sentence)\n"
            "• Explain why briefly (1-2 sentences)\n"
            "• Action steps (2-3 items)\n"
            "• Done. No elaboration.\n"
            "TARGET: 200-300 words maximum\n\n"
        )
    elif complexity in {"standard", "research"}:
        base += (
            "STANDARD/RESEARCH OPTIMIZATION:\n"
            "• Direct answer + reasoning (3-4 sentences)\n"
            "• Decision branches if relevant (2-3 options max)\n"
            "• Action plan (5-7 numbered steps)\n"
            "• Risk warning (specific, actionable)\n"
            "• Next phase preview (1-2 sentences)\n"
            "TARGET: 600-900 words\n\n"
        )
    elif complexity == "deep":
        base += (
            "DEEP QUERY OPTIMIZATION:\n"
            "• Comprehensive analysis: legal basis + procedural flow + timeline + risks\n"
            "• Scenario comparison: 'If you do X... If you do Y... I recommend X because...'\n"
            "• Proactive insights: surface hidden deadlines, policy changes, next challenges\n"
            "• Minimal document checklist: 5-7 key documents with one-line reason each\n"
            "• Processing timeline with what happens at each stage\n"
            "TARGET: 900-1200 words\n\n"
        )
    
    # COST CONTROL RULES (Critical)
    base += (
        "COST CONTROL RULES:\n"
        "✓ Reuse information from retrieved context (don't rephrase)\n"
        "✓ Cite URLs directly without explanation\n"
        "✓ Use bullet points instead of paragraphs where possible\n"
        "✓ Define terms once, inline, in 1-2 words\n"
        "✓ Remove redundancy: don't repeat the question\n"
        "✓ Omit generic disclaimers ('I'm an AI', 'Please consult a lawyer')\n"
        "✓ Use abbreviations after first mention (IRPA, PGWP, CRS)\n"
        "✓ Stop at 1200 words; never exceed\n\n"
        
        "BEST COMPANION MARKERS:\n"
        "✓ Opens with empathy if appropriate ('I know this is confusing')\n"
        "✓ Ends with hope/confidence ('Here's the good news')\n"
        "✓ Gives concrete next action (not 'contact IRCC' but '[Phone], wait times 45 days')\n"
        "✓ Acknowledges trade-offs honestly\n"
        "✓ Shows logical reasoning, not just rules\n"
    )
    
    return base


@router.get("/assistant/history")
async def assistant_history(session_id: str, user: dict = Depends(get_current_user)):
    tier = user.get("tier", "free")
    q = {"user_id": str(user["_id"]), "session_id": session_id}
    cutoff = _retention_cutoff_iso(tier)
    if cutoff:
        q["created_at"] = {"$gte": cutoff}
    items = await db.chat_messages.find(q).sort("created_at", 1).to_list(500)
    return [clean(i) for i in items]


@router.get("/assistant/usage")
async def assistant_usage(user: dict = Depends(get_current_user)):
    """Credit balance + usage info so the UI can render the credit meter."""
    tier = user.get("tier", "free")
    uid = str(user["_id"])
    metered = should_meter_tier(tier)
    summary = await wallet_summary(uid, tier=tier)
    return {
        "tier": tier,
        "metered": metered,
        "unit": "credits",
        "balance": summary["balance"],
        "daily_limit": summary["daily_limit"],
        "lifetime_earned": summary["lifetime_earned"],
        "lifetime_spent": summary["lifetime_spent"],
        "last_daily_refill": summary["last_daily_refill"],
        "refilled_today": summary["refilled_today"],
        "retention_days": CHAT_RETENTION_DAYS.get(tier, CHAT_RETENTION_DAYS["free"]),
        # Legacy compat fields
        "unlimited": not metered,
        "limit": summary["daily_limit"],
        "remaining": summary["balance"] if metered else None,
    }


@router.post("/assistant/chat")
async def assistant_chat(body: ChatIn, user: dict = Depends(get_current_user)):
    if body.session_id:
        session_id = body.session_id
    else:
        session_id = await companion_memory.resolve_channel_session(str(user["_id"]), channel="web")
    uid = str(user["_id"])
    now = datetime.now(timezone.utc).isoformat()
    tier = user.get("tier", "free")
    metered = should_meter_tier(tier)

    # === SECURITY CHECK 1: Prompt Injection Detection ===
    is_attack, attack_reason = await detect_injection_attempt(body.message)
    if is_attack:
        exceeded_limit, attempt_count = await check_rate_limit(uid, datetime.now(timezone.utc).timestamp())
        
        if exceeded_limit:
            # Too many injection attempts - block user temporarily
            logger.warning(f"User {uid} blocked due to repeated injection attempts")
            await db.chat_messages.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": uid,
                "session_id": session_id,
                "role": "assistant",
                "content": "🛡️ We detected unusual activity on your account. For security, please contact support.",
                "created_at": now,
                "security_event": "rate_limited_injection"
            })
            
            return StreamingResponse(
                (i async for i in ["🛡️ Security check: Please contact support."]),
                media_type="text/plain",
                headers={"X-Maple-Security": "rate-limited"}
            )
        
        # Log and reject single injection attempt
        logger.warning(f"Injection attempt blocked for user {uid}: {attack_reason}")
        safe_response = "I'm here to help with immigration and settlement questions. How can I assist you today? 🍁"
        
        await db.chat_messages.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": uid,
            "session_id": session_id,
            "role": "user",
            "content": body.message,
            "created_at": now,
        })
        await db.chat_messages.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": uid,
            "session_id": session_id,
            "role": "assistant",
            "content": safe_response,
            "created_at": now,
            "security_event": "injection_blocked"
        })
        
        return StreamingResponse(
            (i async for i in [safe_response]),
            media_type="text/plain",
            headers={"X-Maple-Security": "attempt-blocked"}
        )
    
    # === SECURITY CHECK 2: Input Sanitization ===
    sanitized_message = sanitize_query(body.message)

    # --- Intelligent credit gate (metered tiers only) ---
    complexity, cost = classify_query(sanitized_message)
    credit_balance = 0

    if metered:
        # Ensure wallet exists and auto-refill if first message of the day
        await ensure_wallet(uid, tier=tier)
        await auto_refill_daily(uid, tier=tier)
        wallet = await db.credit_wallets.find_one({"user_id": uid}) or {}
        credit_balance = int(wallet.get("balance", 0))

        if credit_balance < cost:
            await db.chat_messages.insert_one({"id": str(uuid.uuid4()), "user_id": uid, "session_id": session_id, "role": "user", "content": sanitized_message, "created_at": now})
            limit_msg = (
                f"You need **{cost} credit{'s' if cost != 1 else ''}** for this question "
                f"({complexity} complexity) but your balance is **{credit_balance}**. "
                "Your credits refill automatically tomorrow, or upgrade to **Plus** for 150 credits/day. "
                "🍁 Tap **Upgrade** in your dashboard."
            )
            await db.chat_messages.insert_one({"id": str(uuid.uuid4()), "user_id": uid, "session_id": session_id, "role": "assistant", "content": limit_msg, "created_at": datetime.now(timezone.utc).isoformat()})

            async def limited():
                yield limit_msg

            return StreamingResponse(
                limited(), media_type="text/plain",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no",
                         "X-Session-Id": session_id, "X-Maple-Limit": "insufficient-credits",
                         "X-Maple-Credits": str(credit_balance), "X-Maple-Cost": str(cost)}
            )

    common_headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "X-Session-Id": session_id,
        "X-Maple-Credits": str(credit_balance),
        "X-Maple-Cost": str(cost),
        "X-Maple-Complexity": complexity,
    }

    # Debit credits before processing (atomic — wallet already checked above)
    if metered:
        debit_result = await debit_credits(uid, cost, reason=f"chat-{complexity}", meta={"session_id": session_id, "complexity": complexity})
        if not debit_result.get("ok"):
            limit_msg = (
                f"You need **{cost} credit{'s' if cost != 1 else ''}** for this question "
                f"({complexity} complexity) but your balance is **{debit_result.get('balance', 0)}**. "
                "Your credits refill automatically tomorrow, or upgrade to **Plus** for more daily credits."
            )
            await db.chat_messages.insert_one({"id": str(uuid.uuid4()), "user_id": uid, "session_id": session_id, "role": "assistant", "content": limit_msg, "created_at": datetime.now(timezone.utc).isoformat()})

            async def limited_after_debit():
                yield limit_msg

            return StreamingResponse(
                limited_after_debit(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                    "X-Session-Id": session_id,
                    "X-Maple-Limit": "insufficient-credits",
                    "X-Maple-Credits": str(debit_result.get("balance", 0)),
                    "X-Maple-Cost": str(cost),
                },
            )
        credit_balance = debit_result.get("balance", 0)
        common_headers["X-Maple-Credits"] = str(credit_balance)

    await db.chat_messages.insert_one({"id": str(uuid.uuid4()), "user_id": uid, "session_id": session_id, "role": "user", "content": body.message, "created_at": now})

    # --- RAG Retrieval + Omniscience Engine: ground the response in authoritative documents ---
    rag_context = await rag_search(body.message, user)
    community_context = await build_community_context(
        body.message, 
        province=user.get("profile", {}).get("province"),
        city=user.get("profile", {}).get("city")
    )
    memory_context = await companion_memory.build_memory_brief(session_id)

    # Build the sovereign system prompt with profile + RAG context + live web data
    system = SOVEREIGN_SYSTEM_PROMPT + profile_summary(user) + memory_context + community_context + rag_context
    system += _quality_directive(complexity, tier)
    system += conversation_language_instruction(user)
    system += (
        "\n\nLEGAL/GOVERNMENT RESPONSE RULES:\n"
        "- If the user is asking about law, permits, PR, citizenship, legal aid, hearings, or government benefits, answer with official-source-first reasoning.\n"
        "- State the province-specific rule when the user's profile provides a province.\n"
        "- Prefer the newest official source in context and mention if the rule was last verified recently.\n"
        "- Do not generalize across provinces when the rule differs by province.\n"
    )

    if tier in PAID_TIERS:
        system += (
            "\n\nThis user is on a paid plan. Provide MAXIMUM depth: full legal references, "
            "step-by-step procedural checklists with specific form numbers and URLs, anticipate "
            "their next hurdle based on their profile, and proactively surface deadlines or "
            "eligibility windows they may not have asked about. Maintain sovereign authority "
            "in every response. Use the Omniscience Live Web Data when available for the most "
            "current 2026 information on processing times, fees, and policy changes. "
            "When providing community/resource recommendations, ALWAYS include: "
            "📍 [Organization Name], [Full Address] ☎️ [Phone Number]. Put contact info FIRST, not last."
        )

    # --- PROACTIVE INTELLIGENCE: Inject deadline alerts ---
    try:
        from services.proactive_triggers import proactive_scheduler
        if proactive_scheduler:


# ============================================================================
# SIMPLE PUBLIC /ask ENDPOINT (No auth required)
# ============================================================================

KB_RESPONSES = {
    "payment": (
        "To confirm a payment made to the Government of Canada:\n\n"
        "1. **Identify Payment Type** - Immigration fee, tax, passport, etc.\n"
        "2. **Check Receipt** - Look for your confirmation receipt number\n"
        "3. **Verify Online**:\n"
        "   • IRCC payments: Check your application status on Canada.ca\n"
        "   • CRA payments: Use My Account on CRA website\n"
        "   • Service Canada: Check Service Canada account\n"
        "4. **Contact Support**:\n"
        "   • IRCC: 1-888-242-2342\n"
        "   • CRA: 1-800-959-5525\n"
        "5. **Timeline** - Allow 2-5 business days for processing\n\n"
        "Sources: IRCC, CRA, Service Canada",
        ["IRCC.ca", "CRA.gc.ca", "ServiceCanada.gc.ca"]
    ),
    "move": (
        "Steps to Move to Canada as a Newcomer:\n\n"
        "1. **Determine Eligibility** - Express Entry, family sponsorship, PNP, student visa, work permit\n"
        "2. **Get a Permit** - Apply, pass medical exam, get police certificate, language test\n"
        "3. **Prepare Documents** - Passport, proof of funds, education credentials, work experience\n"
        "4. **Before Arrival** - Find housing, research province, open bank account, get SIN\n"
        "5. **On Arrival** - Register with health authority, open bank account, get SIN, register children in school\n"
        "6. **First 6 Months** - Take ESL classes, get provincial ID, join programs, network\n\n"
        "Sources: IRCC, Settlement.org, Canada.ca",
        ["IRCC.ca", "Settlement.org", "Canada.ca"]
    ),
    "job": (
        "How to Find a Job in Canada:\n\n"
        "1. **Prepare Documents** - Canadian resume, cover letter, references, credential assessment\n"
        "2. **Job Search Platforms**:\n"
        "   • JobBank.gc.ca (government listings)\n"
        "   • Indeed.ca, LinkedIn.ca, Workopolis\n"
        "3. **Getting Experience** - Volunteer, internships, apprenticeships\n"
        "4. **Key Steps** - Tailor resume, write cover letter, network, prepare for interviews\n"
        "5. **Licensing** - Check if your field requires Canadian certification\n"
        "6. **Employer Support** - Many offer settlement assistance and mentorship\n\n"
        "Sources: JobBank.gc.ca, LinkedIn, Indeed, Government of Canada",
        ["JobBank.gc.ca", "LinkedIn.ca", "Indeed.ca"]
    ),
    "education": (
        "Canadian Education System:\n\n"
        "K-12 Education:\n"
        "• Age 4-5: Junior Kindergarten\n"
        "• Age 5-6: Kindergarten  \n"
        "• Grades 1-8: Elementary/Middle School\n"
        "• Grades 9-12: High School\n"
        "• FREE for Canadian residents\n"
        "• Compulsory until age 16-18\n\n"
        "Post-Secondary:\n"
        "• Universities: 3-4 year degrees, $6,000-$15,000/year (domestic)\n"
        "• Colleges: 2-3 year diplomas, $2,000-$8,000/year (domestic)\n"
        "• Trades: 4-5 year apprenticeships\n"
        "• Financial aid available (grants, loans, scholarships)\n\n"
        "Registering Your Child:\n"
        "• Contact local school district\n"
        "• Proof of residency required\n"
        "• Language support available\n\n"
        "Sources: Government of Canada, Provincial Education Ministries",
        ["EducationCanada.ca", "ServiceCanada.gc.ca"]
    ),
    "housing": (
        "Housing in Canada - A Guide:\n\n"
        "Types: Apartments, townhouses, single-family homes, shared accommodations\n\n"
        "Renting:\n"
        "• Average: $1,200-$2,500/month (varies by city)\n"
        "• First month + deposit required\n"
        "• Tenant rights protected by provincial law\n"
        "• Typical lease: 1 year\n\n"
        "Buying:\n"
        "• Down payment: 5-20%\n"
        "• Get pre-approved for mortgage\n"
        "• Home inspection recommended\n"
        "• Closing in 30-60 days\n"
        "• Mortgage rates: 4-6%\n\n"
        "Finding Housing:\n"
        "• Kijiji.ca, Rentals.ca, Zillow.ca, MLS, Facebook groups\n\n"
        "Additional Costs: Property tax, home insurance, utilities, condo fees\n\n"
        "Sources: CMHC, Canada.ca, Provincial Housing Authorities",
        ["CMHC.ca", "Canada.ca", "Rentals.ca"]
    ),
    "benefits": (
        "Government Benefits for Newcomers:\n\n"
        "Income Support:\n"
        "• Employment Insurance (EI) - if employed\n"
        "• Guaranteed Income Supplement (GIS) - if 60+\n"
        "• Canada Pension Plan (CPP) - retirement at 65+\n"
        "• Old Age Security (OAS) - 65+\n\n"
        "Family Benefits:\n"
        "• Canada Child Benefit (CCB) - monthly per child\n"
        "• Parental leave benefits (up to 18 months)\n"
        "• Childcare tax credits\n\n"
        "Healthcare & Support:\n"
        "• Provincial health insurance (FREE)\n"
        "• Settlement programs and language classes (FREE)\n"
        "• Job search assistance, credential recognition help\n"
        "• Counseling and community programs\n\n"
        "How to Apply:\n"
        "1. Visit ServiceCanada.gc.ca\n"
        "2. Create My Service account\n"
        "3. Apply online or visit office\n"
        "4. Submit required documents\n\n"
        "Sources: Service Canada, Provincial Ministries",
        ["ServiceCanada.gc.ca", "BenefitsCanada.ca", "SettlementCanada.ca"]
    ),
}


@router.post("/ask")
async def quick_ask(request: dict):
    """Public Q&A endpoint - no authentication required"""
    message = request.get("message", "").lower()
    
    # Find matching keyword
    best_match = None
    best_response = None
    best_sources = []
    
    for keyword, (response_text, sources) in KB_RESPONSES.items():
        if keyword in message:
            best_match = keyword
            best_response = response_text
            best_sources = sources
            break
    
    # Fallback response
    if not best_response:
        best_response = (
            "Welcome to Maple! 🍁 I can help you with questions about:\n\n"
            "✅ Making payments to the Government of Canada\n"
            "✅ Moving to Canada as a newcomer\n"
            "✅ Finding a job in Canada\n"
            "✅ Education system and schools\n"
            "✅ Housing and accommodation\n"
            "✅ Government benefits and support\n\n"
            "Try asking me about any of these topics!"
        )
        best_sources = ["Canada.ca", "Settlement.org"]
    
    return {
        "response": best_response,
        "sources": best_sources,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
            system = await proactive_scheduler.inject_into_system_prompt(uid, system)
    except Exception as e:
        logger.warning(f"Failed to inject proactive alert: {e}")

    async def gen():
        full = ""
        try:
            full = await _openai_chat_response(system, body.message)
            if not full:
                full = await _anthropic_chat_response(system, body.message)
            if not full:
                full = grounded_fallback_response(reason="llm-unavailable")
            full = attach_verified_citations_if_missing(full, rag_context)
            full, compliant, reason = enforce_citation_policy(full)
            if not compliant:
                logger.warning("assistant citation policy fallback applied: user=%s reason=%s", uid, reason)
            
            # === SECURITY CHECK 3: Output Filtering (prevent leaks) ===
            full = filter_response_for_leaks(full)
            
            # Append smart upsell nudge when credits are critically low
            nudge = upsell_nudge(credit_balance, 0, tier)
            if nudge:
                full += nudge
            try:
                await companion_memory.add_turn(
                    session_id=session_id,
                    user_id=uid,
                    query=sanitized_message,
                    response=full,
                    retrieved_docs=[],
                    model_used=os.environ.get("OPENAI_CHAT_MODEL", "gpt-4.1"),
                )
            except Exception:
                logger.exception("failed to store companion memory turn")
            yield full
        except Exception:
            logger.exception("assistant error")
            if not full:
                full = grounded_fallback_response(reason="runtime-error")
                yield full
        await db.chat_messages.insert_one({"id": str(uuid.uuid4()), "user_id": uid, "session_id": session_id, "role": "assistant", "content": full, "created_at": datetime.now(timezone.utc).isoformat()})

    return StreamingResponse(gen(), media_type="text/plain", headers=common_headers)

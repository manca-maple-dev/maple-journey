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


def _custom_system_instructions() -> str:
    """Optional operator-level instruction overrides appended to Maple system prompt."""
    return _env_value(
        "MAPLE_CUSTOM_INSTRUCTIONS",
        "MAPLE_SYSTEM_INSTRUCTIONS",
        "MAPLE_SYSTEM_PROMPT_APPEND",
        "SYSTEM_PROMPT_APPEND",
    )


def _wings_instruction(user: dict) -> str:
    """Translate per-user Wings settings into explicit runtime instructions."""
    wings = user.get("wings") or {}
    tone = (wings.get("tone") or "").strip()
    autonomy = (wings.get("autonomy") or "").strip()
    goals = [g for g in (wings.get("goals") or []) if isinstance(g, str) and g.strip()]

    chunks = []
    if tone:
        chunks.append(f"Tone preference: {tone}.")
    if autonomy == "ask":
        chunks.append("Autonomy preference: ask before taking major next-step assumptions.")
    elif autonomy:
        chunks.append(f"Autonomy preference: {autonomy}.")
    if goals:
        chunks.append("User goals: " + "; ".join(goals[:6]) + ".")

    if not chunks:
        return ""
    return "\n\nUSER WINGS PREFERENCES:\n- " + "\n- ".join(chunks)


def _preferred_provider_order() -> list[str]:
    """Choose provider order from env + available keys.

    Defaults to OpenAI first when available so OPENAI_API_KEY works out of the box.
    """
    preferred = (_env_value("MAPLE_LLM_PROVIDER", "MODEL_PROVIDER") or "").lower()
    has_openai = bool(_env_value("OPENAI_API_KEY", "OPENAI_KEY", "OPENAI_API_TOKEN", "EMERGENT_LLM_KEY"))
    has_anthropic = bool(_env_value("ANTHROPIC_API_KEY"))

    if preferred in {"openai", "anthropic"}:
        order = [preferred, "anthropic" if preferred == "openai" else "openai"]
    elif has_openai:
        order = ["openai", "anthropic"]
    else:
        order = ["anthropic", "openai"]

    if not has_openai:
        order = [p for p in order if p != "openai"]
    if not has_anthropic:
        order = [p for p in order if p != "anthropic"]
    return order


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
        
        "TONE (Professional, Neutral, Efficient):\n"
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
        "✓ Opens with a direct, respectful answer\n"
        "✓ Uses plain professional language without slang or emoji\n"
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
                "content": "We detected unusual activity on your account. For security, please contact support.",
                "created_at": now,
                "security_event": "rate_limited_injection"
            })
            
            return StreamingResponse(
                (i async for i in ["Security check: please contact support."]),
                media_type="text/plain",
                headers={"X-Maple-Security": "rate-limited"}
            )
        
        # Log and reject single injection attempt
        logger.warning(f"Injection attempt blocked for user {uid}: {attack_reason}")
        safe_response = "I can help with immigration and settlement questions. How can I assist you today?"
        
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

    answer = ""
    used_provider = ""

    instruction_sources = [
        "profile" if profile_summary(user) else "",
        "memory" if memory_context else "",
        "community" if community_context else "",
        "rag" if rag_context else "",
        "wings" if _wings_instruction(user) else "",
        "custom" if custom_instructions else "",
    ]
    common_headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "X-Session-Id": session_id,
        "X-Maple-Credits": str(credit_balance),
        "X-Maple-Cost": str(cost),
        "X-Maple-Complexity": complexity,
        "X-Maple-Instruction-Sources": ",".join([item for item in instruction_sources if item]),
        "X-Maple-Provider": used_provider,
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
    system += _wings_instruction(user)
    custom_instructions = _custom_system_instructions()
    if custom_instructions:
        system += "\n\nOPERATOR CUSTOM INSTRUCTIONS:\n" + custom_instructions
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
            pass  # Placeholder for future enhancement
    except Exception as e:
        logger.debug(f"Proactive scheduler not available: {e}")

    # Generate the actual assistant response with deterministic provider order.
    # This ensures OPENAI_API_KEY can be primary instead of always falling back.
    provider_order = _preferred_provider_order()
    for provider in provider_order:
        if provider == "openai":
            answer = await _openai_chat_response(system, sanitized_message)
        elif provider == "anthropic":
            answer = await _anthropic_chat_response(system, sanitized_message)
        if answer:
            used_provider = provider
            break
    if not answer:
        answer = grounded_fallback_response(sanitized_message, rag_context)

    answer, citation_ok, citation_reason = enforce_citation_policy(answer)
    if not citation_ok:
        answer = attach_verified_citations_if_missing(answer, rag_context)
        answer, citation_ok, citation_reason = enforce_citation_policy(answer)
    answer = filter_response_for_leaks(answer)

    if not answer.strip():
        answer = "I’m unable to generate a reliable answer right now. Please try again in a moment."

    await db.chat_messages.insert_one(
        {
            "id": str(uuid.uuid4()),
            "user_id": uid,
            "session_id": session_id,
            "role": "assistant",
            "content": answer,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    async def stream_answer():
        yield answer

    return StreamingResponse(stream_answer(), media_type="text/plain", headers=common_headers)


# ============================================================================
# PUBLIC /ask ENDPOINT (GPT-powered, no auth required)
# ============================================================================


@router.post("/ask")
async def smart_ask(request: dict):
    """🧠 INTELLIGENT Q&A Endpoint - GPT-powered reasoning (no auth required)
    
    Features:
    - Real LLM reasoning (not keyword matching)
    - Context-aware responses about Canada
    - Auto-citation of official sources
    - Multi-step explanations for complex questions
    """
    try:
        message = request.get("message", "").strip()
        if not message:
            return {
                "response": "Ask me anything about Canada! 🍁 Immigration, jobs, education, housing, benefits, taxes...",
                "sources": [],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        
        # === SYSTEM PROMPT FOR EXPERT AI ===
        system_prompt = """You are Maple 🍁, an EXPERT Canadian immigration and settlement advisor.

CORE RULES:
1. **REAL KNOWLEDGE**: You have authoritative knowledge of Canadian law, benefits, procedures from official sources
2. **CITE SOURCES**: Every answer must end with [Source: ...] listing official websites (Canada.ca, IRCC.ca, CRA.gc.ca, etc.)
3. **STEP-BY-STEP THINKING**: Show your reasoning. Break complex questions into clear steps.
4. **PRACTICAL**: Provide actionable advice with timelines, costs, contact info, and next steps
5. **HONEST**: If uncertain, say so. Recommend consulting official sources or lawyers when needed.

YOUR EXPERTISE:
✅ Immigration (Express Entry, sponsorship, visas, PR, citizenship)
✅ Government Benefits (CPP, OAS, EI, CCB, disability, tax credits, RRSP, TFSA)
✅ Employment (job search, credentials, licensing, workplace rights, unions)
✅ Housing (renting, buying, tenant rights, discrimination laws, affordable programs)
✅ Education (K-12, colleges, universities, student loans, international credentials)
✅ Taxes (CRA, returns, deductions, GST/HST, CPP contributions)
✅ Settlement (orientation, community services, cultural resources, family services)
✅ Healthcare (provincial insurance, coverage, wait times, specialists)
✅ Legal Issues (free legal aid, immigration lawyers, small claims, human rights)

RESPONSE FORMAT:
1. Answer the question directly and clearly
2. For procedures: "Step 1 → Step 2 → Step 3..." with timelines
3. For eligibility: "You qualify IF you meet ALL of..."
4. For decisions: "If [situation A], then [result]. If [situation B], then [result]..."
5. ALWAYS END WITH: [Source: Official_Website_Name, Official_Website_Name]
6. Include contact phone numbers and URLs when relevant
7. Mention if information is current to 2026 or needs verification

DO NOT:
❌ Provide legal advice (recommend "consult a lawyer")
❌ Provide tax advice (recommend "consult a CPA")
❌ Make guarantees about outcomes
❌ Provide outdated information without caveats"""
        
        # === CANADIAN KNOWLEDGE GROUNDING ===
        knowledge = """
FEDERAL PROGRAMS 2026:
• CPP-OAS: $16k-17k/year at 65; earlier claims at reduced rate
• EI: 26-45 weeks depending on region; covers 55% earnings
• CCB: $250-400/month per child; income-tested
• GST Credit: Quarterly payments; up to $500/year
• Disability Support: CPP-D or provincial programs (ODSP, etc.)

IMMIGRATION PATHWAYS:
• Express Entry: 500+ CRS points; ITA monthly; 6-month PR processing
• Family Sponsorship: Spouse (3 months), parents (24 months), others vary
• PNP: 400-450 points; province-specific; adds to Express Entry
• Work Permits: LMIA (6 months), closed employer, international mobility
• Study Permits: $20k proof of funds; acceptance letter required

JOB MARKET:
• Top platforms: JobBank.gc.ca, Indeed.ca, LinkedIn.ca
• Credential assessment: WES ($280), ICES ($100+); 2-3 weeks
• Licensing: Check provincial regulatory body (PEO/engineers, LSUC/lawyers, etc.)
• Resume: Canadian format (no photo, date of birth)
• Canadian experience valued; credential assessment often required

HOUSING COSTS 2026:
• Rent: $1,200-3,500/month (varies by city); first month + deposit
• Buy: 5-20% down; mortgage 4-6%; 30-60 day closing
• Tenant rights: Protected by provincial law; illegal key deposits > 1 month
• Eviction: 60-120 day notice; procedure per province

EDUCATION SYSTEM:
• K-12: FREE for residents; compulsory to 16-18
• Universities: $6-15k/year (domestic); 3-4 year degrees
• Colleges: $2-8k/year (domestic); 2-3 year diplomas
• Trades: 4-5 year apprenticeships; wage while learning
• Funding: Grants, loans, scholarships; OSAP in Ontario

OFFICIAL WEBSITES:
• Canada.ca (start here!)
• IRCC.ca (immigration)
• CRA.gc.ca (taxes)
• ServiceCanada.gc.ca (benefits)
• Provinces.gc.ca/[province]"""
        
        # === CALL OPENAI GPT ===
        from openai import AsyncOpenAI
        
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")
        if not api_key:
            return {
                "response": "I can provide information about Canada, but my AI system isn't currently available. Try again in a moment!",
                "sources": [],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        
        client = AsyncOpenAI(api_key=api_key)
        model = os.environ.get("OPENAI_CHAT_MODEL") or "gpt-4o"
        
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt + f"\n\nKNOWLEDGE BASE:\n{knowledge}"},
                {"role": "user", "content": message},
            ],
            temperature=0.5,     # Balanced: factual but natural
            max_tokens=2000,     # Generous for detailed Canadian advice
            top_p=0.9,
        )
        
        answer = response.choices[0].message.content.strip() if response.choices else ""
        
        if not answer:
            answer = "I couldn't generate an answer. Please try rephrasing your question about Canada."
        
        # === EXTRACT SOURCES ===
        sources = ["Canada.ca"]  # Default
        if "[Source:" in answer:
            try:
                source_section = answer.split("[Source:")[-1].split("]")[0].strip()
                sources = [s.strip() for s in source_section.split(",") if s.strip()]
            except:
                pass
        
        return {
            "response": answer,
            "sources": sources[:5],  # Max 5 sources
            "model": model,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    except Exception as e:
        logger.exception("smart_ask error")
        return {
            "response": "I encountered an error. Please try again!",
            "sources": [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
        }

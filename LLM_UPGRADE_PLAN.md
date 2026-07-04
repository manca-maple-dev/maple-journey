# MapleJourney LLM 4-Priority Upgrade — Implementation Plan

**Date:** 2026-07-03  
**Status:** Analysis Complete  
**Total Timeline:** 5 days (Days 1–5)  
**Blueprint Sections:** G.1, G.2, G.3, G.4, F.4, F.5, D

---

## CURRENT STATE ANALYSIS

### services/rag.py — Keyword Scoring (MOCK)
- **Knowledge Base:** 60+ documents hardcoded in Python (KNOWLEDGE_BASE list)
- **Retrieval:** Weighted keyword matching in `_score_relevance()` (NOT vectors)
  - Exact keyword: +3.0 | Title match: +1.5 | Legal ref: +5.0
  - Category boost: +2.0 | Temporal boost (2026): +1.5-3.0
  - **No embeddings, no pgvector, no similarity search**
- **Top-K:** Returns 3 docs scoring >1.5 threshold
- **Live Web Fallback:** If max_score < 4.0, triggers HTTP call to emergent LLM for web search
- **Context Format:** `format_context_for_llm()` → appends docs + IRPA s.91 + Plain English filter

### routers/chat.py — LLM Integration
- **Model:** Claude Sonnet 4.6 (via emergentintegrations)
- **Parameters:** 4096 tokens, top_p=0.92, temperature=0.3
- **System Prompt:** SOVEREIGN_SYSTEM_PROMPT + profile_summary + RAG context
- **Storage:** Streams to `db.chat_messages` (user_id, session_id, role, content, created_at)
- **Limitation:** NO citation extraction, NO citation validation, NO multi-turn memory
- **Session Management:** Uses session_id (UUID) keyed by user_id (not isolated per session yet)

### models.py — Questionnaire (Limited)
**Current fields:** age, education, language, experience_years, canadian_experience, job_offer, provincial_nomination, marital_status

**Missing (Blueprint Section D):**
- immigration_category (refugee|student|worker|visitor|pr)
- province (for provincial reranking)
- household_size, dependents_ages, spouse_status, credential_country, noc_code

### Database (MongoDB)
**Collections:**
- `users` (profile data)
- `chat_messages` (session conversations)
- **MISSING:** `embeddings` table, `document_chunks` table, `companion_memory` table

---

## RECOMMENDED IMPLEMENTATION ORDER

### 🔴 PHASE 1: Vector Search + Temporal Boost (Days 1–2)
**Status:** Foundation — unblocks Phases 2, 3, 4  
**Why First:** Highest impact, no dependencies, isolated to rag.py

**Blockers:** None  
**Dependencies:** OpenAI API key, pgvector-enabled Supabase

**Deliverables:**
1. ✅ Migrate KNOWLEDGE_BASE → Supabase pgvector (1536 dims, text-embedding-3-small)
2. ✅ Replace `_score_relevance()` with cosine_similarity on embeddings
3. ✅ Add temporal boost: +3.0 if published within 90 days, +0 if >2 years old
4. ✅ Update `retrieve_documents()` to query pgvector (top-3 by similarity)
5. ✅ Test: "Tell me about PGWP 2026" → July 2026 entries rank first

**Code Changes:**
- `services/rag.py`: Replace `_score_relevance()` (~100 lines)
- `services/rag.py`: Rewrite `retrieve_documents()` for pgvector queries (~30 lines)
- `core/db.py`: Add pgvector connection utilities (~20 lines)
- `requirements.txt`: Add `pgvector>=0.2.0`, pin `openai>=1.0.0`

**Example (Before → After):**
```python
# BEFORE: Keyword scoring
score = 0.0
for kw in doc["keywords"]:
    if kw.lower() in query_lower:
        score += 3.0
return score

# AFTER: Vector similarity + temporal boost
query_embedding = openai.Embedding.create(...).embedding
doc_embedding = db.query_pgvector(doc_id)
similarity = cosine_similarity(query_embedding, doc_embedding)
temporal_boost = 3.0 if (today - doc["last_verified"]).days < 90 else 0.0
return similarity * 10.0 + temporal_boost  # normalize + boost
```

---

### 🟡 PHASE 2: User Context Reranking (Days 2–3)
**Status:** Depends on Phase 1  
**Why Second:** Leverages vectors, improves relevance per user's pathway

**Blockers:** Questionnaire schema expansion (minor)  
**Dependencies:** Phase 1 (vectors must work first)

**Deliverables:**
1. ✅ Expand `models.py` QuestionnaireIn:
   - Add `immigration_category` (str: refugee|student|worker|pr|visitor)
   - Add `province` (str: ON|BC|AB|QC|etc.)
2. ✅ Update `_score_relevance()` to boost based on user profile:
   - If user's immigration_category matches doc's category: +2.0
   - If user's province matches doc's province: +1.5
3. ✅ Pass full user context to `rag_search()` for reranking
4. ✅ Test: User "student in BC" → BC study permit docs ranked higher

**Code Changes:**
- `models.py`: Add 5–6 fields to QuestionnaireIn (~10 lines)
- `services/rag.py`: Enhance `_score_relevance()` with user boosting (~30 lines)
- `routers/chat.py`: Ensure user context passed to `rag_search()` (already done, verify)

**Example:**
```python
# User: immigration_category="student", province="BC"
# Docs scoring:
# - irpa-study-deep (category="study_permit", BC-specific): +2.0 (category) +1.5 (province) = +3.5
# - ircc-health-deep (category="settlement", BC-specific): +0 (cat) +1.5 (province) = +1.5
# Final ranking: study_permit doc + BC boost wins
```

---

### 🟠 PHASE 3: Citation Validation (Days 3–4)
**Status:** Depends on Phases 1–2  
**Why Third:** Tight coupling to LLM response, must run after LLM generates text

**Blockers:** Source registry must be defined  
**Dependencies:** Phase 2 context (citation quality depends on good context)

**Deliverables:**
1. ✅ Define SOURCE_REGISTRY whitelist (approved domains)
   - canada.ca, laws-lois.justice.gc.ca, irb.gc.ca, service.gc.ca
2. ✅ Extract citations from LLM response:
   - Regex: `\[Source: (.+?), published (.+?)\]`
   - Extract URL + date from each citation
3. ✅ Validate each citation:
   - Check URL against SOURCE_REGISTRY whitelist (exact match or domain allowlist)
   - HTTP HEAD request (expect 200 status)
   - Cache validation result (1h TTL)
4. ✅ Reject response if validation fails:
   - Regenerate LLM response with stricter system prompt
   - OR return fallback: "I couldn't verify sources for this response. Please visit canada.ca/ircc..."
5. ✅ Test: "How do I apply for PR?" → all citations resolve + in whitelist

**Code Changes:**
- `routers/chat.py`: Add citation extraction + validation in response stream (~50 lines)
- `services/rag.py`: Define SOURCE_REGISTRY whitelist + validator (~40 lines)
- Add httpx utility for URL head checks

**Example:**
```python
# LLM Response (in stream):
"Under IRPR R.205, you need a job offer. [Source: https://laws-lois.justice.gc.ca/eng/regulations/SOR-2002-227/page-43.html, published 2026-06-28]"

# Extract:
citations = re.findall(r'\[Source: (.+?), published (.+?)\]', response)
# Result: [("https://laws-lois.justice.gc.ca/eng/regulations/SOR-2002-227/page-43.html", "2026-06-28")]

# Validate:
for url, date in citations:
    if not is_whitelisted(url):
        raise ValidationError(f"URL not in registry: {url}")
    if not url_resolves(url):  # HEAD request
        raise ValidationError(f"URL returned non-200: {url}")
```

---

### 🔵 PHASE 4: Companion Memory (Days 4–5)
**Status:** Depends on Phases 1, 3  
**Why Fourth:** Heaviest DB changes, requires citation validation first

**Blockers:** Supabase migration, RLS policy setup  
**Dependencies:** Phases 1 (vectors for chunk retrieval), 3 (citations to store)

**Deliverables:**
1. ✅ Create Supabase table `companion_memory`:
   ```sql
   CREATE TABLE companion_memory (
     id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
     companion_session_id uuid NOT NULL,
     user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
     turn_num int NOT NULL,
     user_message text,
     retrieved_chunk_ids text[] NOT NULL DEFAULT '{}',  -- IDs of doc chunks
     assistant_response text,
     extracted_citations jsonb,  -- [{url, date, validated}, ...]
     created_at timestamp DEFAULT now(),
     UNIQUE(companion_session_id, turn_num)
   );
   
   ALTER TABLE companion_memory ENABLE ROW LEVEL SECURITY;
   CREATE POLICY "users_can_read_own_memory" ON companion_memory
     FOR SELECT USING (auth.uid() = user_id);
   CREATE POLICY "users_can_insert_own_memory" ON companion_memory
     FOR INSERT WITH CHECK (auth.uid() = user_id);
   ```

2. ✅ Store retrieved chunks alongside responses:
   - In `rag_search()`, return `(docs, max_score, chunk_ids, snippets)`
   - Save chunk_ids to companion_memory after LLM response

3. ✅ Build multi-turn context for follow-up questions:
   - Fetch last 20 turns from companion_memory (WHERE companion_session_id = current_session_id)
   - Build system message: "Previous conversation: [turn 1], [turn 2], ..."
   - Append to LLM context before generating response

4. ✅ Test: Session 1: "What's PGWP?" → response stored. Then: "How long is it?" → previous context retrieved, coherent multi-turn response

**Code Changes:**
- `core/db.py`: Add Supabase migration file for companion_memory table
- `routers/chat.py`: Update response pipeline to store memory (~60 lines)
- `routers/chat.py`: Update LLM context building to fetch + prepend previous turns (~40 lines)
- `services/rag.py`: Return chunk_ids alongside docs (~20 lines)

**Example:**
```python
# Turn 1: User asks "What's PGWP?"
# Response: "PGWP is an open work permit..."
# Stored: companion_memory(
#   companion_session_id=UUID(...),
#   turn_num=1,
#   user_message="What's PGWP?",
#   retrieved_chunk_ids=["ircc-pgwp-deep"],
#   assistant_response="PGWP is..."
# )

# Turn 2: User asks "How long is it?"
# Fetch: previous_turns = db.companion_memory.where(session_id=UUID(...)).order_by(turn_num).limit(20)
# Build context: "Earlier you asked: 'What's PGWP?' I answered: 'PGWP is...'. Now you're asking: 'How long is it?'"
# LLM sees: system_prompt + full_context + new_question
# Response: "Based on our earlier discussion about PGWP, the duration depends on..."
```

---

## BLOCKERS & DEPENDENCIES MATRIX

| Phase | Blocker | Impact | Mitigation |
|-------|---------|--------|-----------|
| **1** | pgvector setup | Can't use embeddings | Supabase pgvector extension (built-in, enable with UI) |
| **1** | OpenAI API key | Embedding calls fail | Already in .env; verify quota sufficient (60 docs = ~60 calls) |
| **1** | KNOWLEDGE_BASE migration | Manual work | Write Python script to batch migrate hardcoded docs → pgvector |
| **2** | Questionnaire fields missing | Reranking weak | Minor schema update (fields already in UI onboarding, just add to backend) |
| **2** | User profile not populated | User context empty | Already implemented in Profile.jsx; backend reads from users collection |
| **3** | Source registry scope | Can't validate broadly | Start with 60 URLs in KNOWLEDGE_BASE + canada.ca/* allowlist |
| **3** | HTTP validation timeout | Chat latency spikes | Use 2s timeout, cache results (1h TTL), fail-open if timeout |
| **4** | companion_memory schema | Can't store sessions | Create migration; run via Supabase Studio or via script |
| **4** | Multi-turn context bloat | Token limits exceeded | Keep last 20 turns max (~20K tokens); summarize older if needed |
| **4** | RLS policy incorrect | Security issue | Test policy: authenticated user can only read own sessions |

---

## TEST SCENARIOS (Validation Checklist)

### Phase 1 Validation:
- [ ] Document embedding stores in pgvector (1536 dims)
- [ ] Query: "TR-to-PR 2026" → returns July 2026 entry first (temporal boost)
- [ ] Query: "PGWP" → top-3 docs sorted by cosine similarity (not keyword score)
- [ ] Old docs (2025) ranked lower than recent (2026) given same keyword
- [ ] Live web search NOT triggered for well-matched queries (max_score > 4.0)

### Phase 2 Validation:
- [ ] User profile "student, BC" → BC study permit docs ranked higher
- [ ] User profile "worker, Ontario" → ON-specific work permit docs first
- [ ] Same query, different profiles → different doc ranking order

### Phase 3 Validation:
- [ ] Response with valid citation: `[Source: https://www.canada.ca/..., published 2026-07-01]` → ✅ Passes
- [ ] Response with invalid URL (not in whitelist) → ❌ Rejected
- [ ] Response with unresolvable URL (HTTP 404) → ❌ Rejected + regenerate
- [ ] Fallback message displays: "I couldn't verify sources..."

### Phase 4 Validation:
- [ ] Turn 1: Q: "What's PGWP?" → stored in companion_memory
- [ ] Turn 2: Q: "How long is it?" → previous context retrieved + coherent response
- [ ] Last 20 turns enforced (older turns archived/deleted)
- [ ] Cross-session isolation: session_2 can't read session_1 memory
- [ ] RLS policy tested: non-owner user can't read other's sessions

---

## BLUEPRINT ALIGNMENT

| Section | Feature | Phase | Status |
|---------|---------|-------|--------|
| **G.1** | Source Registry whitelist | 3 | ✅ URL validation + domain allowlist |
| **G.2** | Retrieval Stack (embeddings + temporal + user context) | 1+2+4 | ✅ Phases 1-4 combine |
| **G.3** | Citation-required output (`[Source: URL, published date]`) | 3 | ✅ Extraction + validation |
| **G.4** | Refusal patterns (legal advice, CRS, medical) | - | ✅ Already in system prompt (maintained) |
| **F.4** | Per-user leaf identity (companion_session_id UUID) | 4 | ✅ Not user_id |
| **F.5** | PII-safe (embeddings + chunks, discard raw messages) | 4 | ✅ Vectors + chunks stored, raw text after processing |
| **D** | Questionnaire expansion (40 fields, 10 groups) | 2 | ⚠️ Partial (add immigration_category, province; full expansion deferred) |

---

## FILE-BY-FILE CHANGES

### services/rag.py (~200 lines of changes)
```python
# NEW: Vector scoring + temporal boost
async def embed_and_score_relevance(doc: Dict, query: str, user_context: Optional[Dict]) -> float:
    """Cosine similarity on embeddings + temporal boost."""
    query_embedding = await openai.Embedding.create(
        model="text-embedding-3-small",
        input=query
    ).embeddings[0].embedding
    
    doc_embedding = db.pgvector.query_one(
        "SELECT embedding FROM documents WHERE id = %s",
        doc["id"]
    )
    
    similarity = cosine_similarity(query_embedding, doc_embedding)
    temporal_boost = 3.0 if (today - doc["last_verified"]).days < 90 else 0.0
    
    # User context reranking (Phase 2)
    user_boost = 0.0
    if user_context:
        if user_context["immigration_category"] == doc["category"]:
            user_boost += 2.0
        if user_context["province"] in doc.get("provinces", []):
            user_boost += 1.5
    
    return (similarity * 10.0) + temporal_boost + user_boost

# REPLACE: _score_relevance() with embed_and_score_relevance()
# REPLACE: retrieve_documents() to use pgvector queries
```

### routers/chat.py (~100 lines of changes)
```python
# NEW: Citation extraction + validation (Phase 3)
async def validate_citations(response: str) -> Tuple[bool, List[str]]:
    """Extract citations, validate against SOURCE_REGISTRY + HTTP resolve."""
    citations = re.findall(r'\[Source: (.+?), published (.+?)\]', response)
    
    for url, date in citations:
        if not is_url_whitelisted(url):
            return False, [f"URL not in registry: {url}"]
        if not await url_resolves_to_200(url):
            return False, [f"URL returned non-200: {url}"]
    
    return True, [url for url, _ in citations]

# UPDATE: assistant_chat() POST endpoint
# Before storing response, validate citations
# If invalid, regenerate with stricter prompt or return fallback

# NEW: Multi-turn context (Phase 4)
async def build_multi_turn_context(companion_session_id: str, top_k: int = 20) -> str:
    """Fetch last K turns, format as conversation history."""
    turns = await db.companion_memory.find(
        {"companion_session_id": companion_session_id}
    ).sort("created_at", 1).to_list(top_k)
    
    context_parts = []
    for turn in turns:
        context_parts.append(f"User: {turn['user_message']}")
        context_parts.append(f"Assistant: {turn['assistant_response']}")
    
    return "\n\n".join(context_parts)
```

### models.py (~10 lines of changes)
```python
class QuestionnaireIn(BaseModel):
    # ... existing fields ...
    immigration_category: Optional[str] = None  # NEW: refugee|student|worker|pr|visitor
    province: Optional[str] = None              # NEW: ON|BC|AB|QC|...
    language_fluency: Optional[str] = None      # NEW: basic|intermediate|advanced|fluent
    # ... rest ...
```

### core/db.py (~20 lines + migration file)
```python
# NEW: pgvector connection utilities
async def pgvector_similarity_search(
    query_embedding: List[float],
    table: str = "documents",
    top_k: int = 3,
    threshold: float = 0.5
) -> List[Dict]:
    """Query pgvector for top-K similar documents."""
    result = await db.execute(
        f"""
        SELECT id, title, content, url, embedding <-> %s AS distance
        FROM {table}
        WHERE (embedding <-> %s) < 1 - %s
        ORDER BY distance
        LIMIT %s
        """,
        query_embedding, query_embedding, threshold, top_k
    )
    return result

# Supabase Migration File: 2026070301_create_companion_memory.sql
# See Phase 4 Deliverables for full CREATE TABLE statement
```

### requirements.txt (2 lines)
```
pgvector>=0.2.0          # NEW: Vector DB operations
openai>=1.0.0            # ENSURE: Latest API (embeddings support)
```

---

## DEPLOYMENT & ROLLOUT STRATEGY

### Rollout Plan:
1. **v1.1 (Week 1):** Deploy Phases 1–2 together
   - Vector embeddings + temporal boost + user context reranking
   - Test with 5 real users (dogfood phase)
   
2. **v1.2 (Week 2):** Deploy Phases 3–4 together
   - Citation validation + multi-turn memory
   - Gradual rollout (25% → 50% → 100% of users)

3. **Monitoring:**
   - Track LLM latency (Phase 4 context building overhead)
   - Monitor citation validation failure rate
   - Log user satisfaction (A/B test: Phase 1 vs Phase 1-4)

### Fallback Plan:
- If Phase 1 pgvector fails: fall back to keyword scoring
- If Phase 3 citation validation fails: skip validation, log warning, allow response
- If Phase 4 memory lookup slow: cache previous turns in Redis, 5-min TTL

---

## QUESTIONS FOR STAKEHOLDER

1. **pgvector hosting:** Supabase managed (recommended, easiest) or self-host?
2. **Citation format:** Keep `[Source: {URL}, published {date}]` or JSON format?
3. **Source registry scope:** 60 URLs from KNOWLEDGE_BASE + canada.ca/* or broader?
4. **Companion memory retention:** Keep forever or auto-delete after 90 days (privacy)?
5. **Phase 4 scope:** Just chat memory, or integrate with WhatsApp companion workflows (Section F.2)?

---

## IMMEDIATELY NEXT STEPS

1. ✅ **Phase 1 Setup:**
   - [ ] Enable pgvector in Supabase (1-click)
   - [ ] Verify OpenAI API key quota
   - [ ] Write Python migration script (hardcoded → pgvector)

2. ✅ **Testing Infrastructure:**
   - [ ] Create Pytest fixtures for vector search
   - [ ] Mock OpenAI API for CI/CD
   - [ ] Set up test database on Supabase

3. ✅ **Live Validation:**
   - [ ] Spin up dev server: `npm run dev` (frontend) + `python server.py` (backend)
   - [ ] Test Phase 1 retrieval with real queries
   - [ ] Benchmark: retrieval latency (should be <500ms for top-3)

4. ✅ **Git Workflow:**
   - [ ] Create feature branch: `feat/llm-vector-search-phase1`
   - [ ] Commit structure: one commit per Phases 1-2 (together), then Phases 3-4 (together)
   - [ ] PR review checklist: tests pass, latency OK, no regressions

---

## ESTIMATED EFFORT

| Phase | Backend | Frontend | Testing | Total |
|-------|---------|----------|---------|-------|
| **1** | 4h | 0h | 2h | **6h** |
| **2** | 2h | 0h | 1h | **3h** |
| **3** | 3h | 0h | 2h | **5h** |
| **4** | 5h | 0h | 3h | **8h** |
| **Deployment + Docs** | 2h | - | - | **2h** |
| **TOTAL** | **16h** | **0h** | **8h** | **~24h (~3 days)** |

---

## SUCCESS CRITERIA

- ✅ All Phase 1 tests pass (vectors, temporal boost, retrieval <500ms)
- ✅ Phase 2 reranking improves relevance score by 15-20% (A/B test)
- ✅ Phase 3 citations validated; zero invalid citations in production
- ✅ Phase 4 multi-turn memory reduces hallucination by 10-15% (user satisfaction)
- ✅ Blueprint compliance: all Section G requirements met
- ✅ Zero PII leakage in embeddings (audit log)

---

**Status:** Ready for Phase 1 kickoff  
**Owner:** MapleJourney Engineering  
**Last Updated:** 2026-07-03

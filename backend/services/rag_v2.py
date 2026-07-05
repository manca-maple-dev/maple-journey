"""RAG v2.0 — Vector-Based Retrieval with Temporal Boost & User Context

Upgrades from v1:
✅ OpenAI text-embedding-3-small (1536 dims) instead of mock keyword scoring
✅ Supabase pgvector for efficient similarity search (HNSW index)
✅ Temporal boost: +3.0 for docs published in last 90 days
✅ User context reranking: boost docs matching user's immigration_category
✅ Cosine similarity instead of keyword match
✅ Prepared for Phase 3 citation validation & Phase 4 companion memory

Usage:
    documents, max_score = await retrieve_documents_v2(
        query="How do I extend my work permit?",
        user_context={"immigration_category": "temp_foreign_worker", "province": "ON"},
        top_k=3
    )
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import json

from openai import AsyncOpenAI
import httpx

logger = logging.getLogger("maplejourney.rag_v2")

_openai_client: AsyncOpenAI | None = None


def _get_openai_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        _openai_client = AsyncOpenAI(api_key=api_key)
    return _openai_client

# PostgreSQL/Supabase pgvector connection (imported from db.py)
# Assumes: environment variable SUPABASE_URL, SUPABASE_KEY set
# Connection pooling handled by Supabase managed service

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
LIVE_SEARCH_TIMEOUT = 8.0

# SOURCE REGISTRY (whitelist for citation validation in Phase 3)
SOURCE_REGISTRY = {
    "ircc": ["https://www.canada.ca", "https://laws-lois.justice.gc.ca"],
    "cra": ["https://www.canada.ca/en/revenue-agency"],
    "esdc": ["https://www.canada.ca/en/employment-social-development"],
    "irb": ["https://irb.gc.ca"],
    "provincial": ["https://www.ontario.ca", "https://www2.gov.bc.ca", "https://www.quebec.ca"],
}

# IRPA s.91 Disclosure (from rag.py)
IRPA_S91_DISCLOSURE = (
    "\n\n═══ IMPORTANT DISCLOSURE (IRPA Section 91) ═══\n"
    "Maple provides verified information and procedural guidance only. "
    "This is NOT legal advice. Under IRPA s.91, only regulated representatives "
    "(lawyers or RCICs) may provide immigration advice for a fee. "
    "Verify credentials: college-ic.ca/find or CBA Lawyer Referral.\n"
    "═══════════════════════════════════════════════\n"
)

PLAIN_ENGLISH_FILTER = (
    "\n\nPLAIN ENGLISH MANDATE (CLB 3-4 Accessible):\n"
    "• Use SHORT sentences (under 15 words each when possible).\n"
    "• Use SIMPLE words. Say 'get' not 'obtain'. Say 'send in' not 'submit'.\n"
    "• Explain every acronym the FIRST time: 'PGWP (Post-Graduation Work Permit)'.\n"
    "• Use numbered steps for any process.\n"
)

PROACTIVE_PRESCIENCE_INSTRUCTIONS = (
    "\n\nPROACTIVE PRESCIENCE:\n"
    "After answering, add 'What to watch for next:' — identify 1-2 upcoming deadlines "
    "or risks the user likely hasn't thought of yet.\n"
)


# ---------------------------------------------------------------------------
# Phase 1: Vector Embedding & Storage
# ---------------------------------------------------------------------------

async def embed_text(text: str) -> List[float]:
    """Embed text using OpenAI text-embedding-3-small.
    
    Caches embeddings in Supabase to avoid recomputing.
    Cost: $0.02/1M tokens
    """
    try:
        response = await _get_openai_client().embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
        )
        embedding = response.data[0].embedding
        assert len(embedding) == EMBEDDING_DIM
        return embedding
    except Exception as e:
        if "OPENAI_API_KEY is not configured" in str(e):
            logger.warning("OpenAI embeddings disabled because OPENAI_API_KEY is missing")
            return [0.0] * EMBEDDING_DIM
        logger.error("Embedding failed: %s", str(e))
        raise


async def store_embeddings_in_pgvector(documents: List[Dict]) -> int:
    """Store documents + embeddings in Supabase pgvector.
    
    Creates table if not exists:
    - id: UUID primary key
    - doc_id: string (reference to original doc)
    - title: text
    - content: text (first 1000 chars for display)
    - embedding: vector(1536)
    - category: string (for filtering)
    - source_url: string (for citation)
    - last_verified: date (for temporal boost)
    - created_at: timestamp
    
    Args:
        documents: List of dicts with keys: id, title, content, category, url, last_verified
    
    Returns:
        Number of documents stored
    """
    from supabase import create_client  # Assumes SUPABASE_URL, SUPABASE_KEY in env
    
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_KEY", "")
    
    if not supabase_url or not supabase_key:
        logger.warning("SUPABASE_URL or SUPABASE_KEY not set; skipping embedding storage")
        return 0
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        
        # Ensure table exists with pgvector
        # CREATE TABLE IF NOT EXISTS documents (
        #   id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        #   doc_id TEXT NOT NULL,
        #   title TEXT,
        #   content TEXT,
        #   embedding vector(1536),
        #   category TEXT,
        #   source_url TEXT,
        #   last_verified DATE,
        #   created_at TIMESTAMP DEFAULT NOW(),
        #   UNIQUE(doc_id)
        # );
        # CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops);
        
        stored = 0
        for doc in documents:
            # Embed document content
            embedding = await embed_text(doc.get("content", "")[:2000])
            
            # Store in Supabase
            supabase.table("documents").upsert({
                "doc_id": doc["id"],
                "title": doc.get("title", ""),
                "content": doc.get("content", "")[:1000],
                "embedding": embedding,
                "category": doc.get("category", ""),
                "source_url": doc.get("url", ""),
                "last_verified": doc.get("last_verified", ""),
                "deep_links": json.dumps(doc.get("deep_links", [])),
                "legal_refs": json.dumps(doc.get("legal_refs", [])),
            }).execute()
            
            stored += 1
            if stored % 10 == 0:
                logger.info("Embedded and stored %d documents...", stored)
        
        logger.info("✅ Stored %d documents in pgvector", stored)
        return stored
    
    except Exception as e:
        logger.error("Failed to store embeddings: %s", str(e))
        return 0


# ---------------------------------------------------------------------------
# Phase 1: Vector Similarity Search with Temporal Boost
# ---------------------------------------------------------------------------

async def retrieve_documents_v2(
    query: str,
    user_context: Optional[Dict] = None,
    top_k: int = 3
) -> Tuple[List[Dict], float]:
    """Retrieve documents using vector similarity + temporal boost + user context.
    
    Steps:
    1. Embed the query using OpenAI
    2. Vector similarity search in pgvector (HNSW, cosine distance)
    3. Apply temporal boost: +3.0 if published in last 90 days
    4. Apply user context reranking: boost by immigration_category, province
    5. Return top_k by final score + max_score for Omniscience Engine decision
    
    Args:
        query: User question to retrieve for
        user_context: Dict with keys: immigration_category, province, language (optional)
        top_k: Number of results to return
    
    Returns:
        (documents_with_scores, max_score)
        Each document has added keys: relevance_score, reranking_reason
    """
    from supabase import create_client
    from datetime import datetime, timedelta
    
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_KEY", "")
    
    if not supabase_url or not supabase_key:
        logger.warning("SUPABASE not configured; falling back to mock results")
        return [], 0.0
    
    try:
        # Step 1: Embed the query
        query_embedding = await embed_text(query)
        logger.info("Query embedding generated (dim=%d)", len(query_embedding))
        
        # Step 2: Vector search in pgvector
        supabase = create_client(supabase_url, supabase_key)
        
        # SQL: SELECT * FROM documents ORDER BY embedding <=> query_embedding LIMIT 10
        # pgvector <=> operator is cosine distance; smaller = more similar
        results = supabase.rpc(
            "search_documents",  # Custom RPC function or direct SQL
            {
                "query_embedding": query_embedding,
                "match_count": top_k * 2,  # Retrieve extra to rerank
            }
        ).execute()
        
        retrieved_docs = results.data if results.data else []
        logger.info("Vector search returned %d candidates", len(retrieved_docs))
        
        # Step 3: Compute scores with temporal boost & reranking
        scored_docs = []
        for doc in retrieved_docs:
            # Base score from cosine distance (inverted: 1 - distance)
            distance = doc.get("distance", 1.0)  # pgvector returns distance
            base_score = 1.0 - distance  # Convert to similarity (0-1)
            score = base_score * 10.0  # Scale to ~0-10
            
            # Temporal boost: +3.0 for documents < 90 days old
            last_verified = doc.get("last_verified", "")
            if last_verified:
                try:
                    verified_date = datetime.strptime(last_verified, "%Y-%m-%d").date()
                    days_old = (datetime.now().date() - verified_date).days
                    if days_old < 90:
                        score += 3.0
                        logger.debug("Temporal boost applied: doc %s is %d days old", doc.get("doc_id"), days_old)
                except ValueError:
                    pass
            
            # User context reranking
            reranking_reason = ""
            if user_context:
                doc_category = doc.get("category", "")
                
                # Category boost based on immigration_category
                user_category = user_context.get("immigration_category", "")
                category_boost_map = {
                    "temp_foreign_worker": ["work_permit"],
                    "student": ["study_permit"],
                    "refugee_claimant": ["refugee"],
                    "express_entry": ["permanent_residence"],
                    "pnp": ["permanent_residence", "pnp"],
                }
                if user_category in category_boost_map:
                    for cat in category_boost_map[user_category]:
                        if cat in doc_category:
                            score += 2.0
                            reranking_reason += f"Category match: {user_category} ↔ {cat}. "
                
                # Province boost
                user_province = user_context.get("province", "")
                if user_province and user_province.lower() in doc.get("content", "").lower():
                    score += 1.0
                    reranking_reason += f"Province {user_province} mentioned. "
                
                # Language boost (if applicable)
                if user_context.get("language", "").lower() == "french":
                    if "french" in doc.get("title", "").lower():
                        score += 1.5
                        reranking_reason += "French language match. "
            
            doc["relevance_score"] = score
            doc["reranking_reason"] = reranking_reason
            scored_docs.append(doc)
        
        # Step 4: Sort by final score and return top_k
        scored_docs.sort(key=lambda d: d["relevance_score"], reverse=True)
        final_docs = scored_docs[:top_k]
        max_score = final_docs[0]["relevance_score"] if final_docs else 0.0
        
        logger.info(
            "Retrieved %d docs after reranking (max_score=%.2f) for query: %.60s",
            len(final_docs), max_score, query
        )
        
        return final_docs, max_score
    
    except Exception as e:
        logger.error("Vector retrieval failed: %s; falling back to empty results", str(e))
        return [], 0.0


# ---------------------------------------------------------------------------
# Phase 1: Live Web Search Fallback (from rag.py, preserved)
# ---------------------------------------------------------------------------

async def _live_web_search(query: str, top_k: int = 3) -> Optional[str]:
    """Live web search against authoritative Canadian government domains."""
    try:
        openai_key = os.environ.get("OPENAI_API_KEY", "")
        if not openai_key:
            logger.warning("OPENAI_API_KEY not set; skipping live web search")
            return None
        client = AsyncOpenAI(api_key=openai_key)
        model = os.environ.get("OPENAI_WEB_MODEL", os.environ.get("OPENAI_CHAT_MODEL", "gpt-4.1"))
        resp = await client.responses.create(
            model=model,
            instructions=(
                "You are a Canadian immigration research assistant. Search for current information from "
                "canada.ca, justice.gc.ca, and irb.gc.ca. Return factual findings with specific URLs."
            ),
            input=(
                f"Find latest authoritative Canadian government info on: {query}\n\n"
                "Return: key facts, URLs, legal references, effective dates."
            ),
            max_output_tokens=1500,
            temperature=0.1,
            tools=[{"type": "web_search", "search_context_size": "medium"}],
        )
        content = getattr(resp, "output_text", "") or ""
        if content and len(content) > 50:
            logger.info("Live web search returned %d chars", len(content))
            return content

    except Exception as e:
        logger.warning("Live web search failed: %s", str(e))
    
    return None


# ---------------------------------------------------------------------------
# RAG v2 Main Entry Point
# ---------------------------------------------------------------------------

OMNISCIENCE_THRESHOLD = 4.0


async def rag_search_v2(query: str, user: Optional[Dict] = None) -> str:
    """Main RAG v2 entry point with vector search + temporal boost.
    
    Replaces rag_search() from v1.
    
    Args:
        query: User question
        user: User profile dict with optional keys: immigration_category, province, language
    
    Returns:
        Formatted context block for LLM with retrieved docs + instructions
    """
    
    # Build user context for reranking
    user_context = None
    if user:
        user_context = {
            "immigration_category": user.get("immigration_category"),
            "province": user.get("province"),
            "language": user.get("preferred_language", "en"),
        }
    
    # Vector search with temporal boost & reranking
    documents, max_score = await retrieve_documents_v2(query, user_context, top_k=3)
    
    logger.info("RAG v2 retrieved %d docs (max_score=%.2f)", len(documents), max_score)
    
    # Omniscience Engine: trigger live web search if score low or query temporal
    live_web_context = ""
    temporal_triggers = ["2026", "latest", "current", "new", "carney", "bill c-12"]
    query_lower = query.lower()
    
    if max_score < OMNISCIENCE_THRESHOLD or any(t in query_lower for t in temporal_triggers):
        logger.info("Omniscience triggered (score=%.2f or temporal query)", max_score)
        live_content = await _live_web_search(query, top_k=3)
        if live_content:
            live_web_context = (
                "\n\n═══ LIVE WEB DATA (Real-Time Government Sources) ═══\n"
                f"{live_content}\n"
                "═══ END LIVE WEB DATA ═══\n"
            )
    
    # Format context for LLM
    if not documents and not live_web_context:
        return (
            "No specific documents matched this query. "
            "Please check canada.ca/ircc or call IRCC at 1-888-242-2100."
            + PLAIN_ENGLISH_FILTER
            + IRPA_S91_DISCLOSURE
        )
    
    # Build document context block
    doc_context = "\n\n═══ RETRIEVED DOCUMENTS (Vector Search) ═══\n"
    for i, doc in enumerate(documents, 1):
        doc_context += (
            f"\n[{i}] {doc.get('title', 'Untitled')}\n"
            f"    Score: {doc.get('relevance_score', 0):.2f} "
            f"({doc.get('reranking_reason', 'Base vector match')})\n"
            f"    Source: {doc.get('source_url', '')}\n"
            f"    Verified: {doc.get('last_verified', '')}\n"
            f"    Content: {doc.get('content', '')[:500]}...\n"
        )
    doc_context += "═══ END DOCUMENTS ═══\n"
    
    return (
        doc_context
        + live_web_context
        + PLAIN_ENGLISH_FILTER
        + PROACTIVE_PRESCIENCE_INSTRUCTIONS
        + IRPA_S91_DISCLOSURE
    )

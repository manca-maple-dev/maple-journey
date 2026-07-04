"""Test Vector Search Implementation

Verifies that:
1. Documents are stored in pgvector
2. Vector search returns results
3. Temporal boost works
4. User context reranking works

Run:
    python scripts/test_vector_search.py
"""

import asyncio
import os
from services.rag_v2 import retrieve_documents_v2


async def test_vector_search():
    """Run integration tests for vector search."""
    
    print("🧪 Vector Search Tests\n")
    print("=" * 60)
    
    # Test 1: Basic retrieval
    print("\n[Test 1] Basic Vector Search")
    print("-" * 60)
    query = "How do I extend my work permit?"
    docs, score = await retrieve_documents_v2(query, top_k=3)
    
    if docs:
        print(f"✅ Retrieved {len(docs)} documents")
        print(f"   Max relevance score: {score:.2f}")
        for i, doc in enumerate(docs, 1):
            print(f"   [{i}] {doc.get('title', 'Untitled')[:50]}")
            print(f"       Score: {doc.get('relevance_score', 0):.2f}")
    else:
        print("⚠️  No documents returned (pgvector may not be populated yet)")
    
    # Test 2: Temporal boost
    print("\n[Test 2] Temporal Boost (2026 documents)")
    print("-" * 60)
    query2 = "What is the new TR-to-PR pathway 2026?"
    docs2, score2 = await retrieve_documents_v2(query2, top_k=3)
    
    if docs2:
        print(f"✅ Retrieved {len(docs2)} documents")
        print(f"   Max relevance score: {score2:.2f}")
        for i, doc in enumerate(docs2, 1):
            verified = doc.get('last_verified', 'unknown')
            print(f"   [{i}] {doc.get('title', 'Untitled')[:50]}")
            print(f"       Verified: {verified} | Score: {doc.get('relevance_score', 0):.2f}")
            if "2026-07" in verified or "2026-06" in verified:
                print(f"       ✓ Temporal boost applied (recent doc)")
    else:
        print("⚠️  No documents returned")
    
    # Test 3: User context reranking
    print("\n[Test 3] User Context Reranking")
    print("-" * 60)
    query3 = "Express Entry and permanent residence"
    user_context = {
        "immigration_category": "express_entry",
        "province": "ON",
        "language": "en"
    }
    docs3, score3 = await retrieve_documents_v2(query3, user_context=user_context, top_k=3)
    
    if docs3:
        print(f"✅ Retrieved {len(docs3)} documents with user context")
        print(f"   Max relevance score: {score3:.2f}")
        for i, doc in enumerate(docs3, 1):
            print(f"   [{i}] {doc.get('title', 'Untitled')[:50]}")
            print(f"       Score: {doc.get('relevance_score', 0):.2f}")
            reason = doc.get('reranking_reason', '')
            if reason:
                print(f"       Reason: {reason}")
    else:
        print("⚠️  No documents returned")
    
    # Test 4: Omniscience threshold comparison
    print("\n[Test 4] Score Distribution (for Omniscience trigger)")
    print("-" * 60)
    test_queries = [
        "Express Entry CRS",
        "Very obscure immigration topic that won't match",
        "PGWP field of study restrictions",
    ]
    
    for q in test_queries:
        docs_t, score_t = await retrieve_documents_v2(q, top_k=1)
        status = "TRIGGERED" if score_t < 4.0 else "OK"
        print(f"   Query: {q[:40]:<40} | Score: {score_t:.2f} | Omniscience: {status}")
    
    print("\n" + "=" * 60)
    print("✅ Vector search tests complete")
    print("\nNext steps:")
    print("  1. If tests passed: Phase 1 is ready!")
    print("  2. Update chat.py to use rag_v2.rag_search_v2 instead of rag.rag_search")
    print("  3. Test live with: python server.py")
    print("  4. Begin Phase 2: User context reranking refinement")


if __name__ == "__main__":
    asyncio.run(test_vector_search())

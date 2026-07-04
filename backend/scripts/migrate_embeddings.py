"""Migrate KNOWLEDGE_BASE from rag.py into pgvector

Embeds all documents using OpenAI text-embedding-3-small and stores in Supabase.

Requirements:
- OPENAI_API_KEY environment variable set
- SUPABASE_URL and SUPABASE_KEY set
- pgvector table already created (run setup_pgvector.py first)

Run:
    python scripts/migrate_embeddings.py

Cost: ~$0.05 for embedding entire KB (60 docs × 2000 tokens × $0.02/1M)
"""

import os
import asyncio
import json
from datetime import datetime

# Import the KNOWLEDGE_BASE from rag.py
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.rag import KNOWLEDGE_BASE

from openai import AsyncOpenAI
from supabase import create_client


async def migrate_knowledge_base():
    """Embed all KNOWLEDGE_BASE documents and store in pgvector."""
    
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not openai_api_key:
        print("❌ OPENAI_API_KEY not set")
        return
    
    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL or SUPABASE_KEY not set")
        return
    
    openai_client = AsyncOpenAI(api_key=openai_api_key)
    supabase = create_client(supabase_url, supabase_key)
    
    print(f"📚 Starting migration of {len(KNOWLEDGE_BASE)} documents...")
    print("⏳ This will take ~1-2 minutes. OpenAI embedding calls will be batched.\n")
    
    successful = 0
    failed = 0
    
    for i, doc in enumerate(KNOWLEDGE_BASE, 1):
        try:
            # Embed document content (limited to 2000 chars to save tokens)
            content_to_embed = doc.get("content", "")[:2000]
            print(f"  [{i}/{len(KNOWLEDGE_BASE)}] Embedding {doc.get('title', 'Untitled')[:60]}...", end="", flush=True)
            
            response = await openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=content_to_embed,
            )
            
            embedding = response.data[0].embedding
            assert len(embedding) == 1536, f"Expected 1536 dims, got {len(embedding)}"
            
            # Store in Supabase
            result = supabase.table("documents").upsert({
                "doc_id": doc["id"],
                "title": doc.get("title", ""),
                "content": doc.get("content", "")[:1000],
                "embedding": embedding,
                "category": doc.get("category", ""),
                "source_url": doc.get("url", ""),
                "deep_links": json.dumps(doc.get("deep_links", [])),
                "legal_refs": json.dumps(doc.get("legal_refs", [])),
                "last_verified": doc.get("last_verified", ""),
            }).execute()
            
            print(" ✅")
            successful += 1
            
            # Rate limiting: OpenAI has request limits, add slight delay
            if i % 5 == 0:
                await asyncio.sleep(0.5)
        
        except Exception as e:
            print(f" ❌ Error: {str(e)[:50]}")
            failed += 1
    
    print(f"\n✅ Migration complete!")
    print(f"   • Embedded: {successful} documents")
    print(f"   • Failed: {failed} documents")
    print(f"   • Estimated cost: ${successful * 2000 * 0.02 / 1_000_000:.2f}")
    print(f"\nNext: Run 'python scripts/test_vector_search.py' to verify")


if __name__ == "__main__":
    asyncio.run(migrate_knowledge_base())

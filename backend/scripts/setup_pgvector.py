"""Supabase Setup for pgvector Integration

This script creates the necessary tables and functions in Supabase for vector search.

Requirements:
- Supabase project with pgvector extension enabled
- SUPABASE_URL and SUPABASE_KEY in environment

Run:
    python scripts/setup_pgvector.py
"""

import os
from supabase import create_client

def setup_pgvector():
    """Create pgvector table and RPC functions."""
    
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL or SUPABASE_KEY not set")
        return False
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        
        # Raw SQL execution via Supabase admin API
        # We use the execute() method on the client to run custom SQL
        
        print("⏳ Creating pgvector extension...")
        supabase.postgrest.session.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        print("⏳ Creating documents table with pgvector...")
        sql_create_table = """
        CREATE TABLE IF NOT EXISTS documents (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            doc_id TEXT NOT NULL UNIQUE,
            title TEXT,
            content TEXT,
            embedding vector(1536),
            category TEXT,
            source_url TEXT,
            deep_links JSONB DEFAULT '[]'::jsonb,
            legal_refs JSONB DEFAULT '[]'::jsonb,
            last_verified DATE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """
        supabase.postgrest.session.execute(sql_create_table)
        
        print("⏳ Creating HNSW index for fast similarity search...")
        sql_index = """
        CREATE INDEX IF NOT EXISTS documents_embedding_idx 
        ON documents USING hnsw (embedding vector_cosine_ops)
        WITH (m=4, ef_construction=64);
        """
        supabase.postgrest.session.execute(sql_index)
        
        print("⏳ Creating search_documents RPC function...")
        sql_rpc = """
        CREATE OR REPLACE FUNCTION search_documents(
            query_embedding vector(1536),
            match_count INT DEFAULT 10
        )
        RETURNS TABLE(
            id uuid,
            doc_id TEXT,
            title TEXT,
            content TEXT,
            category TEXT,
            source_url TEXT,
            deep_links JSONB,
            legal_refs JSONB,
            last_verified DATE,
            distance FLOAT
        )
        LANGUAGE SQL
        AS $$
            SELECT
                id,
                doc_id,
                title,
                content,
                category,
                source_url,
                deep_links,
                legal_refs,
                last_verified,
                (1 - (embedding <=> query_embedding)) AS distance
            FROM documents
            ORDER BY embedding <=> query_embedding
            LIMIT match_count;
        $$;
        """
        supabase.postgrest.session.execute(sql_rpc)
        
        print("✅ pgvector setup complete!")
        print("\nNext steps:")
        print("1. Run: python scripts/migrate_embeddings.py")
        print("2. Test with: python scripts/test_vector_search.py")
        
        return True
    
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False


if __name__ == "__main__":
    setup_pgvector()

"""Phase 3: Companion Memory System

Multi-turn conversation history with retrieved context persistence.
Enables "companion" continuity across 20 turns, with automatic context
reuse for follow-up questions.

Architecture:
- companion_sessions collection: Top-level session (1 per user per day)
- companion_turns collection: Individual exchanges (query, response, context)
- Retrieved chunks stored with each turn for citation+context reuse
"""

import logging
import re
from datetime import datetime, timezone, timedelta
from collections import Counter
from typing import Optional, List, Dict, Any
from uuid import uuid4

import pymongo

logger = logging.getLogger("maplejourney.companion_memory")


class CompanionMemory:
    """Manage multi-turn companion conversations with context persistence."""
    
    def __init__(self, db):
        self.db = db
        self.sessions_coll = db.companion_sessions
        self.turns_coll = db.companion_turns
    
    async def ensure_indexes(self):
        """Create indexes for fast lookup and cleanup."""
        # Session indexes
        await self.sessions_coll.create_index("user_id")
        await self.sessions_coll.create_index("date")
        await self.sessions_coll.create_index([("created_at", pymongo.DESCENDING)])
        
        # Turn indexes
        await self.turns_coll.create_index("session_id")
        await self.turns_coll.create_index("user_id")
        await self.turns_coll.create_index([("created_at", pymongo.DESCENDING)])
    
    async def get_or_create_session(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        channel: str = "web",
    ) -> Dict[str, Any]:
        """Get existing session or create new one (1 per user per day).
        
        Returns:
            { _id, user_id, session_id, date, turn_count, created_at, updated_at }
        """
        now = datetime.now(timezone.utc)
        date = now.date().isoformat()
        
        # Look for existing today's session
        if not session_id:
            existing = await self.sessions_coll.find_one({
                "user_id": user_id,
                "date": date,
            })
            if existing:
                await self._touch_channel(existing["session_id"], channel)
                logger.info(f"Reusing session {existing['session_id']} for user {user_id}")
                return existing
        
        # Create new session
        new_session = {
            "_id": str(uuid4()),
            "user_id": user_id,
            "session_id": session_id or str(uuid4()),
            "date": date,
            "turn_count": 0,
            "channels": [channel],
            "channel_last_seen": {channel: now.isoformat()},
            "created_at": now,
            "updated_at": now,
        }
        
        await self.sessions_coll.insert_one(new_session)
        logger.info(f"Created new session {new_session['session_id']} for user {user_id}")
        return new_session

    async def _touch_channel(self, session_id: str, channel: str) -> None:
        """Attach a channel to the unified session and track last-seen."""
        now = datetime.now(timezone.utc).isoformat()
        await self.sessions_coll.update_one(
            {"session_id": session_id},
            {
                "$addToSet": {"channels": channel},
                "$set": {
                    f"channel_last_seen.{channel}": now,
                    "updated_at": datetime.now(timezone.utc),
                },
            },
        )

    async def resolve_channel_session(self, user_id: str, channel: str) -> str:
        """Resolve the active unified session id for a user/channel pair."""
        session = await self.get_or_create_session(user_id=user_id, channel=channel)
        return session["session_id"]
    
    async def add_turn(
        self,
        session_id: str,
        user_id: str,
        query: str,
        response: str,
        retrieved_docs: List[Dict[str, Any]],
        model_used: str = "claude-sonnet",
        tokens_used: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Store one conversation turn with context.
        
        Args:
            session_id: Session UUID
            user_id: User UUID
            query: User's question/message
            response: Maple's response
            retrieved_docs: [{ title, url, score, snippet, category, ... }]
            model_used: Model name (claude-sonnet, gpt-4, etc)
            tokens_used: Input+output tokens consumed
        
        Returns:
            { _id, session_id, turn_count, query, response, docs, model_used, created_at }
        """
        session = await self.sessions_coll.find_one({"session_id": session_id})
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        turn_count = session.get("turn_count", 0) + 1
        now = datetime.now(timezone.utc)
        
        turn = {
            "_id": str(uuid4()),
            "session_id": session_id,
            "user_id": user_id,
            "turn_number": turn_count,
            "query": query,
            "response": response,
            "retrieved_docs": retrieved_docs,  # Store for context reuse
            "model_used": model_used,
            "tokens_used": tokens_used or 0,
            "created_at": now,
        }
        
        await self.turns_coll.insert_one(turn)
        
        # Update session metadata
        await self.sessions_coll.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "turn_count": turn_count,
                    "updated_at": now,
                    "last_query": query[:100],
                    "last_model": model_used,
                }
            }
        )
        
        logger.info(f"Added turn {turn_count} to session {session_id}")
        return turn
    
    async def get_recent_context(self, session_id: str, num_turns: int = 5) -> List[Dict[str, Any]]:
        """Retrieve last N turns for context injection into next query.
        
        Returns: List of { turn_number, query, response, doc_titles } for context
        """
        turns = await self.turns_coll.find(
            {"session_id": session_id}
        ).sort("turn_number", -1).limit(num_turns).to_list(None)
        
        context = []
        for turn in reversed(turns):  # Oldest first
            context.append({
                "turn": turn.get("turn_number"),
                "query": turn.get("query"),
                "response": turn.get("response", "")[:500],  # Truncate long responses
                "docs_used": [doc.get("title") for doc in turn.get("retrieved_docs", [])],
            })
        
        return context

    async def build_memory_brief(self, session_id: str, num_turns: int = 5) -> str:
        """Build a short memory block that helps Maple stay consistent and personal."""
        context = await self.get_recent_context(session_id, num_turns=num_turns)
        if not context:
            return ""

        stopwords = {
            "about", "after", "again", "could", "from", "have", "help", "into", "just", "know",
            "more", "need", "please", "that", "there", "this", "what", "when", "where", "which",
            "with", "your", "would", "they", "their", "will", "were", "been", "want", "tell",
            "kind", "make", "show", "give", "keep", "like", "looking", "today", "yesterday",
        }
        words = Counter()
        for item in context:
            query = (item.get("query") or "").lower()
            for token in re.findall(r"[a-z]{4,}", query):
                if token not in stopwords:
                    words[token] += 1

        topic_list = ", ".join(word for word, _ in words.most_common(5))
        lines = ["RECENT MAPLE MEMORY (use this to stay consistent, practical, and not repeat yourself):"]
        if topic_list:
            lines.append(f"- Recurring topics: {topic_list}")
        for item in context[-3:]:
            query = (item.get("query") or "").strip()
            response = (item.get("response") or "").strip()
            if query:
                lines.append(f"- User asked: {query[:120]}")
            if response:
                lines.append(f"- Maple answered: {response[:160]}")
        return "\n".join(lines)
    
    async def extract_doc_ids_for_reuse(self, session_id: str) -> List[str]:
        """Get all document IDs referenced in this session (for follow-up boosting).
        
        Rationale: If user asked about PR timeline in turn 1, follow-up questions
        in turns 2-5 should boost those same docs (temporal locality).
        """
        turns = await self.turns_coll.find(
            {"session_id": session_id}
        ).to_list(None)
        
        doc_ids = set()
        for turn in turns:
            for doc in turn.get("retrieved_docs", []):
                if doc.get("_id"):
                    doc_ids.add(str(doc["_id"]))
        
        return list(doc_ids)
    
    async def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """Delete sessions older than N days (PIPEDA compliance).
        
        Returns: Count of deleted sessions
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_old)
        
        old_sessions = await self.sessions_coll.find(
            {"created_at": {"$lt": cutoff}},
            {"session_id": 1},
        ).to_list(None)
        session_ids = [s.get("session_id") for s in old_sessions if s.get("session_id")]

        result = await self.sessions_coll.delete_many({
            "created_at": {"$lt": cutoff}
        })
        if session_ids:
            await self.turns_coll.delete_many({"session_id": {"$in": session_ids}})
        
        logger.info(f"Cleaned up {result.deleted_count} sessions older than {days_old} days")
        return result.deleted_count
    
    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get session metadata for display (e.g., in admin dashboard).
        
        Returns: { date, turn_count, models_used, total_tokens, docs_referenced }
        """
        session = await self.sessions_coll.find_one({"session_id": session_id})
        if not session:
            return {}
        
        turns = await self.turns_coll.find({"session_id": session_id}).to_list(None)
        
        models_used = set()
        total_tokens = 0
        docs_referenced = set()
        
        for turn in turns:
            models_used.add(turn.get("model_used", "unknown"))
            total_tokens += turn.get("tokens_used", 0)
            for doc in turn.get("retrieved_docs", []):
                docs_referenced.add(doc.get("title", "unknown"))
        
        return {
            "session_id": session_id,
            "user_id": session.get("user_id"),
            "date": session.get("date"),
            "turn_count": session.get("turn_count", 0),
            "models_used": list(models_used),
            "total_tokens": total_tokens,
            "unique_docs": len(docs_referenced),
            "created_at": session.get("created_at"),
            "updated_at": session.get("updated_at"),
        }

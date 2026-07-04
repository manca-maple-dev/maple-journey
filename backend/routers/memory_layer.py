"""
Memory Layer API Endpoints — User-controlled companion memory management
"""
from fastapi import APIRouter, Depends, HTTPException
from core.security import get_current_user
from services.memory_layer import memory_service, MemoryCategory, MemoryConfidence
from core.db import db
from bson import ObjectId
import logging

logger = logging.getLogger("maple.memory_api")
router = APIRouter(prefix="/assistant", tags=["memory-layer"])


@router.get("/memory")
async def get_user_memory(
    category: str = None,
    user: dict = Depends(get_current_user),
):
    """
    Get all facts Maple remembers about the user.
    Optional: filter by category (personal, visa_status, goals, constraints, etc)
    """
    try:
        mem_category = None
        if category:
            try:
                mem_category = MemoryCategory(category)
            except ValueError:
                pass

        memories = await memory_service.get_user_memory(
            str(user["_id"]),
            category=mem_category,
            db=db,
        )

        # Convert ObjectId for JSON serialization
        for mem in memories:
            mem["_id"] = str(mem["_id"])

        return {
            "count": len(memories),
            "memories": memories,
        }
    except Exception as e:
        logger.error(f"Failed to get user memory: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve memory")


@router.post("/memory")
async def add_memory_fact(
    body: dict,
    user: dict = Depends(get_current_user),
):
    """
    Manually add a fact to memory.
    POST body: { fact: string, category: string, confidence?: string }
    """
    try:
        fact = body.get("fact", "").strip()
        category_str = body.get("category", "personal")
        confidence_str = body.get("confidence", "high")

        if not fact:
            raise HTTPException(status_code=400, detail="fact required")

        category = MemoryCategory(category_str)
        confidence = MemoryConfidence(confidence_str)

        memory_doc = await memory_service.add_memory_fact(
            str(user["_id"]),
            fact,
            category,
            confidence,
            db=db,
        )

        memory_doc["_id"] = str(memory_doc["_id"])
        return {"added": True, "memory": memory_doc}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid category or confidence: {e}")
    except Exception as e:
        logger.error(f"Failed to add memory fact: {e}")
        raise HTTPException(status_code=500, detail="Failed to add memory")


@router.put("/memory/{memory_id}")
async def update_memory_fact(
    memory_id: str,
    body: dict,
    user: dict = Depends(get_current_user),
):
    """
    Update an existing memory fact.
    PUT body: { fact?: string, verified?: bool, confidence?: string }
    """
    try:
        # Convert memory_id to ObjectId
        try:
            obj_id = ObjectId(memory_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid memory_id")

        updates = {}
        if "fact" in body:
            updates["fact"] = body["fact"]
        if "confidence" in body:
            updates["confidence"] = body["confidence"]
        if "verified" in body:
            updates["user_verified"] = body["verified"]

        success = await memory_service.update_memory_fact(obj_id, updates, db)

        return {"updated": success}
    except Exception as e:
        logger.error(f"Failed to update memory: {e}")
        raise HTTPException(status_code=500, detail="Failed to update memory")


@router.delete("/memory/{memory_id}")
async def delete_memory_fact(
    memory_id: str,
    user: dict = Depends(get_current_user),
):
    """
    Delete a memory fact (user doesn't want Maple to remember this).
    """
    try:
        try:
            obj_id = ObjectId(memory_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid memory_id")

        success = await memory_service.delete_memory_fact(obj_id, db)

        return {"deleted": success}
    except Exception as e:
        logger.error(f"Failed to delete memory: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete memory")


@router.post("/memory/{memory_id}/verify")
async def verify_memory_fact(
    memory_id: str,
    body: dict,
    user: dict = Depends(get_current_user),
):
    """
    User verifies or disputes a memory fact.
    POST body: { verified: bool }
    """
    try:
        try:
            obj_id = ObjectId(memory_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid memory_id")

        verified = body.get("verified", True)
        success = await memory_service.verify_memory_fact(obj_id, verified, db)

        return {"verified": verified, "success": success}
    except Exception as e:
        logger.error(f"Failed to verify memory: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify memory")


@router.get("/memory-summary")
async def get_memory_summary(
    user: dict = Depends(get_current_user),
):
    """
    Get a quick summary of user's memory profile by category.
    """
    try:
        summary = await memory_service.get_memory_summary(str(user["_id"]), db)

        return summary
    except Exception as e:
        logger.error(f"Failed to get memory summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get memory summary")


@router.get("/memory-context")
async def get_memory_context(
    user: dict = Depends(get_current_user),
):
    """
    Get compact memory context for system prompt (internal use).
    """
    try:
        context = await memory_service.extract_system_memory_context(
            str(user["_id"]), 
            db
        )

        return {"context": context}
    except Exception as e:
        logger.error(f"Failed to get memory context: {e}")
        raise HTTPException(status_code=500, detail="Failed to get memory context")

"""
Hybrid LLM Endpoints — Support for both cloud and local inference
"""
from fastapi import APIRouter, Depends, HTTPException
from core.security import get_current_user
from services.llm_router import route_llm_request, get_fallback_response
from services.webllm_engine import webllm_engine
from core.db import db
import logging

logger = logging.getLogger("maple.hybrid_llm")
router = APIRouter(prefix="/assistant", tags=["hybrid-llm"])


@router.get("/model-status")
async def get_model_status(user: dict = Depends(get_current_user)):
    """
    Get WebLLM model status for the current user.
    Tells frontend whether to attempt local inference.
    """
    try:
        metadata = await webllm_engine.get_model_metadata()
        
        return {
            "model": metadata["model"],
            "size_mb": metadata["size_mb"],
            "ready": metadata["ready"],
            "device": "gpu",  # Would be set by client based on hardware
            "can_offload": True,
        }
    except Exception as e:
        logger.error(f"Failed to get model status: {e}")
        return {"model": "unavailable", "ready": False, "error": str(e)}


@router.post("/routing-decision")
async def get_routing_decision(
    body: dict,
    user: dict = Depends(get_current_user),
):
    """
    Determine whether to route request to cloud or local model.
    Frontend sends: is_online, message_preview, sensitivity_level
    Returns: recommended_route, local_model_ready, timeout_ms
    """
    try:
        is_online = body.get("is_online", True)
        message_preview = body.get("message_preview", "")
        request_sensitivity = body.get("sensitivity", "medium")
        webllm_ready = body.get("webllm_ready", False)

        # Get user's privacy preference
        user_settings = await db.user_settings.find_one({"user_id": str(user["_id"])})
        privacy_mode = user_settings.get("privacy_mode", "hybrid") if user_settings else "hybrid"

        # Make routing decision
        route = await route_llm_request(
            user_id=str(user["_id"]),
            user_privacy_mode=privacy_mode,
            request_sensitivity=request_sensitivity,
            is_online=is_online,
            webllm_ready=webllm_ready,
            message=message_preview,
        )

        return {
            "route": route.value,
            "local_model_ready": webllm_ready,
            "cloud_preferred": route == "cloud",
            "hybrid_mode": route == "hybrid",
            "timeout_ms": 5000,  # Cloud timeout in ms
        }
    except Exception as e:
        logger.error(f"Routing decision error: {e}")
        # Default to cloud on error
        return {
            "route": "cloud",
            "local_model_ready": False,
            "cloud_preferred": True,
            "error": str(e),
        }


@router.get("/fallback-response")
async def get_fallback_response_endpoint(
    query_type: str,
    context: str = "{}",
    user: dict = Depends(get_current_user),
):
    """
    Get fallback response when local model or cloud times out.
    """
    try:
        import json

        context_dict = json.loads(context)
        response = await get_fallback_response(query_type, context_dict)

        return {"response": response}
    except Exception as e:
        logger.error(f"Fallback response error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate fallback response")

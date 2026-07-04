"""
Smart Routing Logic — Decides between Cloud LLM vs Local WebLLM
Routes based on: connectivity, privacy settings, complexity, sensitivity
"""
import logging
from typing import Literal
from enum import Enum

logger = logging.getLogger("maple.llm_router")


class RoutingStrategy(str, Enum):
    CLOUD = "cloud"
    LOCAL = "local"
    HYBRID = "hybrid"  # Try local first, fallback to cloud


async def route_llm_request(
    user_id: str,
    user_privacy_mode: str,  # "cloud_preferred", "local_only", "hybrid"
    request_sensitivity: str,  # "high", "medium", "low"
    is_online: bool,
    webllm_ready: bool,
    message: str,
) -> RoutingStrategy:
    """
    Intelligent router: decides which LLM to use for this request.
    
    Rules:
    1. If offline: use local (or fallback to cached templates)
    2. If local_only mode + privacy concern: use local
    3. If high-sensitivity + private data: use local
    4. If WebLLM ready + network slow: try local first
    5. Default: cloud (faster, higher quality)
    """

    # Rule 1: Offline = local only
    if not is_online:
        logger.info(f"user_id={user_id} routing=local reason=offline")
        return RoutingStrategy.LOCAL

    # Rule 2: User's privacy mode
    if user_privacy_mode == "local_only":
        logger.info(f"user_id={user_id} routing=local reason=privacy_mode")
        return RoutingStrategy.LOCAL

    # Rule 3: High-sensitivity data
    if request_sensitivity == "high":
        # Don't send certain topics to cloud
        sensitive_keywords = [
            "dv",
            "abuse",
            "violence",
            "trafficking",
            "health",
            "legal",
        ]
        if any(keyword in message.lower() for keyword in sensitive_keywords):
            if webllm_ready:
                logger.info(f"user_id={user_id} routing=local reason=sensitive_data")
                return RoutingStrategy.LOCAL
            else:
                # Can't use local, but cloud has safeguards
                logger.info(f"user_id={user_id} routing=cloud reason=sensitive_data_no_local")
                return RoutingStrategy.CLOUD

    # Rule 4: WebLLM ready + hybrid mode (try local first)
    if user_privacy_mode == "hybrid" and webllm_ready:
        logger.info(f"user_id={user_id} routing=hybrid reason=webllm_ready")
        return RoutingStrategy.HYBRID

    # Default: cloud (faster, better quality)
    logger.info(f"user_id={user_id} routing=cloud reason=default")
    return RoutingStrategy.CLOUD


async def get_fallback_response(
    query_type: str,
    context: dict,
) -> str:
    """
    Get cached fallback response when:
    - Offline
    - Local model not ready
    - Cloud timeout
    """
    from services.webllm_engine import FALLBACK_TEMPLATES

    if query_type in FALLBACK_TEMPLATES:
        template = FALLBACK_TEMPLATES[query_type]
        try:
            return template.format(**context)
        except KeyError:
            return template

    # Generic fallback
    return (
        "I'm currently loading my knowledge base. "
        "This should only take a moment. Please try your question again."
    )

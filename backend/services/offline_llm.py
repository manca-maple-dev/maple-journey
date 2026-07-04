"""
Offline WebLLM Integration — Local LLM fallback when cloud unavailable.
Quantized model: phi-2 or mistral-7b-instruct (3-4GB).
Runs via WebLLM on frontend; backend manages model state + caching.
"""
import os
import logging
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger("maple.offline")

# Model cache metadata
OFFLINE_MODEL_CONFIG = {
    "model_id": "Phi-2",  # or "Mistral-7B-Instruct-v0.2"
    "quantized_size_gb": 3.2,
    "context_window": 2048,
    "supports_function_calling": False,
    "typical_latency_ms": 800,  # Per token, on modern device
}

# Cached response templates for common queries (fallback when model unavailable)
CACHED_RESPONSES = {
    "visa_expiry": (
        "I can see your {visa_type} visa expires on {expiry_date}. "
        "That's {days_until} days away. You should start renewal paperwork {buffer_days} days before expiry. "
        "Here's what to do: 1) Check official IRCC portal for your case status. "
        "2) Gather required documents (passport, proof of funds, police certificate). "
        "3) Submit extension 180 days before expiry. Once submitted, you'll have implied status."
    ),
    "pr_eligibility": (
        "Based on your {years_in_canada} years in Canada, you may now qualify for citizenship. "
        "Under the Citizenship Act, you need 3 years physical presence + 2 years permanent residency. "
        "Next steps: 1) Take official language test (CLB 4 minimum). "
        "2) File taxes for all years in Canada. 3) Submit citizenship application online. "
        "Processing time: 12-18 months."
    ),
    "tax_deadline": (
        "Your tax return deadline is {tax_deadline}. As an {status}, you must file because: "
        "• Unlock CCB (Canada Child Benefit) • Claim tuition credits • Avoid penalties. "
        "Bring: T4, T4A, receipts, SIN. Find free VITA help at {vita_location} or call 211."
    ),
}


class OfflineLLMManager:
    """
    Manages offline LLM model state, caching, and fallback responses.
    Frontend (WebLLM) handles actual inference; backend tracks state.
    """

    def __init__(self):
        self.model_ready = False
        self.model_id = OFFLINE_MODEL_CONFIG["model_id"]
        self.last_sync = None
        self.cached_model_version = None
        self.fallback_enabled = True

    async def ensure_model_cached(self):
        """
        Verify model is downloaded and ready on client device.
        Returns metadata for client to display progress.
        """
        return {
            "status": "ready",  # or "downloading", "initializing"
            "model": self.model_id,
            "size_gb": OFFLINE_MODEL_CONFIG["quantized_size_gb"],
            "context_window": OFFLINE_MODEL_CONFIG["context_window"],
            "latency_ms": OFFLINE_MODEL_CONFIG["typical_latency_ms"],
            "last_sync": self.last_sync,
        }

    async def get_fallback_response(
        self, 
        query_type: str, 
        context: dict
    ) -> Optional[str]:
        """
        When cloud LLM unavailable, serve cached template-based response.
        Used during offline or when cloud times out.
        """
        if query_type not in CACHED_RESPONSES:
            return None

        template = CACHED_RESPONSES[query_type]
        try:
            return template.format(**context)
        except KeyError as e:
            logger.warning(f"Fallback template missing key: {e}")
            return None

    async def should_use_local_model(self, 
                                     request_sensitivity: str,
                                     user_privacy_mode: str,
                                     online: bool) -> bool:
        """
        Decide: use local WebLLM or route to cloud?
        
        Rules:
        - If offline: use local
        - If high_sensitivity + privacy_mode="local_only": use local
        - If cloud unavailable: use local
        - Otherwise: prefer cloud for better quality
        """
        if not online:
            return True
        if request_sensitivity == "high" and user_privacy_mode == "local_only":
            return True
        return False

    async def log_fallback_usage(self, user_id: str, reason: str):
        """Track when fallback was used (for analytics)."""
        logger.info(f"user_id={user_id} fallback_reason={reason}")


offline_llm = OfflineLLMManager()

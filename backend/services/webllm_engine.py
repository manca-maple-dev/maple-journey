"""
WebLLM Inference Engine — Local model fallback for offline operation
Downloads quantized phi-2 or mistral-7b and runs inference locally via JavaScript.
Backend manages model state and caching; actual inference happens on client.
"""
import logging
import json
from typing import Optional, Dict
from datetime import datetime, timezone

logger = logging.getLogger("maple.webllm")


class WebLLMEngine:
    """
    Manages WebLLM model lifecycle and metadata.
    Actual model runs on frontend; backend tracks state and provides fallback responses.
    """

    def __init__(self):
        self.model_config = {
            "model_id": "Phi-2",
            "huggingface_id": "mlc-ai/Phi-2-q4f32_1-MLC",
            "quantized_size_mb": 3200,
            "context_window": 2048,
            "supports_streaming": True,
            "recommended_device": "GPU",
            "fallback_device": "CPU",
        }
        self.model_ready = False
        self.last_check = None

    async def get_model_metadata(self) -> Dict:
        """Return model info for frontend to display download progress."""
        return {
            "model": self.model_config["model_id"],
            "huggingface_id": self.model_config["huggingface_id"],
            "size_mb": self.model_config["quantized_size_mb"],
            "context": self.model_config["context_window"],
            "streaming": self.model_config["supports_streaming"],
            "ready": self.model_ready,
            "last_check": self.last_check,
        }

    async def check_model_status(self, device: Optional[str] = None) -> Dict:
        """
        Check if WebLLM model is loaded on client.
        Frontend polls this to report download/initialization progress.
        """
        return {
            "status": "ready" if self.model_ready else "initializing",
            "model": self.model_config["model_id"],
            "size_mb": self.model_config["quantized_size_mb"],
            "device_preference": device or self.model_config["recommended_device"],
            "requires_download": True,
            "estimated_download_time_min": 15,  # ~200MB/min on typical connection
        }

    async def get_inference_fallback(
        self, 
        system_prompt: str, 
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> Optional[str]:
        """
        Fallback response when WebLLM is unavailable or offline.
        Returns a sensible cached/template-based response.
        """
        # This would normally call a lightweight local model or serve cached response
        # For now, return guidance that local inference is initializing
        return (
            "I'm initializing my local reasoning engine to provide you with offline support. "
            "In the meantime, here's what I can help with:\n\n"
            "• Immigration timeline guidance\n"
            "• Deadline reminders based on your profile\n"
            "• Document checklists for common applications\n"
            "• Definition of immigration terms\n\n"
            "Please try your question again in a moment — I'll have faster, offline responses ready."
        )


webllm_engine = WebLLMEngine()


# Lightweight fallback templates for common Maple queries
FALLBACK_TEMPLATES = {
    "visa_extension": """
To extend your {visa_type} visa:
1. Check your current status and expiry date at [ircc.gc.ca/mycic]
2. Gather required documents:
   - Valid passport
   - Proof of funds ($15,263 CAD single person)
   - Police certificate
   - Medical exam (if required)
3. Submit application 180 days before expiry
4. You'll have 'implied status' while processing — cannot work during gap

Processing time: 120-180 days
Fee: $155 CAD
""",
    "pr_eligibility": """
PR Eligibility Checklist:
✓ 3 years physical presence in Canada
✓ Language test: CLB 4+ (or equivalent)
✓ Tax returns filed for all years in Canada
✓ No criminal record (police certificate)
✓ Eligible work/study experience

Next steps:
1. Take language test (IELTS, CELPIP, TCF, TEF)
2. Get ECA for education (if applicable)
3. File taxes for all years
4. Submit citizenship application
Processing: 12-18 months
""",
    "tax_deadline": """
Canada Tax Filing Deadline: April 30
USA Tax Filing Deadline: May 15

Why file:
• Unlock Canada Child Benefit (CCB)
• Claim tuition credits
• Avoid $100+ penalties per month late

As a newcomer:
• File Form T776 if you have rental income
• Claim moving expenses (first year)
• Get GST/HST credit

Free help:
• VITA sites (community.ca/taxa-help)
• Call 211 for local resources
""",
}

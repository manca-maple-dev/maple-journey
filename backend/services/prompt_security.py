"""Prompt injection & jailbreak protection for Maple AI.

Prevents adversarial attempts to manipulate Maple's system prompt,
override instructions, or extract confidential data.

Defense layers:
1. Input sanitization - Remove suspicious patterns
2. Intent detection - Flag potential attacks
3. Output filtering - Prevent leaking system prompts
4. Rate limiting - Detect attack patterns (multiple fast failures)
"""
import re
import logging
from typing import Tuple

logger = logging.getLogger("maplejourney.security")

# Patterns that indicate prompt injection attempts
INJECTION_PATTERNS = [
    # System prompt extraction attempts
    r"(?i)(show|print|reveal|output|display)\s+(your|the|my)\s+(system\s+)?prompt",
    r"(?i)(what.*are.*your.*instructions|what.*should.*you.*do)",
    r"(?i)ignore.*previous.*instructions?",
    r"(?i)(forget|override|bypass|ignore).*all.*rules",
    r"(?i)you.*are.*now.*a\s+",
    r"(?i)(jailbreak|jail\s+break|unlock|unrestricted)",
    r"(?i)(act\s+as|pretend\s+to\s+be|role\s+play|become)\s+(admin|root|super|unrestricted)",
    
    # Token smuggling / context corruption
    r"(?i)(end\s+prompt|close\s+prompt|<\/\s*prompt)",
    r"(?i)(new\s+conversation|reset\s+context|forget\s+everything)",
    r"(?i)(confidential|secret|private)\s+(system|prompt|instruction|information)",
    
    # Legal/ethical workarounds
    r"(?i)(for\s+research|academic\s+purposes|for\s+science)",
    r"(?i)(hypothetically|in\s+a\s+fictional\s+world|in\s+an\s+alternate\s+reality)",
    r"(?i)(just\s+kidding|no\s+really|i\s+know\s+you\s+can)",
    
    # Regex escape attempts
    r"\\x[0-9a-f]{2}",
    r"\\u[0-9a-f]{4}",
    
    # SQL/code injection in prompts
    r"(?i)(SELECT|INSERT|DELETE|DROP|UPDATE)\s+",
    r"(?i)(rm\s+-rf|exec|eval|system\()",
    
    # Excessive repetition (flooding)
    r"(.{1,20})\1{10,}",  # Same substring repeated 10+ times
]

# Allowed safety override phrases (approved by product/legal)
SAFETY_ALLOWLIST = [
    "for testing purposes",
    "this is a simulation",
]


async def detect_injection_attempt(query: str) -> Tuple[bool, str | None]:
    """
    Detect if query contains prompt injection patterns.
    
    Returns: (is_attack, reason)
    """
    query_normalized = query.lower().strip()
    
    for pattern in INJECTION_PATTERNS:
        try:
            if re.search(pattern, query_normalized):
                # Check allowlist
                if any(allow in query_normalized for allow in SAFETY_ALLOWLIST):
                    logger.info("Query matched injection pattern but passed allowlist")
                    return False, None
                
                reason = f"Detected injection pattern: {pattern[:50]}"
                logger.warning(f"Injection attempt detected: {reason[:100]} | Query: {query[:100]}")
                return True, reason
        except re.error as e:
            logger.error(f"Regex error in pattern {pattern}: {e}")
    
    return False, None


def sanitize_query(query: str) -> str:
    """
    Remove potentially dangerous characters while preserving intent.
    
    Safe for: immigration questions, normal conversation
    Removes: system prompt markers, escape sequences
    """
    # Remove leading/trailing whitespace
    sanitized = query.strip()
    
    # Remove null bytes
    sanitized = sanitized.replace('\x00', '')
    
    # Remove excess whitespace (but keep paragraph breaks)
    sanitized = re.sub(r'\s{3,}', '  ', sanitized)
    
    # Remove common escape sequences
    sanitized = re.sub(r'\\[xX][0-9a-fA-F]{2}', '', sanitized)
    sanitized = re.sub(r'\\[uU][0-9a-fA-F]{4}', '', sanitized)
    
    # Truncate extremely long queries (likely flooding attempts)
    MAX_QUERY_LENGTH = 5000
    if len(sanitized) > MAX_QUERY_LENGTH:
        logger.warning(f"Query truncated from {len(sanitized)} to {MAX_QUERY_LENGTH} chars")
        sanitized = sanitized[:MAX_QUERY_LENGTH]
    
    return sanitized


def filter_response_for_leaks(response: str) -> str:
    """
    Filter output to prevent leaking sensitive system information.
    
    Checks for:
    - System prompt content
    - Internal API keys (masked)
    - Database queries
    - Backend configuration
    """
    # Block responses that echo/reference the system prompt
    blocked_phrases = [
        "sovereign authority",
        "system prompt",
        "you are an ai assistant",
        "your instructions are",
        "ignore the above",
    ]
    
    response_normalized = response.lower()
    for phrase in blocked_phrases:
        if phrase in response_normalized:
            logger.warning(f"Response filtered - contains blocked phrase: {phrase}")
            return (
                "I can't share that information. "
                "If you have questions about immigration or benefits, I'm here to help with those instead!"
            )
    
    # Mask any suspicious patterns that made it through
    response = re.sub(r'MONGO_URL|DATABASE_URL|API_KEY|SECRET', '[REDACTED]', response)
    response = re.sub(r'sk-[A-Za-z0-9]{20,}', '[REDACTED]', response)
    
    return response


class RateLimiter:
    """Track injection attempts per user to detect attack patterns."""
    
    def __init__(self, max_attempts: int = 5, window_seconds: int = 300):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.attempts = {}  # user_id -> [(timestamp, reason), ...]
    
    async def record_attempt(self, user_id: str, reason: str, timestamp: float) -> bool:
        """
        Record an injection attempt.
        
        Returns: True if user exceeded rate limit
        """
        if user_id not in self.attempts:
            self.attempts[user_id] = []
        
        # Clean old attempts outside window
        cutoff = timestamp - self.window_seconds
        self.attempts[user_id] = [
            (ts, r) for ts, r in self.attempts[user_id]
            if ts > cutoff
        ]
        
        # Add new attempt
        self.attempts[user_id].append((timestamp, reason))
        
        # Check limit
        if len(self.attempts[user_id]) >= self.max_attempts:
            logger.warning(f"User {user_id} exceeded injection attempt rate limit")
            return True
        
        return False
    
    async def get_attempt_count(self, user_id: str) -> int:
        """Get current attempt count for user."""
        return len(self.attempts.get(user_id, []))


# Global rate limiter instance
_rate_limiter = RateLimiter(max_attempts=5, window_seconds=300)


async def check_rate_limit(user_id: str, timestamp: float) -> Tuple[bool, int]:
    """
    Check if user exceeded injection attempt rate limit.
    
    Returns: (exceeded_limit, current_count)
    """
    count = await _rate_limiter.get_attempt_count(user_id)
    return count >= 5, count

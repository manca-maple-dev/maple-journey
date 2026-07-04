import re

# Test the classification logic directly
_SIMPLE_PATTERNS = re.compile(r"^(hi|hello|hey|thanks|thank you|ok|okay|yes|no|sure|got it|understood|great|\?+)$", re.IGNORECASE)
_DEEP_PATTERNS = re.compile(r"(calculate|full analysis|step.by.step|all documents|complete checklist|case review|crs score|points breakdown|compare.*pathway|which.*better|should i|strategy|appeal|inadmissib|misrepresent|refused|criminal|medical|sponsor|divorce|custody)", re.IGNORECASE)
_RESEARCH_PATTERNS = re.compile(r"(how long|processing time|timeline|deadline|expire|renewal|extension|eligible|requirement|pathway|program|provincial|pnp|express entry|pgwp|lmia|bowp|explain|difference between|what is|what are|can i|am i|do i need)", re.IGNORECASE)

CHAT_COMPLEXITY_COSTS = {"simple": 1, "standard": 2, "research": 3, "deep": 5}

def classify_query(message: str):
    text = (message or "").strip()
    if not text:
        return "simple", 1
    if len(text) < 20 or _SIMPLE_PATTERNS.match(text):
        return "simple", CHAT_COMPLEXITY_COSTS["simple"]
    if _DEEP_PATTERNS.search(text):
        return "deep", CHAT_COMPLEXITY_COSTS["deep"]
    if _RESEARCH_PATTERNS.search(text) or len(text) > 120:
        return "research", CHAT_COMPLEXITY_COSTS["research"]
    return "standard", CHAT_COMPLEXITY_COSTS["standard"]

# Test cases
tests = [
    "Hi",
    "How do I qualify for PR?",
    "Calculate my CRS score",
    "What is a work permit",
    "I need a full analysis of my express entry profile with all documents and step-by-step checklist for understanding my eligibility",
]

print("🔬 INTELLIGENT QUERY CLASSIFIER TEST\n")
for t in tests:
    complexity, cost = classify_query(t)
    print(f"{cost:1d} credit{'s' if cost != 1 else ' '} [{complexity:8s}] {t[:60]}")

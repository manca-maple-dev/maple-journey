"""Turns a user's onboarding profile into a compact, AI-readable context block.
Shared by the Maple chat and the Maple Wingman briefing so the companion understands
who it is talking to — without ever fabricating facts."""
from typing import Optional


def _join(v):
    if isinstance(v, list):
        return ", ".join(str(x) for x in v if x)
    return v


def conversation_language(user: dict) -> str:
    """Infer Maple's reply language from the user's profile without extra settings."""
    profile = user.get("profile") or {}
    preferred = str(profile.get("preferred_response_language") or "").strip().lower()
    if preferred in {"english", "french"}:
        return preferred.capitalize()
    languages = profile.get("languages_spoken") or []
    if isinstance(languages, str):
        languages = [languages]
    normalized = {str(item).strip().lower() for item in languages if item}
    province = str(profile.get("province_of_residence") or profile.get("intended_province") or "").upper()
    if "french" in normalized or province in {"QC", "QUEBEC", "NB", "NEW BRUNSWICK"}:
        return "French"
    return "English"


def conversation_language_instruction(user: dict) -> str:
    language = conversation_language(user)
    if language == "French":
        return (
            "\n\nLANGUAGE RULE: Reply in simple French. Keep sentences short, clear, and practical. "
            "Avoid jargon. If the user asks for English, switch immediately."
        )
    return (
        "\n\nLANGUAGE RULE: Reply in simple English. Keep sentences short, clear, and practical. "
        "Avoid jargon. If the user asks for French, switch immediately."
    )


def profile_summary(user: dict) -> str:
    p = user.get("profile") or {}
    if not p:
        return ""
    rows = [
        ("Preferred name", p.get("preferred_name")),
        ("Pronouns", p.get("pronouns")),
        ("Journey stage", p.get("arrival_status")),
        ("Immigration category", p.get("immigration_category")),
        ("Visa subtype", p.get("visa_subtype")),
        ("Country of birth", p.get("country_of_birth")),
        ("Citizenship", p.get("country_of_citizenship")),
        ("Languages", _join(p.get("languages_spoken"))),
        ("City", p.get("current_city")),
        ("Province", p.get("province_of_residence") or p.get("intended_province")),
        ("Needs legal help for", _join(p.get("legal_topics"))),
        ("Preferred update frequency", p.get("update_frequency")),
        ("Preferred guidance style", p.get("guidance_style")),
        ("Postal prefix", p.get("current_postal_prefix")),
        ("Arrival date in Canada", p.get("arrival_date_canada")),
        ("Work permit expiry", p.get("work_permit_expiry")),
        ("Study permit expiry", p.get("study_permit_expiry")),
        ("Marital status", p.get("marital_status")),
        ("Dependents", p.get("dependents")),
        ("Housing", p.get("housing_status")),
        ("Employment status", p.get("employment_status")),
        ("Occupation", p.get("current_occupation")),
        ("Years of experience", p.get("years_experience")),
        ("Has SIN", p.get("has_sin")),
        ("Banking", p.get("banking_status")),
        ("Health coverage", p.get("health_coverage_status")),
        ("Has family doctor", p.get("has_family_doctor")),
        ("Religion", p.get("religion")),
        ("Cuisine preferences", _join(p.get("cuisine_preferences"))),
        ("Interests", _join(p.get("hobbies"))),
    ]
    bits = [f"{label}: {value}" for label, value in rows if value not in (None, "", [])]
    if not bits:
        return ""
    return (
        "\n\nUSER PROFILE (use this to tailor your guidance to their exact situation. "
        "Still cite official sources and never fabricate facts, fees, or dates):\n- "
        + "\n- ".join(bits)
    )


def legal_personalization_context(user: dict) -> dict:
    """Extract the user context that matters for legal/government ranking."""
    p = user.get("profile") or {}
    province = (p.get("province_focus") or p.get("province_of_residence") or p.get("intended_province") or "").strip()
    newcomer_type = (user.get("newcomer_type") or p.get("immigration_category") or "").strip()
    legal_topics = p.get("legal_topics") or []
    if isinstance(legal_topics, str):
        legal_topics = [legal_topics]
    return {
        "province": province,
        "newcomer_type": newcomer_type,
        "legal_topics": [str(topic).strip().lower() for topic in legal_topics if topic],
        "guidance_style": str(p.get("guidance_style") or "").strip().lower(),
        "update_frequency": str(p.get("update_frequency") or "").strip().lower(),
        "preferred_response_language": str(p.get("preferred_response_language") or "").strip().lower(),
    }

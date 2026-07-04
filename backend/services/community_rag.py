"""Community RAG - Search + inject real community data with addresses & phone numbers.

When user asks for resources, services, help, we pull actual communities from database.
Returns formatted contact info: name, address, phone, hours, specialization.
"""
import logging
from typing import List, Dict, Optional
from core.db import db

logger = logging.getLogger("maplejourney.community_rag")


async def search_communities_by_keyword(
    keyword: str, 
    province: Optional[str] = None,
    city: Optional[str] = None,
    limit: int = 5
) -> List[Dict]:
    """
    Search communities database by keyword + location.
    
    Returns list of communities with:
    - name, address, phone, email
    - specialization (settlement, legal, health, etc)
    - hours, website
    - rating/verification status
    
    Keyword matches: name, specialization, services offered
    """
    try:
        query = {}
        
        # Keyword search
        if keyword:
            query["$text"] = {"$search": keyword}
        
        # Location filters
        if province:
            query["province"] = province
        if city:
            query["city"] = {"$regex": city, "$options": "i"}
        
        # Fetch + sort by rating/verified
        communities = await db.communities.find(query)\
            .sort([("verified", -1), ("rating", -1)])\
            .limit(limit)\
            .to_list(limit)
        
        # Format for display
        formatted = []
        for c in communities:
            formatted.append({
                "name": c.get("name"),
                "address": f"{c.get('address', '')}, {c.get('city', '')}, {c.get('province', '')}",
                "phone": c.get("phone"),
                "email": c.get("email"),
                "website": c.get("website"),
                "hours": c.get("hours"),
                "specialization": c.get("specialization"),
                "services": c.get("services", []),
                "verified": c.get("verified", False),
                "rating": c.get("rating", 0),
                "languages": c.get("languages", []),
            })
        
        return formatted
    except Exception as e:
        logger.error(f"Community search failed: {e}")
        return []


async def build_community_context(
    message: str,
    province: Optional[str] = None,
    city: Optional[str] = None
) -> str:
    """
    Detect if user is asking for resources/communities/help.
    If yes, search communities and return formatted contact info to inject into system prompt.
    """
    
    # Keywords that trigger community search
    community_keywords = [
        "help", "support", "services", "resource", "clinic", "legal",
        "settlement", "housing", "job", "employment", "training",
        "health", "mental health", "counseling", "community",
        "where", "phone", "address", "contact", "near me",
        "how do i find", "can you recommend", "what services",
        "looking for", "need help", "assist"
    ]
    
    message_lower = message.lower()
    should_search = any(kw in message_lower for kw in community_keywords)
    
    if not should_search:
        return ""
    
    # Extract keywords from message
    keywords = []
    for word in message_lower.split():
        if len(word) > 3 and word not in community_keywords:
            keywords.append(word)
    
    if not keywords:
        keywords = community_keywords[:3]
    
    # Search communities
    communities = await search_communities_by_keyword(
        keyword=" ".join(keywords[:3]),
        province=province,
        city=city,
        limit=10
    )
    
    if not communities:
        return ""
    
    # Format as context for system prompt
    context = "\n\n" + "="*70 + "\n"
    context += "🏘️ VERIFIED COMMUNITY RESOURCES (Real contact info):\n"
    context += "="*70 + "\n\n"
    
    for i, c in enumerate(communities, 1):
        verified_badge = "✅ VERIFIED" if c["verified"] else "⚠️ Not verified"
        rating_str = f"⭐ {c['rating']}/5" if c["rating"] > 0 else ""
        
        context += f"{i}. {c['name']} {verified_badge}\n"
        if c["specialization"]:
            context += f"   📋 Specialization: {c['specialization']}\n"
        context += f"   📍 Address: {c['address']}\n"
        context += f"   ☎️  Phone: {c['phone']}\n"
        if c["email"]:
            context += f"   📧 Email: {c['email']}\n"
        if c["website"]:
            context += f"   🌐 Website: {c['website']}\n"
        if c["hours"]:
            context += f"   🕐 Hours: {c['hours']}\n"
        if c["languages"]:
            context += f"   🗣️  Languages: {', '.join(c['languages'])}\n"
        if c["services"]:
            context += f"   ✓ Services: {', '.join(c['services'][:5])}\n"
        if rating_str:
            context += f"   {rating_str}\n"
        context += "\n"
    
    context += "="*70 + "\n"
    context += "INSTRUCTIONS FOR MAPLE:\n"
    context += "- When user asks for resources/help, provide the phone number and address FIRST (not last)\n"
    context += "- Format: '📍 [Name], [Address] ☎️ [Phone]'\n"
    context += "- Emphasize verified communities (✅)\n"
    context += "- Include website link for online booking\n"
    context += "- Mention languages spoken if relevant to user\n"
    context += "- Give 2-3 best matches (not all 10)\n"
    context += "="*70 + "\n\n"
    
    return context

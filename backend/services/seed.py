"""Startup seeding: indexes, admin account, and catalog seed data."""
import os
import uuid
import logging
from datetime import datetime, timezone, timedelta

from core.config import DEFAULT_FEATURES
from core.db import db
from core.security import hash_password, verify_password
from services.users import get_global_features
from services.source_registry import ensure_source_registry, materialize_legal_resources_from_registry, refresh_legal_sources_and_resources

logger = logging.getLogger("maplejourney.seed")


async def run_startup():
    await db.users.create_index("email", unique=True)
    # Password reset tokens auto-expire via a TTL index on `expires_at`.
    await db.password_reset_tokens.create_index("expires_at", expireAfterSeconds=0)
    await db.password_reset_tokens.create_index("token_hash")
    await db.companion_actions.create_index("user_id")
    await db.companion_actions.create_index([("created_at", -1)])
    await db.companion_followups.create_index([("status", 1), ("due_at", 1)])
    await db.companion_followups.create_index("user_id")

    admin_email = os.environ["ADMIN_EMAIL"].lower()
    admin_password = os.environ["ADMIN_PASSWORD"]
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        await db.users.insert_one({
            "email": admin_email,
            "password_hash": hash_password(admin_password),
            "name": "MapleJourney Admin",
            "role": "admin",
            "features": DEFAULT_FEATURES.copy(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}})

    await get_global_features()

    if await db.jobs.count_documents({}) == 0:
        await db.jobs.insert_many([
            {"id": str(uuid.uuid4()), "title": "Software Developer", "company": "Shopify", "location": "Toronto, ON", "salary": "$95k–$130k", "type": "Full-time", "match": 94, "tags": ["Tech", "LMIA-exempt"], "logo": "SH"},
            {"id": str(uuid.uuid4()), "title": "Registered Nurse", "company": "Vancouver Coastal Health", "location": "Vancouver, BC", "salary": "$78k–$102k", "type": "Full-time", "match": 88, "tags": ["Healthcare", "In-demand"], "logo": "VC"},
            {"id": str(uuid.uuid4()), "title": "Financial Analyst", "company": "RBC", "location": "Montreal, QC", "salary": "$70k–$92k", "type": "Full-time", "match": 81, "tags": ["Finance"], "logo": "RB"},
            {"id": str(uuid.uuid4()), "title": "Truck Driver (AZ)", "company": "Bison Transport", "location": "Winnipeg, MB", "salary": "$62k–$85k", "type": "Full-time", "match": 76, "tags": ["Trades", "PNP-friendly"], "logo": "BT"},
            {"id": str(uuid.uuid4()), "title": "UX Designer", "company": "Wealthsimple", "location": "Remote (Canada)", "salary": "$88k–$118k", "type": "Remote", "match": 90, "tags": ["Tech", "Design"], "logo": "WS"},
            {"id": str(uuid.uuid4()), "title": "Construction Estimator", "company": "PCL", "location": "Calgary, AB", "salary": "$72k–$98k", "type": "Full-time", "match": 73, "tags": ["Trades"], "logo": "PC"},
        ])

    if await db.benefits.count_documents({}) == 0:
        await db.benefits.insert_many([
            {"id": str(uuid.uuid4()), "title": "Canada Child Benefit (CCB)", "category": "Family", "description": "Tax-free monthly payment to help with the cost of raising children under 18.", "eligibility": "Parents/guardians who are residents for tax purposes.", "amount": "Up to $7,787/yr per child"},
            {"id": str(uuid.uuid4()), "title": "GST/HST Credit", "category": "Tax", "description": "Quarterly tax-free payment to offset sales tax for low-income individuals & families.", "eligibility": "Residents 19+ filing taxes.", "amount": "Up to $519/yr"},
            {"id": str(uuid.uuid4()), "title": "Provincial Health Card", "category": "Healthcare", "description": "Publicly funded health coverage. Apply as soon as you arrive in your province.", "eligibility": "New permanent residents & many work permit holders.", "amount": "Free coverage"},
            {"id": str(uuid.uuid4()), "title": "Employment Insurance (EI)", "category": "Employment", "description": "Temporary income support if you lose your job through no fault of your own.", "eligibility": "Worked required insurable hours.", "amount": "Up to 55% of earnings"},
            {"id": str(uuid.uuid4()), "title": "Canada Workers Benefit", "category": "Tax", "description": "Refundable tax credit for low-income working individuals and families.", "eligibility": "Working residents meeting income thresholds.", "amount": "Up to $1,590/yr"},
            {"id": str(uuid.uuid4()), "title": "Settlement Services (IRCC-funded)", "category": "Settlement", "description": "Free language classes, job search help, and community connections for newcomers.", "eligibility": "Permanent residents & protected persons.", "amount": "Free programs"},
        ])

    if await db.resources.count_documents({}) == 0:
        await db.resources.insert_many([
            {"id": str(uuid.uuid4()), "title": "Express Entry Explained", "category": "PR Pathways", "description": "How the CRS points system works and how to boost your score.", "url": "#"},
            {"id": str(uuid.uuid4()), "title": "Provincial Nominee Programs", "category": "PR Pathways", "description": "Province-specific streams that can fast-track your PR.", "url": "#"},
            {"id": str(uuid.uuid4()), "title": "Getting Your SIN", "category": "First Steps", "description": "Your Social Insurance Number is required to work in Canada.", "url": "#"},
            {"id": str(uuid.uuid4()), "title": "Opening a Bank Account", "category": "First Steps", "description": "Newcomer banking packages and what documents you need.", "url": "#"},
            {"id": str(uuid.uuid4()), "title": "Renting Your First Home", "category": "Housing", "description": "Understanding leases, deposits, and tenant rights.", "url": "#"},
            {"id": str(uuid.uuid4()), "title": "Filing Taxes as a Newcomer", "category": "Taxes", "description": "Your first tax return and benefits you can claim.", "url": "#"},
        ])

    if await db.content.count_documents({"_id": "landing"}) == 0:
        await db.content.insert_one({"_id": "landing", "data": {
            "hero_title": "Your journey to Canada, guided every step",
            "hero_subtitle": "MapleJourney turns the maze of visas, PR, jobs and benefits into one clear, personalized path — with cited guidance from IRCC, CRA & Service Canada.",
            "cta_label": "Start free",
        }})

    if await db.announcements.count_documents({}) == 0:
        await db.announcements.insert_many([
            {"id": str(uuid.uuid4()), "title": "Express Entry draw results", "body": "Latest CRS cut-off was 481. Check your updated score in your dashboard.", "tone": "info", "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "title": "New: Maple companion upgrade", "body": "Maple now understands provincial nominee programs in more detail.", "tone": "success", "created_at": datetime.now(timezone.utc).isoformat()},
        ])

    await ensure_source_registry(db)
    legal_count = await materialize_legal_resources_from_registry(db)
    logger.info(f"Legal resources materialized: {legal_count} sources")
    
    # Ensure at least some legal resources exist
    existing_legal = await db.legal_resources.count_documents({})
    if existing_legal == 0:
        logger.warning("No legal resources found after materialization. Reseeding...")
        await refresh_legal_sources_and_resources(db)

    logger.info("MapleJourney startup complete.")

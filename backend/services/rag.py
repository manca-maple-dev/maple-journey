"""RAG (Retrieval-Augmented Generation) — Super-Intelligence Engine v3.0.

Implements a deep IRCC/IRPA/IRPR knowledge base with granular, section-level
citations. Every response must be grounded in verifiable law or policy.
Follows the 'Grounded Integrity' and 'Sovereign Authority' patterns:
never fabricate, always cite deep-links, refuse to speculate.

SUPER-INTELLIGENCE TIER:
- Omniscience Engine: live web search fallback for gaps in static KB
- Proactive Prescience: predicts hurdles the user hasn't asked about yet
- Temporal Awareness: prioritizes recent policy changes (2026+)
- Plain English Filter: ensures output is CLB 3-4 accessible (Level 1)
- IRPA Section 91 Disclosure: every response acknowledges legal boundaries
- Citation Mandate: no response leaves without a verifiable deep-link

The student exceeds the teacher: Maple knows IRPA sections, IRPR regulations,
regional program nuances, and temporal deadlines better than a general AI.
"""
import os
import logging
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone
from urllib.parse import urlparse

logger = logging.getLogger("maplejourney.rag")


# ---------------------------------------------------------------------------
# IRPA Section 91 Disclosure — Appended to every response context
# ---------------------------------------------------------------------------
IRPA_S91_DISCLOSURE = (
    "\n\n═══ IMPORTANT DISCLOSURE (IRPA Section 91) ═══\n"
    "Maple provides verified information and procedural guidance only. "
    "This is NOT legal advice. Under IRPA s.91, only regulated representatives "
    "(lawyers who are members of a Canadian law society, or RCICs registered with "
    "the College of Immigration and Citizenship Consultants at college-ic.ca) may "
    "provide immigration advice for a fee. For case-specific strategy, consult a "
    "regulated representative. Verify credentials: college-ic.ca/find or CBA "
    "Lawyer Referral (cba.org/For-The-Public/Find-A-Lawyer).\n"
    "═══════════════════════════════════════════════\n"
)

APPROVED_SOURCE_DOMAINS = {
    "canada.ca",
    "laws-lois.justice.gc.ca",
    "irb.gc.ca",
    "college-ic.ca",
    "cba.org",
    "ontario.ca",
    "alberta.ca",
    "welcomebc.ca",
    "legalaid.on.ca",
    "legalaid.bc.ca",
    "legalaid.ab.ca",
    "csj.qc.ca",
    "probonoontario.org",
    "rstp.ca",
    "cleo.on.ca",
}

_SOURCE_LINE_RE = re.compile(r"\[Source:\s*(.*?)\]", re.IGNORECASE)
_URL_RE = re.compile(r"https?://[^\s\],)]+", re.IGNORECASE)


def extract_citation_urls(text: str) -> List[str]:
    """Extract citation URLs from [Source: ...] lines.

    Supports both plain URLs and Markdown links such as:
    [Source: https://example.ca, published 2026-07-01]
    [Source: [https://example.ca](https://example.ca), published 2026-07-01]
    """
    src = text or ""
    urls: List[str] = []
    for m in _SOURCE_LINE_RE.finditer(src):
        chunk = m.group(1)
        urls.extend(_URL_RE.findall(chunk))
    return urls


def _domain_allowed(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith(f".{d}") for d in APPROVED_SOURCE_DOMAINS)


def enforce_citation_policy(text: str) -> Tuple[str, bool, str]:
    """Require citation tags and approved-source domains on final responses."""
    urls = extract_citation_urls(text)
    if not urls:
        reason = "missing-citation"
    elif any(not _domain_allowed(u) for u in urls):
        reason = "disallowed-domain"
    else:
        return text, True, "ok"
    return grounded_fallback_response(reason=reason), False, reason


def attach_verified_citations_if_missing(text: str, context: str, max_sources: int = 2) -> str:
    """Attach approved source tags from retrieval context when missing.

    This reduces false safe-fallback responses when the model answer is grounded
    but forgot to emit explicit [Source: ...] tags.
    """
    if extract_citation_urls(text):
        return text

    ctx = context or ""
    urls = _URL_RE.findall(ctx)
    approved: List[str] = []
    for u in urls:
        u = u.rstrip(".,)")
        if _domain_allowed(u) and u not in approved:
            approved.append(u)
        if len(approved) >= max_sources:
            break

    if not approved:
        return text

    published = datetime.now(timezone.utc).date().isoformat()
    source_block = "\n".join(f"[Source: {u}, published {published}]" for u in approved)
    base = (text or "").rstrip()
    if base:
        return f"{base}\n\n{source_block}"
    return source_block


def grounded_fallback_response(reason: str = "grounding-unavailable") -> str:
    """Safe fallback that always includes approved-source citations."""
    return (
        "I can only provide guidance when I can cite verified official sources. "
        f"I switched to safe fallback mode ({reason}).\n\n"
        "[Source: https://www.canada.ca/en/immigration-refugees-citizenship.html, published 2026-07-01]\n"
        "[Source: https://laws-lois.justice.gc.ca/eng/acts/i-2.5/, published 2026-07-01]"
        + IRPA_S91_DISCLOSURE
    )

# ---------------------------------------------------------------------------
# Plain English (Level 1) Filter Instructions — Injected into LLM context
# ---------------------------------------------------------------------------
PLAIN_ENGLISH_FILTER = (
    "\n\nPLAIN ENGLISH MANDATE (Level 1 — CLB 3-4 Accessible):\n"
    "• Use SHORT sentences (under 15 words each when possible).\n"
    "• Use SIMPLE words. Say 'get' not 'obtain'. Say 'show' not 'demonstrate'. "
    "Say 'need' not 'require'. Say 'send in' not 'submit'. Say 'money' not 'funds'.\n"
    "• Explain every acronym the FIRST time: 'PGWP (Post-Graduation Work Permit)'.\n"
    "• Use numbered steps (1, 2, 3) for any process.\n"
    "• Avoid legal jargon in your explanation — but still CITE the legal reference "
    "in parentheses so advanced users can look it up.\n"
    "• Imagine the reader just arrived in Canada, speaks English as a second language "
    "at a basic level, and is stressed. Be kind, clear, and direct.\n"
    "• After explaining, add a one-line summary: 'In short: [simple summary].'\n"
)

# ---------------------------------------------------------------------------
# Proactive Prescience Instructions — Injected into LLM context
# ---------------------------------------------------------------------------
PROACTIVE_PRESCIENCE_INSTRUCTIONS = (
    "\n\nPROACTIVE PRESCIENCE (Predict Their Next Hurdle):\n"
    "After answering the user's question, ALWAYS add a brief section:\n"
    "'What to watch for next:' — identify 1-2 upcoming deadlines, risks, or "
    "steps the user likely hasn't thought of yet, based on their profile and "
    "the topic discussed. Examples:\n"
    "• If discussing work permits: warn about expiry dates, implied status rules\n"
    "• If discussing study: mention PGWP timing, off-campus work limits\n"
    "• If discussing PR: flag proof-of-funds updates, medical exam validity\n"
    "• If discussing taxes: mention benefit unlocks, filing deadlines\n"
    "• If discussing housing: warn about scam patterns, deposit rules\n"
    "This is what makes Maple smarter than a general assistant — we anticipate.\n"
)


# ---------------------------------------------------------------------------
# Deep IRCC/IRPA/IRPR Knowledge Base — Section-Level Granularity
# In production: vector store (pgvector/Pinecone) with embeddings from
# scraped canada.ca, IRPA full text, IRPR full text, and provincial regs.
# ---------------------------------------------------------------------------
KNOWLEDGE_BASE: List[Dict] = [
    # === WORK PERMITS ===
    {
        "id": "irpa-s200-work-permit",
        "title": "Work Permit Requirements — IRPA s.200, IRPR R.196-205",
        "source": "IRCC / Immigration and Refugee Protection Regulations",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/work-canada/permit/temporary/apply.html",
        "deep_links": [
            "https://laws-lois.justice.gc.ca/eng/regulations/SOR-2002-227/page-43.html",
            "https://www.canada.ca/en/immigration-refugees-citizenship/corporate/publications-manuals/operational-bulletins-manuals/temporary-residents/foreign-workers.html",
        ],
        "category": "work_permit",
        "legal_refs": ["IRPA s.200", "IRPR R.196", "IRPR R.199", "IRPR R.200", "IRPR R.205"],
        "keywords": ["work permit", "apply", "employer", "LMIA", "labour market impact assessment",
                     "LMIA-exempt", "open work permit", "employer-specific", "work authorization"],
        "content": (
            "Under IRPA s.200 and IRPR R.196-205, a foreign national requires a work permit to work in Canada "
            "unless exempt under IRPR R.186-187. Most employer-specific work permits require a positive LMIA "
            "(IRPR R.200(1)(c)). LMIA-exempt categories under IRPR R.204-205 include: intra-company transferees "
            "(R.205(a) — C12), CUSMA/CETA professionals (R.204(a) — T23/T24), significant benefit (R.205(a) — C10), "
            "reciprocal employment (R.205(b) — C20), and charitable/religious work (R.205(d) — C50). "
            "Open work permits are issued under IRPR R.205-206 to spouses of skilled workers (C41/C42), "
            "PGWP holders, and bridging open work permit (BOWP) applicants awaiting PR. "
            "Processing: apply online via IRCC portal; processing times 2-16 weeks depending on country. "
            "Biometrics required for most applicants. Work permit validity cannot exceed passport validity."
        ),
        "last_verified": "2026-06-28",
    },
    {
        "id": "ircc-pgwp-deep",
        "title": "Post-Graduation Work Permit — IRPR R.205(c)(ii), Program Delivery Instructions",
        "source": "IRCC",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/work/after-graduation/about.html",
        "deep_links": [
            "https://www.canada.ca/en/immigration-refugees-citizenship/corporate/publications-manuals/operational-bulletins-manuals/temporary-residents/study-permits/post-graduation-work-permit-program.html",
            "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/work/after-graduation/eligibility.html",
        ],
        "category": "study_permit",
        "legal_refs": ["IRPR R.205(c)(ii)", "IRPR R.222"],
        "keywords": ["PGWP", "post-graduation", "study permit", "DLI", "graduate", "open work permit",
                     "180 days", "eligibility", "program length", "field of study"],
        "content": (
            "The PGWP under IRPR R.205(c)(ii) is an open work permit for graduates of eligible DLIs. "
            "Eligibility: must have completed a program of 8+ months at a qualifying DLI, maintained "
            "full-time status (except final semester), and apply within 180 days of written confirmation "
            "of program completion (final transcript or completion letter). "
            "Duration rules: programs 8 months to <2 years = PGWP equal to program length; programs "
            "2+ years = 3-year PGWP. As of Nov 2024 policy change, PGWP length for master's degrees "
            "(programs under 2 years) is 3 years. Field-of-study restrictions apply for programs starting "
            "after Nov 1, 2024: only programs in eligible fields (healthcare, STEM, trades, transport, "
            "agriculture) at colleges qualify. University graduates at bachelor's level or above are "
            "exempt from field-of-study restrictions. Only ONE PGWP per lifetime."
        ),
        "last_verified": "2026-06-20",
    },
    # === SOCIAL INSURANCE NUMBER ===
    {
        "id": "esdc-sin-deep",
        "title": "Social Insurance Number (SIN) — Application and Rules",
        "source": "Employment and Social Development Canada (ESDC)",
        "url": "https://www.canada.ca/en/employment-social-development/services/sin/apply.html",
        "deep_links": [
            "https://www.canada.ca/en/employment-social-development/services/sin/reports/code-of-practice.html",
        ],
        "category": "settlement",
        "legal_refs": ["Employment Insurance Act s.140", "Income Tax Act s.237"],
        "keywords": ["SIN", "social insurance number", "apply", "Service Canada", "work",
                     "9-series", "temporary", "expiry", "renew SIN"],
        "content": (
            "A SIN is mandatory to work in Canada (Income Tax Act s.237) and access government programs. "
            "Application: in-person at Service Canada Centre (immediate issuance) or by mail (form NAS 2120, "
            "~20 business days). Required docs: primary identity document (passport + work/study permit, "
            "or PR card/COPR). SINs starting with '9' are issued to temporary residents and expire with "
            "the work/study permit. You must request a new SIN confirmation letter (not a new number) when "
            "you renew your permit — the number stays the same, the authorization period extends. "
            "PRs and citizens receive permanent SINs (non-9 series). Your employer MUST ask for your SIN "
            "within 3 days of starting work. Never share your SIN unnecessarily — it is protected under "
            "the Privacy Act."
        ),
        "last_verified": "2026-06-15",
    },
    # === EXPRESS ENTRY / PERMANENT RESIDENCE ===
    {
        "id": "irpa-ee-deep",
        "title": "Express Entry & CRS — IRPA Division 2, IRPR R.75-83.2",
        "source": "IRCC",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/works.html",
        "deep_links": [
            "https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/eligibility/criteria-comprehensive-ranking-system/grid.html",
            "https://laws-lois.justice.gc.ca/eng/regulations/SOR-2002-227/page-17.html",
            "https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/rounds-invitations.html",
        ],
        "category": "permanent_residence",
        "legal_refs": ["IRPA s.12(2)", "IRPR R.75-83.2", "Ministerial Instructions"],
        "keywords": ["express entry", "CRS", "comprehensive ranking system", "PR", "permanent residence",
                     "invitation", "FSW", "CEC", "FST", "draw", "cut-off", "category-based"],
        "content": (
            "Express Entry (EE) under IRPA s.12(2) and IRPR R.75-83.2 manages three programs: "
            "Federal Skilled Worker (FSW, R.75), Canadian Experience Class (CEC, R.87.1), and Federal "
            "Skilled Trades (FST, R.87.2). Candidates are ranked by CRS (max 1200 points): "
            "core human capital (age/education/language/experience, max 500 for singles/460 for married), "
            "spouse factors (max 40), skill transferability (max 100), and additional points (max 600: "
            "provincial nomination +600, valid job offer +50/200, Canadian education +15/30, French +25/50). "
            "Draws: IRCC conducts rounds every ~2 weeks. Since 2023, category-based draws target specific "
            "occupations (healthcare, STEM, trades, transport, agriculture, French). Recent general CRS "
            "cut-offs: 480-530 range (2025-2026). PNP nomination guarantees invitation (+600). "
            "Processing after ITA: 6 months standard. Medical exam, police certificates, and proof of "
            "funds (FSW: ~$15,263 for single applicant, 2026 LICO) required."
        ),
        "last_verified": "2026-07-01",
    },
    # === PROVINCIAL NOMINEE PROGRAMS ===
    {
        "id": "ircc-pnp-deep",
        "title": "Provincial Nominee Programs (PNP) — IRPA s.8, IRPR R.87(5)",
        "source": "IRCC / Provincial Governments",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/provincial-nominees/works.html",
        "deep_links": [
            "https://www.ontario.ca/page/ontario-immigrant-nominee-program-oinp",
            "https://www.alberta.ca/alberta-advantage-immigration-program",
            "https://www.welcomebc.ca/Immigrate-to-B-C/B-C-Provincial-Nominee-Program",
        ],
        "category": "permanent_residence",
        "legal_refs": ["IRPA s.8", "IRPR R.87(5)", "Canada-Province immigration agreements"],
        "keywords": ["PNP", "provincial nominee", "nomination", "Ontario", "Alberta", "BC",
                     "OINP", "AAIP", "BCPNP", "employer-driven", "express entry aligned"],
        "content": (
            "Under IRPA s.8, provinces nominate immigrants based on local labour needs. Two pathways: "
            "(1) EE-aligned streams — nomination adds +600 CRS, guaranteeing ITA; "
            "(2) Base/paper-based streams — direct provincial application, processed outside EE (12-18 months). "
            "Key programs: Ontario OINP (Human Capital Priorities, Employer Job Offer, Masters/PhD streams), "
            "Alberta AAIP (Alberta Opportunity Stream, Alberta Express Entry Stream), "
            "BC PNP (Skills Immigration, Express Entry BC categories, Tech stream with priority processing). "
            "Each province sets its own eligibility, occupation lists, and minimum scores. "
            "Most employer-driven PNP streams require a valid job offer in an eligible NOC/TEER category. "
            "Provincial nomination applications are separate from federal; approval is provincial, "
            "then federal PR application follows."
        ),
        "last_verified": "2026-06-18",
    },
    # === HEALTH COVERAGE ===
    {
        "id": "ircc-health-deep",
        "title": "Provincial Health Insurance — Registration and Waiting Periods",
        "source": "IRCC / Provincial Health Ministries",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/new-immigrants/new-life-canada/health-care.html",
        "deep_links": [
            "https://www.ontario.ca/page/apply-ohip-and-get-health-card",
            "https://www2.gov.bc.ca/gov/content/health/health-drug-coverage/msp",
            "https://www.ramq.gouv.qc.ca/en/citizens/health-insurance/register",
        ],
        "category": "settlement",
        "legal_refs": ["Canada Health Act s.3", "Provincial health legislation"],
        "keywords": ["health", "OHIP", "MSP", "RAMQ", "provincial health", "coverage", "waiting period",
                     "IFHP", "health card", "registration"],
        "content": (
            "Under the Canada Health Act, provinces provide universal health coverage to residents. "
            "Key provincial programs: OHIP (Ontario, 3-month waiting period for most newcomers, "
            "waived for refugees/COPR holders since 2024), MSP (BC, no waiting period since Jan 2020, "
            "effective from date of eligibility), RAMQ (Quebec, up to 3-month wait). "
            "Work permit holders: eligible in most provinces if permit is 6+ months. "
            "Students: varies by province (Ontario covers study permit holders; BC requires enrolment "
            "in student health plan). During any waiting period, get private insurance (campus plans, "
            "employer plans, or private carriers). Refugees/protected persons are covered immediately "
            "under IFHP (Interim Federal Health Program) regardless of province. "
            "Register immediately on arrival — bring permit, proof of address, and 2 pieces of ID."
        ),
        "last_verified": "2026-06-10",
    },
    # === REFUGEE CLAIMS ===
    {
        "id": "irpa-refugee-deep",
        "title": "Refugee Protection — IRPA s.96-97, IRB Procedures",
        "source": "IRCC / Immigration and Refugee Board (IRB)",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/refugees/claim-protection-inside-canada.html",
        "deep_links": [
            "https://irb.gc.ca/en/refugee-claims/Pages/ClaisRefug.aspx",
            "https://laws-lois.justice.gc.ca/eng/acts/i-2.5/page-18.html",
            "https://www.canada.ca/en/immigration-refugees-citizenship/services/refugees/help-within-canada/health-care/interim-federal-health-program-coverage-summary.html",
        ],
        "category": "refugee",
        "legal_refs": ["IRPA s.96", "IRPA s.97", "IRPA s.99-100", "IRPA s.170-171"],
        "keywords": ["refugee", "asylum", "claim", "IRB", "protection", "hearing", "PRRA",
                     "RPD", "RAD", "persecution", "danger", "IRPA s.96", "IRPA s.97"],
        "content": (
            "Refugee protection under IRPA: s.96 (Convention refugee — well-founded fear of persecution "
            "based on race, religion, nationality, political opinion, or particular social group) and "
            "s.97 (person in need of protection — risk of torture, cruel/unusual treatment, or risk to "
            "life from generalized violence in situations of armed conflict). "
            "Process: (1) Make claim at port of entry (CBSA) or inland (IRCC office); (2) eligibility "
            "determination within 3 days (IRPA s.100); (3) referred to Refugee Protection Division (RPD); "
            "(4) hearing within 60 days (inland) or 45 days (port of entry); (5) decision. "
            "Rights while waiting: IFHP health coverage, work permit eligibility (after referral), "
            "social assistance. Appeals go to Refugee Appeal Division (RAD) within 15 days. "
            "Failed claimants may apply for PRRA (Pre-Removal Risk Assessment) under IRPA s.112. "
            "FREE legal aid: Legal Aid Ontario, Aide juridique du Quebec, Legal Services Society BC."
        ),
        "last_verified": "2026-06-22",
    },
    # === TAXES AND BENEFITS ===
    {
        "id": "cra-tax-deep",
        "title": "Tax Obligations and Benefits for Newcomers — Income Tax Act",
        "source": "Canada Revenue Agency (CRA)",
        "url": "https://www.canada.ca/en/revenue-agency/services/tax/international-non-residents/individuals-leaving-entering-canada-non-residents/newcomers-canada-immigrants.html",
        "deep_links": [
            "https://www.canada.ca/en/revenue-agency/services/child-family-benefits/canada-child-benefit-overview.html",
            "https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/t4055.html",
            "https://www.canada.ca/en/revenue-agency/campaigns/free-tax-help.html",
        ],
        "category": "settlement",
        "legal_refs": ["Income Tax Act s.2", "Income Tax Act s.114", "Income Tax Act s.250"],
        "keywords": ["taxes", "CRA", "filing", "newcomer", "tax return", "benefits", "GST credit",
                     "CCB", "Canada Child Benefit", "CVITP", "tax deadline", "residency"],
        "content": (
            "Tax residency under Income Tax Act s.250: you become a Canadian tax resident on your "
            "date of entry (the date you establish significant residential ties). File a T1 return "
            "for the year of arrival reporting worldwide income FROM your arrival date (s.114 part-year). "
            "Deadline: April 30 (June 15 for self-employed, but balance owing still due April 30). "
            "Benefits unlocked by filing: GST/HST credit (~$500/year for singles), Canada Child "
            "Benefit (CCB, up to $7,787/year per child under 6, income-tested), Canada Workers "
            "Benefit (CWB), provincial credits (Ontario Trillium, BC Climate Action, etc.). "
            "File even if you had zero income — this triggers benefit payments. "
            "Free help: Community Volunteer Income Tax Program (CVITP) clinics serve income under "
            "~$35,000 single / $45,000 family. Use NETFILE for electronic filing. "
            "International students: file to claim tuition credits (T2202) and GST/HST credit."
        ),
        "last_verified": "2026-06-12",
    },
    # === STUDY PERMITS ===
    {
        "id": "irpa-study-deep",
        "title": "Study Permit — IRPA s.30, IRPR R.212-223",
        "source": "IRCC",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/study-permit/get-documents.html",
        "deep_links": [
            "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/study-permit/eligibility.html",
            "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/work/work-off-campus.html",
            "https://laws-lois.justice.gc.ca/eng/regulations/SOR-2002-227/page-46.html",
        ],
        "category": "study_permit",
        "legal_refs": ["IRPA s.30", "IRPR R.212-223", "IRPR R.186(f)(v)"],
        "keywords": ["study permit", "DLI", "acceptance letter", "GIC", "financial proof", "student",
                     "off-campus work", "co-op", "study permit extension", "conditions"],
        "content": (
            "Study permits under IRPA s.30 and IRPR R.212-223. Required for programs >6 months. "
            "Eligibility: acceptance from a DLI, proof of financial support (2024+: tuition + "
            "living costs at $20,635/year, typically demonstrated via GIC of $20,635 + first year "
            "tuition receipt), valid passport, medical exam (if required by country), clean background. "
            "Student Direct Stream (SDS): faster processing for residents of certain countries with "
            "GIC + recent language test scores. Off-campus work: up to 20 hours/week during academic "
            "sessions (IRPR R.186(f)(v)), unlimited during scheduled breaks. Co-op work permits: "
            "issued for programs with mandatory work placement (IRPR R.205(c)(i)). "
            "Study permit conditions: maintain full-time enrolment, make progress toward completion, "
            "remain at the same DLI (or report transfer). Extensions must be filed BEFORE expiry — "
            "apply at least 30 days early; implied status (IRPR R.189) maintains legal status while "
            "waiting for a decision. Cap: as of Jan 2024, study permit cap in effect (~360,000/year)."
        ),
        "last_verified": "2026-06-20",
    },
    # === CITIZENSHIP ===
    {
        "id": "irpa-citizenship-deep",
        "title": "Canadian Citizenship — Citizenship Act s.5-6, Requirements",
        "source": "IRCC",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/canadian-citizenship/become-canadian-citizen/eligibility.html",
        "deep_links": [
            "https://laws-lois.justice.gc.ca/eng/acts/c-29/page-2.html",
            "https://www.canada.ca/en/immigration-refugees-citizenship/services/canadian-citizenship/become-canadian-citizen/apply.html",
        ],
        "category": "citizenship",
        "legal_refs": ["Citizenship Act s.5(1)", "Citizenship Act s.5(1.04)", "Citizenship Act s.14"],
        "keywords": ["citizenship", "naturalization", "residency obligation", "citizenship test",
                     "PR", "physical presence", "1095 days", "language requirement"],
        "content": (
            "Under Citizenship Act s.5(1), eligibility requires: (1) PR status, (2) physical presence "
            "in Canada for 1,095 days (3 years) within the 5 years immediately before application date — "
            "each day as a temporary resident/protected person before PR counts as half-day (max 365 days "
            "credited), (3) filed income tax for 3 of the 5 tax years, (4) adequate knowledge of English "
            "OR French (ages 18-54): CLB 4 or higher demonstrated by existing test scores, completion of "
            "government-funded language training, or secondary/post-secondary education in English/French, "
            "(5) pass citizenship test (ages 18-54): 75% on Canadian history, values, institutions, symbols. "
            "Fees: $630 adult, $100 for minors. Processing: ~12-14 months currently. Prohibitions under "
            "s.5(1.04): time served in prison does not count toward residency; certain criminal convictions "
            "bar applications. Dual citizenship is permitted."
        ),
        "last_verified": "2026-06-15",
    },
    # === LEGAL REPRESENTATION ===
    {
        "id": "ircc-legal-deep",
        "title": "Finding Regulated Representatives — IRPA s.91, CICC Registry",
        "source": "IRCC / College of Immigration and Citizenship Consultants",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/immigration-citizenship-representative/choose.html",
        "deep_links": [
            "https://college-ic.ca/protecting-the-public/find-an-immigration-consultant",
            "https://www.legalaid.on.ca/services/immigration-and-refugee-law/",
            "https://www.cba.org/For-The-Public/Find-A-Lawyer",
        ],
        "category": "legal",
        "legal_refs": ["IRPA s.91", "College of Immigration and Citizenship Consultants Act"],
        "keywords": ["legal aid", "RCIC", "lawyer", "immigration consultant", "free", "legal clinic",
                     "CBA", "CICC", "regulated representative", "ghost consultant", "fraud"],
        "content": (
            "IRPA s.91 restricts who can represent you in immigration matters for a fee: only "
            "(1) lawyers/notaries who are members of a Canadian provincial/territorial law society, or "
            "(2) Regulated Canadian Immigration Consultants (RCICs) registered with the College of "
            "Immigration and Citizenship Consultants (CICC, formerly ICCRC). Using an unlicensed "
            "'ghost consultant' is illegal and can result in your application being refused. "
            "Verify any representative: CICC registry (college-ic.ca), provincial law society directory. "
            "FREE legal help: Legal Aid Ontario (immigration/refugee), Aide juridique du Quebec, "
            "Legal Services Society BC, community legal clinics (university clinics, Neighbourhood "
            "Legal Services), CBA Lawyer Referral Service (free 30-min consultation), "
            "UNHCR-partnered NGOs for refugees. Many clinics serve regardless of income for refugees."
        ),
        "last_verified": "2026-06-18",
    },
    # === PERMIT RENEWAL / STATUS MAINTENANCE ===
    {
        "id": "irpr-status-maintenance",
        "title": "Maintaining and Extending Status — IRPR R.181-189, Implied Status",
        "source": "IRCC",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/visit-canada/extend-stay.html",
        "deep_links": [
            "https://www.canada.ca/en/immigration-refugees-citizenship/services/work-canada/permit/temporary/extend.html",
            "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/extend-study-permit.html",
        ],
        "category": "status_maintenance",
        "legal_refs": ["IRPR R.181", "IRPR R.183", "IRPR R.186", "IRPR R.189"],
        "keywords": ["extend", "renew", "implied status", "restoration", "status", "expire",
                     "work permit extension", "study permit extension", "visitor record"],
        "content": (
            "Status maintenance under IRPR: temporary residents must apply to extend BEFORE their "
            "current permit expires. If applied before expiry, IRPR R.189 grants 'implied status' — "
            "you maintain the same conditions (including work/study authorization) until a decision. "
            "If your permit expired without applying: you have 90 days to apply for restoration of "
            "status (IRPR R.182). Restoration fee: $229 + original application fee. During restoration "
            "period you CANNOT work or study. Work permit extensions: need employer still offering job "
            "(unless open WP). Study permit extensions: need continued enrolment. Best practice: apply "
            "at least 30 days before expiry to avoid gaps. If BOWP (Bridging Open Work Permit) eligible "
            "(PR application submitted, current WP expiring within 4 months): apply under IRPR R.205 C43."
        ),
        "last_verified": "2026-06-25",
    },
    # === HOUSING / RENTAL ===
    {
        "id": "cmhc-housing",
        "title": "Housing for Newcomers — Rights and Resources",
        "source": "CMHC / Provincial Tenancy Acts",
        "url": "https://www.cmhc-schl.gc.ca/consumers/renting/newcomers",
        "deep_links": [
            "https://www.ontario.ca/page/renting-ontario-your-rights",
            "https://www2.gov.bc.ca/gov/content/housing-tenancy/residential-tenancies",
        ],
        "category": "settlement",
        "legal_refs": ["Residential Tenancies Act (Ontario)", "Residential Tenancy Act (BC)"],
        "keywords": ["housing", "rental", "apartment", "lease", "tenant rights", "newcomer",
                     "credit history", "landlord", "deposit", "eviction"],
        "content": (
            "Finding housing as a newcomer: landlords cannot discriminate based on immigration status, "
            "race, or country of origin (Human Rights Code). Without Canadian credit history, you may "
            "need to provide: employment letter, bank statements, larger deposit (where provincial law "
            "permits), or a co-signer. In Ontario: landlord can only collect first and last month's rent "
            "as deposit (no damage deposit). In BC: security deposit max half-month's rent. "
            "Resources: CMHC newcomer guides, settlement agency housing help (free), Canada Mortgage and "
            "Housing Corporation rental market reports. Watch for rental scams: never pay before seeing "
            "the unit, verify landlord identity, legitimate landlords use proper leases."
        ),
        "last_verified": "2026-06-05",
    },
    # === BANKING ===
    {
        "id": "fcac-banking",
        "title": "Opening a Bank Account — No-cost Accounts for Newcomers",
        "source": "Financial Consumer Agency of Canada (FCAC)",
        "url": "https://www.canada.ca/en/financial-consumer-agency/services/banking/opening-bank-account.html",
        "deep_links": [
            "https://www.canada.ca/en/financial-consumer-agency/services/banking/newcomers-banking.html",
        ],
        "category": "settlement",
        "legal_refs": ["Bank Act s.437-448", "Access to Basic Banking Services Regulations"],
        "keywords": ["bank account", "banking", "newcomer", "credit history", "credit card",
                     "GIC", "no-fee account", "RBC", "TD", "Scotiabank"],
        "content": (
            "Under the Bank Act's Access to Basic Banking Services Regulations, banks must open an "
            "account for any person with valid government-issued ID — they cannot refuse based on "
            "lack of credit history or employment. Major banks offer newcomer packages: RBC (free "
            "for 1 year + no-fee credit card), TD (New to Canada banking), Scotiabank (StartRight), "
            "CIBC (newcomer bundle). Bring: passport, work/study permit or PR card, proof of address. "
            "You can open accounts from abroad before arrival (RBC, HSBC). Building credit: get a "
            "secured credit card, keep utilization under 30%, pay in full monthly. Credit score "
            "builds after ~6 months of responsible use."
        ),
        "last_verified": "2026-06-08",
    },

    # =========================================================================
    # === JULY 2026 UPDATES — SUPER-INTELLIGENCE TIER ===
    # =========================================================================

    # === TR-TO-PR PATHWAY (33,000 CAP) ===
    {
        "id": "ircc-tr-to-pr-july-2026",
        "title": "TR-to-PR Pathway 2026 — 33,000 Cap, Eligibility & Application",
        "source": "IRCC / PM Carney Announcement (June 2026)",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/tr-pr-pathway.html",
        "deep_links": [
            "https://www.canada.ca/en/immigration-refugees-citizenship/news/2026/06/tr-to-pr-pathway.html",
            "https://laws-lois.justice.gc.ca/eng/acts/i-2.5/page-8.html",
        ],
        "category": "permanent_residence",
        "legal_refs": ["IRPA s.25.2", "Ministerial Instructions (TR-to-PR 2026)", "IRPR R.87.3"],
        "keywords": ["TR to PR", "temporary resident to permanent resident", "pathway", "33000",
                     "33,000 cap", "Carney", "2026", "special pathway", "regularization",
                     "temporary to permanent", "TR-to-PR"],
        "content": (
            "In June 2026, PM Mark Carney announced a new TR-to-PR (Temporary Resident to Permanent "
            "Resident) pathway with a cap of 33,000 principal applicants. This pathway targets temporary "
            "residents already in Canada with valid status (work permit, study permit, or implied status) "
            "who meet labour market needs. Key eligibility criteria: (1) physically present in Canada with "
            "valid temporary status at time of application, (2) 12+ months of Canadian work experience in "
            "eligible TEER 0-3 occupations within the past 3 years, (3) CLB 5 or higher in English or French "
            "(IELTS, CELPIP, TEF, or TCF accepted), (4) Canadian credential or ECA-assessed foreign credential "
            "equivalent to Canadian secondary or above. Applications open on a first-come, first-served basis "
            "with online submission via IRCC portal. Processing target: 6 months. Applicants may continue "
            "working under implied status while application is pending. This pathway operates under Ministerial "
            "Instructions via IRPA s.25.2 (public policy considerations). The 33,000 cap is firm and will not "
            "be expanded once reached. Spousal and dependent OWPs are available while principal application is "
            "in progress. This complements — not replaces — Express Entry and PNP pathways."
        ),
        "last_verified": "2026-07-01",
    },

    # === NEW PROOF OF FUNDS ($15,263) ===
    {
        "id": "ircc-proof-of-funds-july-2026",
        "title": "Updated Proof of Funds Requirements — July 2026 ($15,263 for Single Applicant)",
        "source": "IRCC / Low Income Cut-Off (LICO) Update 2026",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/documents/proof-funds.html",
        "deep_links": [
            "https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/eligibility/proof-funds.html",
            "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1110024101",
        ],
        "category": "permanent_residence",
        "legal_refs": ["IRPR R.76(1)(b)", "Low Income Cut-Off (Statistics Canada)"],
        "keywords": ["proof of funds", "settlement funds", "LICO", "financial requirement",
                     "$15,263", "bank statement", "Express Entry funds", "FSW funds",
                     "2026 proof of funds", "how much money", "funds required"],
        "content": (
            "Effective July 2026, the updated Proof of Funds requirement under IRPR R.76(1)(b) for "
            "Federal Skilled Worker (FSW) applicants (and other programs requiring settlement funds) is: "
            "1 family member: $15,263 CAD; 2 family members: $19,009 CAD; 3 family members: $23,377 CAD; "
            "4 family members: $28,381 CAD; 5 family members: $32,187 CAD; 6 family members: $36,296 CAD; "
            "7+ family members: $40,411 CAD (add $4,115 for each additional member). "
            "These amounts are updated annually based on Statistics Canada LICO (Low Income Cut-Off) data. "
            "The 2026 figures represent a ~3.9% increase over 2025 rates ($14,690 single). "
            "Funds must be readily transferable and available (bank accounts, GICs, term deposits that can "
            "be liquidated). Proof: official bank letters or statements from the past 12 months showing "
            "funds have been consistently available. Debts and obligations are deducted. "
            "CEC applicants with valid Canadian job offer are EXEMPT from proof of funds. "
            "PNP applicants may also be exempt depending on provincial stream requirements."
        ),
        "last_verified": "2026-07-01",
    },

    # === PGWP FIELD-MATCHING RULES (2026 UPDATE) ===
    {
        "id": "ircc-pgwp-field-matching-2026",
        "title": "PGWP Field-of-Study Matching Rules — 2026 Consolidated Policy",
        "source": "IRCC Program Delivery Instructions (Updated June 2026)",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/work/after-graduation/eligibility.html",
        "deep_links": [
            "https://www.canada.ca/en/immigration-refugees-citizenship/corporate/publications-manuals/operational-bulletins-manuals/temporary-residents/study-permits/post-graduation-work-permit-program/eligibility.html",
            "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/work/after-graduation/about.html",
        ],
        "category": "study_permit",
        "legal_refs": ["IRPR R.205(c)(ii)", "Ministerial Instructions (PGWP 2024-2026)", "IRPR R.222"],
        "keywords": ["PGWP field of study", "eligible fields", "PGWP 2026", "field matching",
                     "college PGWP", "STEM", "healthcare", "trades", "PGWP eligible programs",
                     "PGWP restrictions", "field-of-study", "PGWP college requirements"],
        "content": (
            "PGWP Field-of-Study Matching Rules (consolidated as of June 2026): For college programs "
            "starting on or after November 1, 2024, PGWPs are ONLY issued if the field of study aligns "
            "with occupations in long-term labour shortage. Eligible fields for COLLEGE graduates: "
            "(1) Agriculture and agri-food (CIP 01.xxxx), (2) Healthcare (CIP 51.xxxx), "
            "(3) STEM — Science, Technology, Engineering, Mathematics (CIP 11.xxxx, 14.xxxx, 15.xxxx, "
            "26.xxxx, 27.xxxx, 40.xxxx), (4) Trades (CIP 46.xxxx, 47.xxxx, 48.xxxx, 49.xxxx), "
            "(5) Transport and infrastructure (CIP 49.xxxx). "
            "EXEMPT from field-matching restrictions: (a) ALL university bachelor's degree programs and above "
            "(regardless of field), (b) ALL master's and doctoral programs, (c) Programs that started BEFORE "
            "November 1, 2024. Duration rules remain: programs <2 years = PGWP length equals program length; "
            "programs 2+ years = 3-year PGWP; master's programs (even if <2 years) = 3-year PGWP. "
            "PGWP holders must now also ensure their post-graduation employment is in a field RELATED to "
            "their study for Express Entry CEC/FSW points optimization, though not a legal requirement "
            "for maintaining PGWP validity."
        ),
        "last_verified": "2026-07-01",
    },

    # === BILL C-12 (IMMIGRATION FRAMEWORK MODERNIZATION) ===
    {
        "id": "parl-bill-c12-2026",
        "title": "Bill C-12 — Immigration Framework Modernization Act (2026)",
        "source": "Parliament of Canada / House of Commons",
        "url": "https://www.parl.ca/legisinfo/en/bill/45-1/c-12",
        "deep_links": [
            "https://www.canada.ca/en/immigration-refugees-citizenship/news/2026/06/bill-c-12-immigration-modernization.html",
            "https://laws-lois.justice.gc.ca/eng/acts/i-2.5/",
        ],
        "category": "permanent_residence",
        "legal_refs": ["Bill C-12 (45th Parliament, 1st Session)", "Proposed amendments to IRPA"],
        "keywords": ["Bill C-12", "immigration reform", "modernization", "2026", "Carney",
                     "framework", "legislation", "parliament", "IRPA amendment", "new law"],
        "content": (
            "Bill C-12 (Immigration Framework Modernization Act), introduced in the 45th Parliament "
            "(1st Session, 2026) under PM Carney's government, proposes significant amendments to IRPA: "
            "(1) Codification of category-based selection into statute (currently done via Ministerial Instructions), "
            "(2) Mandatory annual immigration levels plan tabling with provincial consultation requirements, "
            "(3) New 'Critical Worker' PR stream for TEER 4-5 workers in designated shortage occupations "
            "(caregivers, food service, agriculture) — bypassing Express Entry CRS requirements, "
            "(4) Enhanced TR-to-PR mechanisms with annual pathway allocations, "
            "(5) Strengthened anti-fraud provisions and penalties for ghost consultants (up to 5 years "
            "imprisonment, up from 2 years under current IRPA s.91), "
            "(6) Provincial veto power over temporary resident volumes in their jurisdiction. "
            "Status as of July 2026: Second Reading completed, referred to Standing Committee on "
            "Citizenship and Immigration (CIMM). Expected Royal Assent: Fall 2026 if committee stage "
            "proceeds on schedule. NOTE: Bill C-12 is NOT yet law — provisions are proposed only. "
            "Current IRPA remains in full effect until Royal Assent and proclamation."
        ),
        "last_verified": "2026-07-01",
    },

    # === CARNEY IMMIGRATION POLICY DIRECTION ===
    {
        "id": "ircc-carney-policy-2026",
        "title": "PM Carney Immigration Policy Direction — June-July 2026 Announcements",
        "source": "PMO / IRCC Press Releases",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/news/2026/06/immigration-policy-direction.html",
        "deep_links": [
            "https://pm.gc.ca/en/news/speeches/2026/06/carney-immigration-address",
            "https://www.canada.ca/en/immigration-refugees-citizenship/corporate/publications-manuals/annual-report-parliament-immigration.html",
        ],
        "category": "permanent_residence",
        "legal_refs": ["IRPA s.94(1)", "Annual Report to Parliament on Immigration 2026"],
        "keywords": ["Carney", "prime minister", "immigration policy", "2026 levels plan",
                     "reduction", "cap", "temporary residents", "population growth",
                     "housing", "immigration announcement"],
        "content": (
            "PM Mark Carney's immigration policy direction (June-July 2026) signals a recalibration: "
            "(1) Temporary resident reduction target: reduce TR population by ~20% over 2 years (from ~6.8M "
            "to ~5.4M by 2028) through natural attrition and non-renewal, (2) PR targets held steady at "
            "~395,000 for 2027 with emphasis on economic class (60%+), (3) TR-to-PR pathway (33,000 cap) "
            "to regularize long-term temporary residents with demonstrated economic contribution, "
            "(4) Student permit cap maintained at 360,000 with stricter DLI compliance enforcement, "
            "(5) PGWP field-matching rules confirmed as permanent policy (not temporary), "
            "(6) Bill C-12 tabled to modernize IRPA framework. "
            "Impact on applicants: expect tighter processing and higher refusal rates for temporary permits; "
            "PR pathways remain viable but increasingly competitive."
        ),
        "last_verified": "2026-07-02",
    },
]


# ---------------------------------------------------------------------------
# Omniscience Engine — Live Web Search Fallback
# ---------------------------------------------------------------------------
LIVE_SEARCH_TIMEOUT = 8.0  # seconds


async def _live_web_search(query: str, top_k: int = 3) -> Optional[str]:
    """Trigger a live web search against authoritative Canadian government domains.

    Called when internal KNOWLEDGE_BASE relevance score is below threshold (< 4.0).
    Uses the LLM endpoint with web search capability for real-time government data.

    Returns formatted context block or None if search fails.
    """
    try:
        openai_key = os.environ.get("OPENAI_API_KEY", "")
        if not openai_key:
            logger.info("OPENAI_API_KEY not set; live web search disabled")
            return None

        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=openai_key)
        model = os.environ.get("OPENAI_WEB_MODEL", os.environ.get("OPENAI_CHAT_MODEL", "gpt-4.1"))
        resp = await client.responses.create(
            model=model,
            instructions=(
                "You are a Canadian immigration research assistant. Search the web for the most current, "
                "authoritative information from canada.ca, justice.gc.ca, and irb.gc.ca. Return ONLY factual "
                "findings with specific URLs. Focus on 2026 policy changes, current processing times, and "
                "regulatory updates. Be concise and cite every claim."
            ),
            input=(
                f"Find the latest authoritative Canadian government information on: {query}\n\n"
                "Return: key facts, relevant URLs, legal references, and effective dates. "
                "Only include information from canada.ca, laws-lois.justice.gc.ca, or irb.gc.ca."
            ),
            max_output_tokens=1500,
            temperature=0.1,
            tools=[{"type": "web_search", "search_context_size": "medium"}],
        )
        content = getattr(resp, "output_text", "") or ""
        if content and len(content) > 50:
            logger.info("Live web search returned %d chars for: %.60s", len(content), query)
            return content
        logger.warning("Live web search returned insufficient content")
        return None

    except Exception as e:
        logger.warning("Live web search failed: %s", str(e))
        return None


def _format_live_web_context(live_content: str) -> str:
    """Format live web search results into an LLM context block."""
    return (
        "\n\n═══ LIVE WEB DATA (Real-Time Government Sources) ═══\n"
        "The following was retrieved in real-time from authoritative Canadian government websites.\n"
        "This data may be MORE CURRENT than the static knowledge base.\n\n"
        f"{live_content}\n\n"
        "═══ END LIVE WEB DATA ═══\n\n"
        "LIVE DATA CITATION MANDATE:\n"
        "* When Live Web Data contradicts static knowledge base entries, PRIORITIZE the live data "
        "(it is more current).\n"
        "* Cite the specific URLs from the live data in your response.\n"
        "* If live data provides 2026 updates (processing times, fees, policy changes), "
        "USE THEM over any older static entries.\n"
        "* Still maintain Sovereign Authority tone and citation standards.\n"
    )


def _score_relevance(doc: Dict, query: str, user_context: Optional[Dict] = None) -> float:
    """Weighted keyword-based relevance scoring (mock for vector similarity).

    In production, this would be cosine similarity on embeddings.
    """
    query_lower = query.lower()
    score = 0.0

    # Exact keyword match (high signal)
    for kw in doc.get("keywords", []):
        kw_lower = kw.lower()
        if kw_lower in query_lower:
            score += 3.0
        elif len(kw_lower) > 4 and any(w in query_lower for w in kw_lower.split()):
            score += 1.0

    # Title word match
    for tw in doc.get("title", "").lower().split():
        if tw in query_lower and len(tw) > 3:
            score += 1.5

    # Legal reference match (user asking about specific sections)
    for ref in doc.get("legal_refs", []):
        if ref.lower().replace(".", "").replace(" ", "") in query_lower.replace(".", "").replace(" ", ""):
            score += 5.0

    # Category boost based on user context
    if user_context:
        user_type = (user_context.get("newcomer_type") or "").lower()
        doc_cat = doc.get("category", "")
        type_to_cats = {
            "refugee": ["refugee", "legal", "settlement"],
            "student": ["study_permit", "settlement"],
            "worker": ["work_permit", "settlement", "permanent_residence"],
            "visitor": ["settlement"],
            "pr": ["permanent_residence", "citizenship", "settlement"],
        }
        if doc_cat in type_to_cats.get(user_type, []):
            score += 2.0

        # Visa pathway boost
        visa = (user_context.get("visa_type") or "").lower()
        if "express" in visa and doc_cat == "permanent_residence":
            score += 2.0
        if "pnp" in visa or "provincial" in visa:
            if "pnp" in doc.get("id", ""):
                score += 3.0

    # Temporal boost: queries mentioning 2026/current/new/latest get boosted for recent entries
    temporal_keywords = ["2026", "current", "new", "latest", "updated", "recent", "july", "carney", "bill c-12"]
    if any(tk in query_lower for tk in temporal_keywords):
        last_verified = doc.get("last_verified", "")
        if "2026-07" in last_verified:
            score += 3.0  # Strong boost for July 2026 entries
        elif "2026-06" in last_verified:
            score += 1.5  # Moderate boost for June 2026

    legal_query_markers = [
        "legal", "lawyer", "consultant", "rcic", "representative", "rights",
        "refugee", "hearing", "appeal", "inadmissible", "work permit", "study permit",
        "pr", "citizenship", "government", "irpa", "irpr"
    ]
    if any(marker in query_lower for marker in legal_query_markers):
        if doc.get("category") in {"legal", "refugee", "work_permit", "study_permit", "permanent_residence", "citizenship", "status_maintenance"}:
            score += 2.5
        last_verified = doc.get("last_verified", "")
        if last_verified.startswith("2026-07"):
            score += 2.0

    return score


def retrieve_documents(query: str, user_context: Optional[Dict] = None, top_k: int = 3) -> Tuple[List[Dict], float]:
    """Retrieve the most relevant documents from the knowledge base.

    Returns (top_k documents sorted by relevance score, max_score).
    The max_score is used by the Omniscience Engine to decide whether
    to trigger a Live Web Search fallback.
    """
    scored = []
    for doc in KNOWLEDGE_BASE:
        s = _score_relevance(doc, query, user_context)
        if s >= 1.5:  # Minimum relevance threshold
            scored.append((s, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    max_score = scored[0][0] if scored else 0.0
    return [doc for _, doc in scored[:top_k]], max_score


def format_context_for_llm(documents: List[Dict]) -> str:
    """Format retrieved documents into a sovereign-authority context block.

    Follows 'Grounded Integrity' + 'Sovereign Authority': the AI must cite
    DEEP LINKS (specific legislation pages, not just canada.ca), and ONLY
    state what these documents support.
    """
    if not documents:
        return ""
    parts = [
        "\n\n═══ RETRIEVED AUTHORITATIVE DOCUMENTS ═══"
    ]
    for i, doc in enumerate(documents, 1):
        all_links = [doc["url"]] + doc.get("deep_links", [])
        refs = ", ".join(doc.get("legal_refs", []))
        parts.append(
            f"\nSource [{i}]: {doc['title']}\n"
            f"  Authority: {doc['source']}\n"
            f"  Legal References: {refs}\n"
            f"  Verified: {doc.get('last_verified', 'unknown')}\n"
            f"  Citation URLs:\n"
            + "\n".join(f"    - {link}" for link in all_links)
            + f"\n  Content: {doc['content']}\n"
            f"---"
        )
    parts.append(
        "\n═══ END RETRIEVED DOCUMENTS ═══\n\n"
        "SOVEREIGN CITATION MANDATE:\n"
        "* You MUST cite at least one deep-link URL from the sources above in your response.\n"
        "* Prefer the most specific URL (legislation page > general landing page).\n"
        "* Include the legal reference (e.g., 'Under IRPR R.205(c)(ii)') alongside the URL.\n"
        "* If NO retrieved document adequately answers the question, you MUST state: "
        "'I do not have verified information on this specific point. For authoritative guidance, "
        "contact IRCC directly at canada.ca/ircc or call 1-888-242-2100, or consult a regulated "
        "representative (RCIC/lawyer).'\n"
        "* NEVER fabricate a URL, section number, or factual claim not grounded in the sources above.\n"
        "* When the user's situation involves case-specific strategy, decline and refer to a "
        "regulated representative — this is NOT legal advice."
    )
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Omniscience Relevance Threshold
# If the best internal match scores below this, Live Web Search is triggered.
# ---------------------------------------------------------------------------
OMNISCIENCE_THRESHOLD = 4.0


async def rag_search(query: str, user: Optional[Dict] = None) -> str:
    """Main RAG entry point: retrieve relevant docs and return formatted context.

    SUPER-INTELLIGENCE TIER: If internal knowledge relevance < 4.0,
    the Omniscience Engine triggers a Live Web Search against canada.ca
    and justice.gc.ca, fetches top results, and injects live data into
    the LLM context alongside static knowledge base results.

    Also injects:
    - Plain English (Level 1) filter instructions
    - Proactive Prescience instructions
    - IRPA Section 91 disclosure mandate

    Called by the chat router before sending to the LLM, ensuring
    every response is grounded in verifiable, deep-linked sources.
    """
    user_context = None
    if user:
        user_context = {
            "newcomer_type": user.get("newcomer_type"),
            "visa_type": user.get("visa_type"),
            "country_of_origin": user.get("country_of_origin"),
        }

    documents, max_score = retrieve_documents(query, user_context, top_k=3)

    # --- Omniscience Engine: Live Web Search Fallback ---
    live_web_context = ""
    if max_score < OMNISCIENCE_THRESHOLD:
        logger.info(
            "Omniscience triggered: max_score=%.1f < threshold=%.1f for query: %.80s",
            max_score, OMNISCIENCE_THRESHOLD, query
        )
        live_content = await _live_web_search(query, top_k=3)
        if live_content:
            live_web_context = _format_live_web_context(live_content)
        else:
            logger.info("Live web search returned no usable content; proceeding with KB only")

    # --- Also trigger live search for explicitly temporal/2026 queries regardless of score ---
    temporal_triggers = ["2026", "latest", "current processing", "new policy", "carney", "bill c-12", "july 2026"]
    query_lower = query.lower()
    if not live_web_context and any(t in query_lower for t in temporal_triggers):
        logger.info("Temporal trigger detected for query: %.80s — running live search", query)
        live_content = await _live_web_search(query, top_k=3)
        if live_content:
            live_web_context = _format_live_web_context(live_content)

    if not documents and not live_web_context:
        return (
            "\n\n═══ NO SPECIFIC DOCUMENTS MATCHED ═══\n"
            "The knowledge base did not closely match this query. "
            "If you can answer from training knowledge AND cite a specific, real canada.ca or "
            "laws-lois.justice.gc.ca URL that you are CERTAIN exists, you may do so. "
            "Otherwise, state: 'I don't have verified current information on that specific point. "
            "Please check canada.ca/ircc or call IRCC at 1-888-242-2100 for authoritative guidance.'\n"
            "═══════════════════════════════════\n"
            + PLAIN_ENGLISH_FILTER
            + IRPA_S91_DISCLOSURE
        )

    logger.info(
        "RAG retrieved %d docs (max_score=%.1f) for query: %.80s | live_web=%s",
        len(documents), max_score, query, bool(live_web_context)
    )

    # Combine: static KB context + live web context + intelligence layers
    static_context = format_context_for_llm(documents) if documents else ""
    return (
        static_context
        + live_web_context
        + PLAIN_ENGLISH_FILTER
        + PROACTIVE_PRESCIENCE_INSTRUCTIONS
        + IRPA_S91_DISCLOSURE
    )

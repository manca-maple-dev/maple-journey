"""
Benefits Eligibility & Free Application Guide Service
Helps newcomers navigate tax, settlement, and government benefits without paying agents
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("benefits_guide")

# Comprehensive benefits database with FREE alternatives to paid services
BENEFITS_DATABASE = {
    # TAX BENEFITS
    "canada_child_benefit": {
        "name": "Canada Child Benefit (CCB)",
        "description": "Monthly payment for families with children under 18",
        "eligibility": [
            "Have Canadian income or reside in Canada",
            "Child under 18 years old",
            "Canadian resident for tax purposes",
        ],
        "max_benefit": "$7,437/year per child (varies by income)",
        "how_to_apply_free": [
            "1. Register child's birth with vital statistics (free)",
            "2. File tax return with CRA (free at NETFILE partners)",
            "3. Apply through CRA My Account (free online)",
        ],
        "free_resources": [
            {"name": "CRA My Account", "url": "https://www.canada.ca/myaccount", "type": "Official portal"},
            {"name": "Free Tax Clinic", "url": "https://www.canada.ca/taxes/freeclinic", "type": "Government program"},
            {"name": "Settlement services (FREE)", "url": "https://www.211.ca", "type": "211 directory"},
        ],
        "avoid_paying_for": "Do NOT pay agents/accountants to apply - it's free through CRA",
        "category": "tax",
        "estimated_yearly_value": "$7437"
    },
    
    "gis_benefit": {
        "name": "Guaranteed Income Supplement (GIS)",
        "description": "Top-up for low-income seniors (65+) receiving Old Age Security",
        "eligibility": [
            "Age 65+",
            "Canadian resident for 10+ years",
            "Low annual income",
            "Receiving Old Age Security (OAS)",
        ],
        "max_benefit": "$19,000+/year (income-tested)",
        "how_to_apply_free": [
            "1. Apply for OAS at Service Canada office (free)",
            "2. GIS is automatic if you qualify",
            "3. Update income annually on tax return",
        ],
        "free_resources": [
            {"name": "Service Canada", "url": "https://www.canada.ca/servicecanada", "type": "Official"},
            {"name": "1-800-277-9914", "type": "Call Service Canada"},
            {"name": "Settlement counseling (FREE)", "url": "https://www.211.ca", "type": "211 directory"},
        ],
        "avoid_paying_for": "Never pay for GIS application - it's automatic if eligible",
        "category": "seniors",
        "estimated_yearly_value": "$19000"
    },

    # SETTLEMENT BENEFITS
    "resettlement_allowance": {
        "name": "Resettlement Allowance for Refugees",
        "description": "One-time support for newly recognized refugees to cover initial settlement costs",
        "eligibility": [
            "Refugee/protected person status granted",
            "Within 12 months of arrival",
        ],
        "max_benefit": "$3,000-$12,000 (family size dependent)",
        "how_to_apply_free": [
            "1. Contact IRCC (Immigration, Refugees and Citizenship Canada)",
            "2. Provide proof of status letter",
            "3. Submit documentation (all free)",
        ],
        "free_resources": [
            {"name": "IRCC Port of Entry", "type": "Provided upon arrival"},
            {"name": "Settlement agencies (FREE)", "url": "https://www.211.ca", "type": "Find local"},
            {"name": "Community support centers", "type": "FREE programming"},
        ],
        "avoid_paying_for": "This is ALWAYS free - never pay agents for this",
        "category": "settlement",
        "estimated_yearly_value": "$6000"
    },

    "provincial_settlement_support": {
        "name": "Provincial Settlement Programs",
        "description": "Free language training, job placement, credential recognition help",
        "eligibility": [
            "Newcomer to Canada (varies by province)",
            "Landed immigrant or refugee",
            "Reside in province offering program",
        ],
        "max_benefit": "Up to $15,000+ in free services",
        "how_to_apply_free": [
            "1. Contact your province's immigration ministry",
            "2. Connect with local settlement organization",
            "3. Access FREE language and employment programs",
            "4. Get credential assessment support (sometimes free)",
        ],
        "free_resources": [
            {"name": "211.ca - Find your province's programs", "url": "https://www.211.ca", "type": "Directory"},
            {"name": "Language training programs", "type": "FREE or subsidized"},
            {"name": "Employment support programs", "type": "FREE through settlement agencies"},
            {"name": "Credential recognition programs", "type": "Varies - often FREE"},
        ],
        "avoid_paying_for": "Language training and job counseling are FREE through settlement agencies",
        "category": "settlement",
        "estimated_yearly_value": "$15000"
    },

    # EMPLOYMENT BENEFITS
    "earned_income_tax_credit": {
        "name": "Canada Earned Income Tax Credit (EITC)",
        "description": "Refundable tax credit for low to moderate income workers",
        "eligibility": [
            "Age 19-64",
            "Canadian resident for tax purposes",
            "Earned employment or self-employment income",
            "Low to moderate income",
        ],
        "max_benefit": "$3,995/year",
        "how_to_apply_free": [
            "1. File tax return with employment income",
            "2. Claim EITC on Schedule 6",
            "3. Use free tax clinic or NETFILE services",
        ],
        "free_resources": [
            {"name": "Free tax clinic near you", "url": "https://www.canada.ca/taxes/freeclinic", "type": "CRA"},
            {"name": "NETFILE authorized services", "url": "https://www.canada.ca/netfile", "type": "Free tax prep"},
            {"name": "Community volunteer program", "type": "FREE tax filing"},
        ],
        "avoid_paying_for": "Tax preparation is free for low-income filers",
        "category": "tax",
        "estimated_yearly_value": "$3995"
    },

    # HOUSING BENEFITS
    "housing_allowance": {
        "name": "Rent Subsidy Programs",
        "description": "Subsidized housing for low-income households",
        "eligibility": [
            "Low household income",
            "Canadian citizen or permanent resident",
            "Rent burden >30% of income",
        ],
        "max_benefit": "Up to 75% rent subsidy",
        "how_to_apply_free": [
            "1. Contact provincial housing agency (FREE assessment)",
            "2. Gather income documents",
            "3. Submit application (no fees)",
        ],
        "free_resources": [
            {"name": "Federal housing portal", "url": "https://www.canada.ca/housing", "type": "Find programs"},
            {"name": "211.ca housing search", "url": "https://www.211.ca", "type": "Find locally"},
            {"name": "Community legal clinics", "type": "FREE housing advice"},
        ],
        "avoid_paying_for": "Never pay for housing applications - all housing programs are free to apply",
        "category": "housing",
        "estimated_yearly_value": "$6000"
    },

    # EDUCATION BENEFITS
    "student_financial_aid": {
        "name": "Student Loans & Grants",
        "description": "Government loans and non-repayable grants for post-secondary education",
        "eligibility": [
            "Canadian citizen, PR, or protected person",
            "Studying full-time at eligible institution",
            "Demonstrate financial need",
        ],
        "max_benefit": "$15,000+/year in grants + loans",
        "how_to_apply_free": [
            "1. Complete FAFSA or provincial equivalent (FREE online)",
            "2. Submit directly to government (no middleman fees)",
            "3. Grants are never repaid",
            "4. Loans have interest-free repayment assistance",
        ],
        "free_resources": [
            {"name": "National Student Loans Services", "url": "https://www.canada.ca/studentloans", "type": "Official"},
            {"name": "Provincial student aid offices", "type": "Direct application (FREE)"},
            {"name": "Scholarship search (FREE)", "url": "https://www.scholarshipscanada.com", "type": "Database"},
        ],
        "avoid_paying_for": "NEVER pay anyone to apply for student aid - government doesn't charge fees",
        "category": "education",
        "estimated_yearly_value": "$15000"
    },

    # HEALTHCARE BENEFITS
    "prescription_drug_assistance": {
        "name": "Prescription Drug Assistance Programs",
        "description": "Free/reduced-cost prescription medications for low-income individuals",
        "eligibility": [
            "Canadian resident",
            "Prescription required",
            "Income below threshold",
            "No drug coverage",
        ],
        "max_benefit": "Free medications (varies by program)",
        "how_to_apply_free": [
            "1. Ask pharmacist about low-income programs (FREE)",
            "2. Manufacturer assistance programs (direct to company)",
            "3. Provincial drug plans (FREE coverage)",
        ],
        "free_resources": [
            {"name": "411.ca Rx Assistance", "url": "https://www.411.ca", "type": "Find programs"},
            {"name": "Patient support programs", "type": "Manufacturer (FREE)"},
            {"name": "Community health centers", "type": "FREE assessments"},
        ],
        "avoid_paying_for": "These programs are always FREE - never pay for access",
        "category": "healthcare",
        "estimated_yearly_value": "$2000"
    },

    # LEGAL BENEFITS
    "legal_aid": {
        "name": "Legal Aid Services",
        "description": "Free legal representation for those who cannot afford a lawyer",
        "eligibility": [
            "Income below threshold",
            "Legal matter requires representation",
            "Canadian resident",
        ],
        "max_benefit": "Full legal representation (FREE)",
        "how_to_apply_free": [
            "1. Contact provincial legal aid office",
            "2. Income assessment (automatic)",
            "3. Assigned lawyer at no cost",
        ],
        "free_resources": [
            {"name": "Provincial Legal Aid Society", "type": "Contact directly"},
            {"name": "Community legal clinics", "type": "FREE consultations"},
            {"name": "Law student clinics", "type": "FREE with student supervision"},
        ],
        "avoid_paying_for": "Legal aid is PROVIDED for free - do not pay for legal services if eligible",
        "category": "legal",
        "estimated_yearly_value": "$5000"
    },
}

# Scams and what to avoid
COMMON_SCAMS = [
    {
        "scam": "Agent charging to apply for CCB",
        "why_scam": "CCB is free to apply through CRA",
        "cost": "Typically $50-200 per child",
        "actual_cost": "$0 - completely free",
        "free_alternative": "Use CRA My Account or local settlement agency"
    },
    {
        "scam": "Immigration consultant charging for credential assessment",
        "why_scam": "Most assessments are $100-300 from official bodies, agents add markup",
        "cost": "$300-800",
        "actual_cost": "$100-300 direct",
        "free_alternative": "Contact provincial credential recognition body directly"
    },
    {
        "scam": "Paying for housing application assistance",
        "why_scam": "Housing applications never have fees",
        "cost": "$100-500",
        "actual_cost": "$0 - always free",
        "free_alternative": "Contact housing agency directly or use 211.ca"
    },
    {
        "scam": "Paying for student aid application",
        "why_scam": "Government never charges for student aid applications",
        "cost": "$50-300",
        "actual_cost": "$0 - always free online",
        "free_alternative": "Apply directly at canada.ca/studentloans"
    },
]

class BenefitsGuideService:
    @staticmethod
    async def get_all_benefits() -> List[Dict[str, Any]]:
        """Get complete benefits database"""
        return list(BENEFITS_DATABASE.values())
    
    @staticmethod
    async def get_benefit(benefit_id: str) -> Optional[Dict[str, Any]]:
        """Get specific benefit details"""
        return BENEFITS_DATABASE.get(benefit_id)
    
    @staticmethod
    async def get_free_alternatives() -> List[Dict[str, Any]]:
        """Get common scams and their FREE alternatives"""
        return COMMON_SCAMS
    
    @staticmethod
    async def calculate_total_potential_value(user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate total potential benefits user qualifies for"""
        eligible_benefits = []
        total_value = 0
        
        age = user_profile.get("age", 0)
        income = user_profile.get("annual_income", 0)
        has_children = user_profile.get("has_children", False)
        status = user_profile.get("immigration_status", "")
        
        # Check eligibility
        if has_children and income < 200000:
            eligible_benefits.append({
                "benefit": "Canada Child Benefit",
                "value": "$7,437/year per child",
                "priority": "HIGH"
            })
            total_value += 7437
        
        if income < 35000:
            eligible_benefits.append({
                "benefit": "Canada Earned Income Tax Credit",
                "value": "$3,995/year",
                "priority": "HIGH"
            })
            total_value += 3995
        
        if "refugee" in status.lower():
            eligible_benefits.append({
                "benefit": "Resettlement Allowance",
                "value": "$6,000+ one-time",
                "priority": "CRITICAL"
            })
            total_value += 6000
        
        if age >= 65:
            eligible_benefits.append({
                "benefit": "Guaranteed Income Supplement",
                "value": "$19,000+/year",
                "priority": "CRITICAL"
            })
            total_value += 19000
        
        return {
            "eligible_benefits": eligible_benefits,
            "total_potential_value": f"${total_value:,}/year",
            "total_numeric": total_value,
            "next_steps": [
                "Contact CRA at 1-800-959-8281",
                "Visit local settlement agency via 211.ca",
                "Apply through canada.ca (always free)"
            ]
        }
    
    @staticmethod
    async def get_how_to_get_free(benefit_id: str) -> Dict[str, Any]:
        """Get step-by-step guide to get benefit for FREE"""
        benefit = BENEFITS_DATABASE.get(benefit_id)
        if not benefit:
            return {"error": "Benefit not found"}
        
        return {
            "benefit_name": benefit["name"],
            "free_steps": benefit["how_to_apply_free"],
            "free_resources": benefit["free_resources"],
            "warning": benefit["avoid_paying_for"],
            "estimated_value": benefit.get("estimated_yearly_value", "N/A"),
            "typical_scam_cost": "Would cost $100-500 through agent",
            "your_cost": "$0 - FREE"
        }

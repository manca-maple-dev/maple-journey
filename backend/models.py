"""Pydantic request models for the MapleJourney API."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr


# --- Auth ---
class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None  # Optional at signup, enables WhatsApp/SMS welcome
    country_of_origin: Optional[str] = ""
    newcomer_type: Optional[str] = ""


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordIn(BaseModel):
    email: EmailStr


class ResetPasswordIn(BaseModel):
    token: str
    password: str


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str


class TestEmailIn(BaseModel):
    to: Optional[EmailStr] = None


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    country_of_origin: Optional[str] = None
    newcomer_type: Optional[str] = None
    visa_type: Optional[str] = None
    pr_score: Optional[int] = None
    work_permit_expiry: Optional[str] = None
    avatar: Optional[str] = None


# --- Questionnaire ---
class QuestionnaireIn(BaseModel):
    age: Optional[int] = None
    education: Optional[str] = None
    language: Optional[str] = None
    experience_years: Optional[int] = 0
    canadian_experience: Optional[bool] = False
    job_offer: Optional[bool] = False
    provincial_nomination: Optional[bool] = False
    marital_status: Optional[str] = "single"


# --- Maple Wingman ---
class WingsSettingsIn(BaseModel):
    tone: Optional[str] = None            # friendly | concise | professional
    goals: Optional[List[str]] = None
    autonomy: Optional[str] = None        # ask | auto
    onboarded: Optional[bool] = None


# --- Messaging (Twilio) ---
class PhoneIn(BaseModel):
    phone: str


class OtpVerifyIn(BaseModel):
    phone: str
    code: str


# --- Domain ---
class MilestoneIn(BaseModel):
    title: str
    description: Optional[str] = ""
    date: Optional[str] = ""
    status: str = "upcoming"  # done | active | upcoming


class DocumentIn(BaseModel):
    name: str
    category: Optional[str] = "General"
    status: str = "pending"  # verified | pending | missing
    file_url: Optional[str] = ""
    note: Optional[str] = ""


class LegalResourceIn(BaseModel):
    name: str
    type: str            # Refugee | Immigration | General
    province: str        # National or a specific province
    cost: str            # Free | Low-cost
    description: str
    contact: Optional[str] = ""
    url: Optional[str] = ""


# --- Chat ---
class ChatIn(BaseModel):
    session_id: Optional[str] = None
    message: str


# --- Payments ---
class CheckoutIn(BaseModel):
    plan_id: str
    origin_url: Optional[str] = ""


class SecureIdsIn(BaseModel):
    ircc_file_number: Optional[str] = None
    ucis_or_foreign_id: Optional[str] = None


# --- Admin ---
class UserFeatureUpdate(BaseModel):
    features: Dict[str, bool]


class AdminUserPatch(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    visa_type: Optional[str] = None
    pr_score: Optional[int] = None


class ResourceIn(BaseModel):
    title: str
    category: str
    description: str
    url: Optional[str] = ""


class BenefitIn(BaseModel):
    title: str
    category: str
    description: str
    eligibility: Optional[str] = ""
    amount: Optional[str] = ""


class AnnouncementIn(BaseModel):
    title: str
    body: str
    tone: str = "info"  # info | success | warning


# --- Resume Maker ---
class ResumeBullet(BaseModel):
    text: str


class ResumeExperience(BaseModel):
    title: str
    employer: str
    location: str
    start_date: str  # YYYY-MM
    end_date: Optional[str] = None  # YYYY-MM or null (current)
    bullets: List[ResumeBullet] = []


class ResumeEducation(BaseModel):
    credential: str  # Bachelor of Engineering, Diploma in Nursing, etc.
    institution: str
    country: str
    graduation_year: Optional[str] = None  # YYYY
    canadian_equivalent: Optional[str] = None  # "Equivalent to Canadian B.Eng."


class ResumeLanguage(BaseModel):
    language: str  # English, French, etc.
    clb_level: Optional[str] = None  # CLB 7, CLB 8, etc. (for French/English)


class ResumeDraft(BaseModel):
    """Resume data structure — matches job-search expectations."""
    full_name: str
    email: str
    phone: str
    city: str
    province: str
    summary: str
    experience: List[ResumeExperience] = []
    education: List[ResumeEducation] = []
    skills: List[str] = []
    languages: List[ResumeLanguage] = []
    template: str = "classic"  # classic | modern | compact
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ResumeGenerateIn(BaseModel):
    """Questionnaire for filling resume gaps."""
    target_role: str
    years_experience: int
    key_achievements: List[str] = []
    key_skills: List[str] = []
    additional_info: Optional[str] = None


class ResumeSaveIn(BaseModel):
    """Save edited resume."""
    data: ResumeDraft

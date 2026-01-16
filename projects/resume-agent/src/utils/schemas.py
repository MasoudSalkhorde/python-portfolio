# schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class JDRequirement(BaseModel):
    requirement: str
    type: Literal["must", "nice"] = "must"
    category: Optional[str] = None  # e.g., budget, experimentation, leadership, analytics, partners
    keywords: List[str] = Field(default_factory=list)

class JobDescriptionJSON(BaseModel):
    company: str
    role_title: str
    level: Optional[str] = None
    location: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)
    requirements: List[JDRequirement] = Field(default_factory=list)
    networks_tools: List[str] = Field(default_factory=list)  # Meta, Google, TikTok, AppLovin...
    metrics: List[str] = Field(default_factory=list)         # ROAS, LTV, CPI...

class ResumeBullet(BaseModel):
    id: str                      # e.g. "aylo_1"
    text: str
    evidence_tags: List[str] = Field(default_factory=list)  # ["budget", "roas", "testing", "leadership"]

class ResumeRole(BaseModel):
    company: str
    title: str
    dates: str
    location: Optional[str] = None
    bullets: List[ResumeBullet] = Field(default_factory=list)

class ResumeJSON(BaseModel):
    name: str
    location: Optional[str] = None
    email: Optional[str] = None
    headline: Optional[str] = None
    summary_bullets: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    roles: List[ResumeRole] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    awards: List[str] = Field(default_factory=list)

class MatchItem(BaseModel):
    jd_requirement: str
    matched_bullet_ids: List[str] = Field(default_factory=list)
    strength: Literal["strong", "medium", "weak", "missing"] = "missing"
    notes: Optional[str] = None

class MatchJSON(BaseModel):
    match_map: List[MatchItem] = Field(default_factory=list)
    priority_keywords: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)

class TailoredBullet(BaseModel):
    text: str
    source_bullet_ids: List[str]  # provenance
    needs_revision: bool = False  # True if bullet is far off from original resume
    revision_note: Optional[str] = None  # Note explaining why revision is needed

class TailoredRole(BaseModel):
    company: str
    title: str
    dates: str
    bullets: List[TailoredBullet]

class TailoredResumeJSON(BaseModel):
    tailored_headline: str
    tailored_summary: List[str]
    tailored_skills: List[str]
    tailored_roles: List[TailoredRole]
    change_log: List[str]
    questions_for_user: List[str]
    gaps_to_confirm: List[str] = Field(default_factory=list)  # Gaps that need user confirmation

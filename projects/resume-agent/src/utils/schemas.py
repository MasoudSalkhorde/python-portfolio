# schemas.py
"""
Pydantic schemas for resume tailoring pipeline.

Supports both:
- Legacy single-call approach (TailoredResumeJSON)
- Modular per-component approach (HeaderOutput, RoleOutput, etc.)
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal


# =============================================================================
# JOB DESCRIPTION SCHEMAS
# =============================================================================

class JDRequirement(BaseModel):
    requirement: str
    type: Literal["must", "nice"] = "must"


class JobDescriptionJSON(BaseModel):
    company: str
    role_title: str
    level: Optional[str] = None
    location: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)
    requirements: List[JDRequirement] = Field(default_factory=list)
    tools_platforms: List[str] = Field(default_factory=list)
    metrics_kpis: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    
    # Legacy field aliases for backward compatibility
    @property
    def networks_tools(self) -> List[str]:
        return self.tools_platforms
    
    @property
    def metrics(self) -> List[str]:
        return self.metrics_kpis
    
    @property
    def priority_keywords(self) -> List[str]:
        return self.keywords


# =============================================================================
# RESUME SCHEMAS
# =============================================================================

class ResumeBullet(BaseModel):
    id: str
    text: str
    has_metric: bool = False
    evidence_tags: List[str] = Field(default_factory=list)


class ResumeRole(BaseModel):
    company: str
    title: str
    dates: str
    location: Optional[str] = None
    bullets: List[ResumeBullet] = Field(default_factory=list)


class EducationEntry(BaseModel):
    """Education entry - can be string or structured."""
    degree: str
    institution: Optional[str] = None
    year: Optional[str] = None
    location: Optional[str] = None
    
    def __str__(self) -> str:
        parts = [self.degree]
        if self.institution:
            parts.append(self.institution)
        if self.year:
            parts.append(self.year)
        return ", ".join(parts)


class ResumeJSON(BaseModel):
    name: str
    email: Optional[str] = None
    location: Optional[str] = None
    headline: Optional[str] = None
    summary: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    roles: List[ResumeRole] = Field(default_factory=list)
    education: List = Field(default_factory=list)  # Can be strings or EducationEntry dicts
    certifications: List[str] = Field(default_factory=list)
    awards: List[str] = Field(default_factory=list)
    
    # Legacy field alias
    @property
    def summary_bullets(self) -> List[str]:
        return self.summary
    
    @property
    def education_strings(self) -> List[str]:
        """Convert education entries to strings."""
        result = []
        for edu in self.education:
            if isinstance(edu, str):
                result.append(edu)
            elif isinstance(edu, dict):
                parts = []
                if edu.get('degree'):
                    parts.append(edu['degree'])
                if edu.get('institution'):
                    parts.append(edu['institution'])
                if edu.get('year'):
                    parts.append(edu['year'])
                result.append(", ".join(parts) if parts else str(edu))
            else:
                result.append(str(edu))
        return result


# =============================================================================
# MODULAR OUTPUT SCHEMAS (NEW)
# =============================================================================

class SkillCategory(BaseModel):
    """A category of skills."""
    category: str  # e.g., "Technical Skills", "Tools & Platforms", "Soft Skills"
    skills: List[str]


class HeaderOutput(BaseModel):
    """Output from tailor_header prompt."""
    headline: str
    summary: List[str]
    skills: List[SkillCategory]  # Categorized skills


class TailoredBullet(BaseModel):
    """A single tailored bullet point."""
    text: str
    source_bullet_ids: List = Field(default_factory=list)  # Can be strings or ints
    needs_revision: bool = False
    revision_note: Optional[str] = None
    
    @property
    def source_ids_as_strings(self) -> List[str]:
        """Get source bullet IDs as strings."""
        return [str(sid) for sid in self.source_bullet_ids if sid]


class RoleOutput(BaseModel):
    """Output from tailor_role prompt."""
    company: str
    title: str
    dates: str
    bullets: List[TailoredBullet]
    responsibilities_covered: List[str] = Field(default_factory=list)


class ReviewOutput(BaseModel):
    """Output from final_review prompt."""
    gaps_to_confirm: List[str] = Field(default_factory=list)
    questions_for_user: List[str] = Field(default_factory=list)
    change_log: List[str] = Field(default_factory=list)


# =============================================================================
# LEGACY SCHEMAS (for backward compatibility)
# =============================================================================

class MatchItem(BaseModel):
    jd_requirement: str
    matched_bullet_ids: List[str] = Field(default_factory=list)
    strength: Literal["strong", "medium", "weak", "missing"] = "missing"
    notes: Optional[str] = None


class MatchJSON(BaseModel):
    match_map: List[MatchItem] = Field(default_factory=list)
    priority_keywords: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)


class TailoredRole(BaseModel):
    """A complete tailored role for final output."""
    company: str
    title: str
    dates: str
    bullets: List[TailoredBullet]


class TailoredResumeJSON(BaseModel):
    """Complete tailored resume - assembled from modular outputs."""
    tailored_headline: str
    tailored_summary: List[str]
    tailored_skills: List[SkillCategory]  # Categorized skills
    tailored_roles: List[TailoredRole]
    change_log: List[str] = Field(default_factory=list)
    questions_for_user: List[str] = Field(default_factory=list)
    gaps_to_confirm: List[str] = Field(default_factory=list)
    
    @property
    def skills_flat(self) -> List[str]:
        """Get all skills as a flat list (for backward compatibility)."""
        all_skills = []
        for cat in self.tailored_skills:
            if isinstance(cat, dict):
                all_skills.extend(cat.get("skills", []))
            elif hasattr(cat, "skills"):
                all_skills.extend(cat.skills)
        return all_skills

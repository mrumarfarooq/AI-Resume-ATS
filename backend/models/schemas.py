from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ComponentScores(BaseModel):
    formatting: float
    keywords: float
    content: float
    skill_validation: float
    ats_compatibility: float

class RoleMatch(BaseModel):
    job_role: str
    match_score: Optional[float] = None
    score_available: bool = False
    message: Optional[str] = None
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    preferred_matches: List[str] = Field(default_factory=list)
    evidence_backed_skills: List[str] = Field(default_factory=list)
    required_skill_count: int = 0
    matched_required_count: int = 0
    preferred_skill_count: int = 0
    matched_preferred_count: int = 0
    score_method: str = ""


class JobDescriptionMatch(BaseModel):
    job_title: str = ""
    match_score: Optional[float] = None
    score_available: bool = False
    message: Optional[str] = None

    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    preferred_matches: List[str] = Field(default_factory=list)
    evidence_backed_skills: List[str] = Field(default_factory=list)

    relevant_projects: List[str] = Field(default_factory=list)
    relevant_experience: List[str] = Field(default_factory=list)

    required_skill_count: int = 0
    matched_required_count: int = 0
    preferred_skill_count: int = 0
    matched_preferred_count: int = 0

    score_method: str = ""

class SkillValidationDetails(BaseModel):
    validated: List[Dict[str, Any]] = Field(default_factory=list)       # [{'skill': str, 'projects': [str]}]
    unvalidated: List[str] = Field(default_factory=list)                # ['Flask', 'A/B Testing', ...]
    total: int = 0
    validated_count: int = 0
    validation_pct: float = 0.0

class IssueDetail(BaseModel):
    issue_title: str
    severity_level: str
    ats_impact: str
    explanation: str
    where_it_appears: str
    how_to_fix: str
    action_items: List[str] = Field(default_factory=list)
    example_improvement: str

class AnalysisResponse(BaseModel):
    ATS_score: float
    component_scores: ComponentScores
    issues_summary: List[str]
    detailed_feedback: List[IssueDetail]
    job_role: Optional[str] = None
    role_match_analysis: Optional[RoleMatch] = None
    job_description_match_analysis: Optional[JobDescriptionMatch] = None
    skill_validation_details: Optional[SkillValidationDetails] = None

    ats_score: float
    keyword_match: float = 0.0
    missing_keywords: List[str] = Field(default_factory=list)
    matched_keywords: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    critical_issues: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    role_match: Optional[RoleMatch] = None
    warnings: List[str] = Field(default_factory=list)
    interpretation: str = ""

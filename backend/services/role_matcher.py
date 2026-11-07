"""Transparent role matching against curated baseline skill profiles."""
import re
from typing import Dict, List
from rapidfuzz import fuzz
from backend.services.role_profiles import ROLE_PROFILES
from backend.utils.matching import normalize_skill


def _match_skill(target: str, evidence: List[str]) -> bool:
    target_norm = normalize_skill(str(target)).strip().lower()
    for item in (evidence or []):
        item_norm = normalize_skill(str(item)).strip().lower()
        if target_norm == item_norm:
            return True
        if target_norm in item_norm.split() or item_norm in target_norm.split():
            return True
        if len(target_norm) >= 4 and fuzz.ratio(target_norm, item_norm) >= 94:
            return True
    return False


def _text_contains_skill(skill: str, text: str) -> bool:
    """Require an explicit mention in the evidence text; do not infer semantically."""
    variants = {skill.lower(), normalize_skill(skill).lower()}
    for variant in variants:
        pattern = r"(?<![a-z0-9])" + re.escape(variant) + r"(?![a-z0-9])"
        if re.search(pattern, text or "", re.IGNORECASE):
            return True
    return False


def calculate_role_match(
    role: str,
    skills: List[str],
    keywords: List[str],
    projects: List[Dict],
    experience: List[Dict],
) -> Dict:
    """Return a role score with explicit evidence and no inferred resume claims."""
    profile = ROLE_PROFILES.get(role)
    if not profile:
        return {
            "job_role": role,
            "match_score": None,
            "score_available": False,
            "message": "A curated skill profile is not available for this custom role. No score has been generated rather than inventing role requirements.",
            "matched_skills": [],
            "missing_skills": [],
            "preferred_matches": [],
            "evidence_backed_skills": [],
            "relevant_projects": [],
            "relevant_experience": [],
            "required_skill_count": 0,
            "matched_required_count": 0,
            "score_method": "No custom profile; no score generated.",
        }

    resume_evidence = (skills or []) + (keywords or [])
    required = profile["required_skills"]
    preferred = profile["preferred_skills"]
    matched_required = [s for s in required if _match_skill(s, resume_evidence)]
    missing_required = [s for s in required if s not in matched_required]
    matched_preferred = [s for s in preferred if _match_skill(s, resume_evidence)]

    project_evidence = []
    relevant_projects = []
    for project in (projects or []):
        if not isinstance(project, dict):
            continue
        title = str(project.get("title") or "Untitled project")
        description = str(project.get("description") or "")
        project_evidence.append((title, f"{title} {description}"))
        if any(_text_contains_skill(skill, description + " " + title) for skill in matched_required):
            relevant_projects.append(title)

    experience_evidence = []
    relevant_experience = []
    for entry in (experience or []):
        if not isinstance(entry, dict):
            continue
        title = str(entry.get("job_title") or "Experience entry")
        description = str(entry.get("description") or "")
        company = str(entry.get("company") or "")
        text = f"{title} {company} {description}"
        experience_evidence.append((title, text))
        if any(_text_contains_skill(skill, text) for skill in matched_required):
            relevant_experience.append(title)

    evidence_backed = [
        skill for skill in matched_required
        if any(_text_contains_skill(skill, text) for _, text in project_evidence + experience_evidence)
    ]

    required_coverage = len(matched_required) / len(required) if required else 0.0
    evidence_coverage = len(evidence_backed) / len(required) if required else 0.0
    preferred_coverage = len(matched_preferred) / len(preferred) if preferred else 0.0
    score = round(required_coverage * 70 + evidence_coverage * 20 + preferred_coverage * 10, 1)

    return {
        "job_role": role,
        "match_score": score,
        "score_available": True,
        "matched_skills": matched_required,
        "missing_skills": missing_required,
        "preferred_matches": matched_preferred,
        "evidence_backed_skills": evidence_backed,
        "relevant_projects": relevant_projects,
        "relevant_experience": relevant_experience,
        "required_skill_count": len(required),
        "matched_required_count": len(matched_required),
        "preferred_skill_count": len(preferred),
        "matched_preferred_count": len(matched_preferred),
        "score_method": "70% required-skill coverage + 20% explicit project/experience evidence + 10% preferred-skill coverage. Broad baseline profile; not an employer-specific hiring probability.",
    }

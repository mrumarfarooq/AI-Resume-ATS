"""Transparent matching against an employer-provided job description."""

import re
from typing import Dict, List

from backend.utils.matching import normalize_skill


def _match_skill(target: str, evidence: List[str]) -> bool:
    target_norm = normalize_skill(str(target)).strip().lower()

    if not target_norm:
        return False

    for item in evidence or []:
        item_norm = normalize_skill(str(item)).strip().lower()

        if target_norm == item_norm:
            return True

        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(target_norm)
            + r"(?![a-z0-9])"
        )

        if re.search(pattern, item_norm):
            return True

    return False


def _text_contains_skill(skill: str, text: str) -> bool:
    variants = {
        str(skill).strip().lower(),
        normalize_skill(str(skill)).strip().lower(),
    }

    for variant in variants:
        if not variant:
            continue

        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(variant)
            + r"(?![a-z0-9])"
        )

        if re.search(pattern, text or "", re.IGNORECASE):
            return True

    return False


def calculate_job_description_match(
    job_data: Dict,
    skills: List[str],
    keywords: List[str],
    projects: List[Dict],
    experience: List[Dict],
) -> Dict:
    """Compare parsed resume evidence against extracted JD requirements."""

    required = job_data.get("required_skills", [])
    preferred = job_data.get("preferred_skills", [])

    resume_evidence = (skills or []) + (keywords or [])

    matched_required = [
        skill for skill in required
        if _match_skill(skill, resume_evidence)
    ]

    missing_required = [
        skill for skill in required
        if skill not in matched_required
    ]

    matched_preferred = [
        skill for skill in preferred
        if _match_skill(skill, resume_evidence)
    ]

    project_evidence = []
    relevant_projects = []

    for project in projects or []:
        if not isinstance(project, dict):
            continue

        title = str(project.get("title") or "Untitled project")
        description = str(project.get("description") or "")
        technologies = project.get("technologies") or []

        text = f"{title} {description} {' '.join(map(str, technologies))}"
        project_evidence.append(text)

        if any(
            _text_contains_skill(skill, text)
            for skill in matched_required
        ):
            relevant_projects.append(title)

    experience_evidence = []
    relevant_experience = []

    for entry in experience or []:
        if not isinstance(entry, dict):
            continue

        title = str(entry.get("job_title") or "Experience entry")
        company = str(entry.get("company") or "")
        description = str(entry.get("description") or "")
        text = f"{title} {company} {description}"

        experience_evidence.append(text)

        if any(
            _text_contains_skill(skill, text)
            for skill in matched_required
        ):
            relevant_experience.append(title)

    all_evidence = project_evidence + experience_evidence

    evidence_backed = [
        skill for skill in matched_required
        if any(
            _text_contains_skill(skill, text)
            for text in all_evidence
        )
    ]

    if not required:
        return {
            "job_title": job_data.get("job_title", ""),
            "match_score": None,
            "score_available": False,
            "message": (
                "No explicit required skills were identified in this "
                "job description. A match score cannot be calculated reliably."
            ),
            "matched_skills": [],
            "missing_skills": [],
            "preferred_matches": matched_preferred,
            "evidence_backed_skills": evidence_backed,
            "relevant_projects": relevant_projects,
            "relevant_experience": relevant_experience,
            "required_skill_count": 0,
            "matched_required_count": 0,
            "score_method": "No score generated.",
        }

    required_coverage = len(matched_required) / len(required)
    preferred_coverage = (
        len(matched_preferred) / len(preferred)
        if preferred else 0.0
    )
    evidence_coverage = len(evidence_backed) / len(required)

    score = round(
        required_coverage * 70
        + preferred_coverage * 10
        + evidence_coverage * 20,
        1,
    )

    return {
        "job_title": job_data.get("job_title", ""),
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
        "score_method": (
            "70% required-skill coverage + 10% preferred-skill coverage "
            "+ 20% explicit project/experience evidence. "
            "This is a resume-to-JD comparison, not a hiring probability."
        ),
    }
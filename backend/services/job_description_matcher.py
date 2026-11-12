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

def _get_description_evidence(
    projects: List[Dict],
    experience: List[Dict],
) -> List[Dict]:
    """Collect meaningful project and experience descriptions only."""

    evidence = []

    for project in projects or []:
        if not isinstance(project, dict):
            continue

        description = str(project.get("description") or "").strip()

        if description:
            evidence.append({
                "type": "project",
                "title": str(project.get("title") or "Untitled project"),
                "description": description,
            })

    for entry in experience or []:
        if not isinstance(entry, dict):
            continue

        description = str(entry.get("description") or "").strip()

        if description:
            evidence.append({
                "type": "experience",
                "title": str(entry.get("job_title") or "Experience entry"),
                "description": description,
            })

    return evidence


def _skill_in_resume_list(
    skill: str,
    resume_skills: List[str],
) -> bool:
    """Check exact normalized skill matches."""

    return _match_skill(skill, resume_skills or [])


def _skill_has_practical_evidence(
    skill: str,
    evidence: List[Dict],
) -> bool:
    """
    Require a skill mention and an implementation action
    in the same sentence.

    This identifies resume-described implementation evidence;
    it does not independently verify the candidate's work.
    """

    action_verbs = {
        "built", "build", "developed", "develop",
        "implemented", "implement", "designed", "design",
        "created", "create", "integrated", "integrate",
        "configured", "configure", "deployed", "deploy",
        "trained", "train", "optimized", "optimize",
        "automated", "automate", "tested", "test",
        "maintained", "maintain", "debugged", "debug",
        "analyzed", "analyze", "cleaned", "clean",
        "queried", "query", "managed", "manage",
        "migrated", "migrate", "secured", "secure",
        "engineered", "engineer", "visualized", "visualize",
        "executed", "execute", "performed", "perform",
        "processed", "process",
    }

    for item in evidence:
        description = str(
            item.get("description") or ""
        )

        sentences = re.split(r"[.!?;\n]+", description)

        for sentence in sentences:
            if not _text_contains_skill(skill, sentence):
                continue

            words = set(
                re.findall(r"[a-zA-Z]+", sentence.lower())
            )

            if words.intersection(action_verbs):
                return True

    return False

def _meaningful_words(text: str) -> set:
    """Extract meaningful words for responsibility comparison."""

    stop_words = {
        "a", "an", "the", "and", "or", "to", "of", "in",
        "on", "for", "with", "by", "as", "is", "are",
        "be", "will", "must", "should", "have", "has",
        "using", "use", "work", "working",
    }

    words = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]*", text.lower())

    return {
        word
        for word in words
        if len(word) > 2 and word not in stop_words
    }


def _responsibility_matches(
    responsibility: str,
    evidence: List[Dict],
) -> bool:
    """Compare a JD responsibility with actual resume descriptions."""

    required_words = _meaningful_words(responsibility)

    if len(required_words) < 2:
        return False

    for item in evidence:
        evidence_words = _meaningful_words(
            item.get("description", "")
        )

        overlap = required_words.intersection(evidence_words)

        if (
            len(overlap) >= 2
            and len(overlap) / len(required_words) >= 0.60
        ):
            return True

    return False

def calculate_job_description_match(
    job_data: Dict,
    skills: List[str],
    projects: List[Dict],
    experience: List[Dict],
    education: List[Dict],
    experience_months: int,
    experience_status: str,
) -> Dict:
    """Calculate a transparent, evidence-based resume-to-JD match."""

    required = job_data.get("required_skills", [])
    preferred = job_data.get("preferred_skills", [])
    responsibilities = job_data.get("responsibilities", [])
    experience_requirements = job_data.get("experience_requirements", [])
    education_requirements = job_data.get("education_requirements", [])
    locations = job_data.get("locations", [])

    required = required if isinstance(required, list) else []
    preferred = preferred if isinstance(preferred, list) else []
    responsibilities = responsibilities if isinstance(responsibilities, list) else []
    experience_requirements = (
        experience_requirements
        if isinstance(experience_requirements, list) else []
    )
    education_requirements = (
        education_requirements
        if isinstance(education_requirements, list) else []
    )
    locations = locations if isinstance(locations, list) else []

    skills = skills if isinstance(skills, list) else []
    projects = projects if isinstance(projects, list) else []
    experience = experience if isinstance(experience, list) else []
    education = education if isinstance(education, list) else []

    evidence = _get_description_evidence(projects, experience)

    # --------------------------------------------------
    # --------------------------------------------------
    # 1. Classify skill evidence
    # --------------------------------------------------

    def _get_skill_evidence_category(skill):

        # Strongest evidence: skill + action in description
        if _skill_has_practical_evidence(skill, evidence):
            return "demonstrated"

        # Skill appears in project or experience description
        if any(
            _text_contains_skill(skill, item["description"])
            for item in evidence
        ):
            return "described"

        # Skill appears in resume skills or project technologies
        project_technologies = []

        for project in projects:
            if not isinstance(project, dict):
                continue

            technologies = project.get("technologies", [])

            if isinstance(technologies, list):
                project_technologies.extend(
                    str(item).strip()
                    for item in technologies
                    if item
                )

        if (
            _skill_in_resume_list(skill, skills)
            or _skill_in_resume_list(skill, project_technologies)
        ):
            return "mentioned"

        return "not_found"

    # --------------------------------------------------
    # 2. Required skill evidence classification
    # --------------------------------------------------

    mentioned_skills = []
    described_skills = []
    demonstrated_skills = []

    for skill in required:

        category = _get_skill_evidence_category(skill)

        if category == "mentioned":
            mentioned_skills.append(skill)

        elif category == "described":
            described_skills.append(skill)

        elif category == "demonstrated":
            demonstrated_skills.append(skill)

    matched_required = [
        skill for skill in required
        if _get_skill_evidence_category(skill) != "not_found"
    ]

    missing_required = [
        skill for skill in required
        if _get_skill_evidence_category(skill) == "not_found"
    ]

    # --------------------------------------------------
    # 3. Preferred skill coverage
    # --------------------------------------------------

    matched_preferred = [
        skill for skill in preferred
        if _get_skill_evidence_category(skill) != "not_found"
    ]

    # --------------------------------------------------
    # 4. Practical skill evidence
    # --------------------------------------------------

    evidence_backed = list(demonstrated_skills)

    relevant_projects = list(dict.fromkeys(
        item["title"]
        for item in evidence
        if (
            item["type"] == "project"
            and any(
                _text_contains_skill(skill, item["description"])
                for skill in required
            )
        )
    ))

    relevant_experience = list(dict.fromkeys(
        item["title"]
        for item in evidence
        if (
            item["type"] == "experience"
            and any(
                _text_contains_skill(skill, item["description"])
                for skill in required
            )
        )
    ))
    # --------------------------------------------------
    # 4. Responsibility alignment
    # --------------------------------------------------

    matched_responsibilities = [
        item for item in responsibilities
        if _responsibility_matches(item, evidence)
    ]

    missing_responsibilities = [
        item for item in responsibilities
        if item not in matched_responsibilities
    ]

    # --------------------------------------------------
    # 5. Experience assessment
    # --------------------------------------------------

    minimum = job_data.get("minimum_experience_months")
    maximum = job_data.get("maximum_experience_months")
    experience_scope = str(
        job_data.get("experience_scope", "unspecified")
    ).lower()

    experience_assessment = None
    experience_score = None

    has_numeric_experience = (
        isinstance(minimum, int)
        and not isinstance(minimum, bool)
    ) or (
        isinstance(maximum, int)
        and not isinstance(maximum, bool)
    )

    if has_numeric_experience:

        # Total employment experience cannot prove
        # role-specific relevant experience.
        if experience_scope == "relevant":
            experience_assessment = "unverified"

        elif experience_status == "verified":

            meets_minimum = (
                minimum is None or experience_months >= minimum
            )

            meets_maximum = (
                maximum is None or experience_months <= maximum
            )

            if meets_minimum and meets_maximum:
                experience_assessment = "met"
                experience_score = 100.0
            else:
                experience_assessment = "not_met"
                experience_score = 0.0

        elif experience_status == "partially_verified":

            # Known experience already exceeds the maximum.
            if maximum is not None and experience_months > maximum:
                experience_assessment = "not_met"
                experience_score = 0.0

            # A minimum-only requirement can be proven
            # by verified months even if other periods are unknown.
            elif (
                maximum is None
                and minimum is not None
                and experience_months >= minimum
            ):
                experience_assessment = "met"
                experience_score = 100.0

            else:
                experience_assessment = "unverified"

        else:
            experience_assessment = "unverified"

    elif experience_requirements:
        experience_assessment = "unverified"
    # --------------------------------------------------
    # 6. Education assessment
    # --------------------------------------------------

    education_level = job_data.get(
        "education_level", "unspecified"
    )

    education_assessment = None
    education_score = None

    level_order = {
        "high_school": 1,
        "diploma": 2,
        "bachelor": 3,
        "master": 4,
        "doctorate": 5,
    }

    candidate_levels = []

    for item in education:
        if not isinstance(item, dict):
            continue

        degree = str(item.get("degree") or "").lower()

        if "doctor" in degree or "ph.d" in degree or "phd" in degree:
            candidate_levels.append(5)
        elif "master" in degree or "m.tech" in degree or "m.e." in degree:
            candidate_levels.append(4)
        elif (
            "bachelor" in degree
            or "b.e." in degree
            or "b.tech" in degree
            or "b.sc" in degree
            or "bca" in degree
        ):
            candidate_levels.append(3)
        elif "diploma" in degree:
            candidate_levels.append(2)
        elif "high school" in degree or "secondary" in degree:
            candidate_levels.append(1)

    has_education_criteria = (
        bool(education_requirements)
        or education_level != "unspecified"
    )

    if has_education_criteria:
        if not education:
            education_assessment = "not_found_in_resume"
            education_score = 0.0

        elif (
            education_level in level_order
            and candidate_levels
        ):
            if max(candidate_levels) >= level_order[education_level]:
                education_assessment = "met"
                education_score = 100.0
            else:
                education_assessment = "not_met"
                education_score = 0.0

        elif education_requirements:
            requirement_words = set()

            for requirement in education_requirements:
                requirement_words.update(
                    _meaningful_words(requirement)
                )

            candidate_words = set()

            for item in education:
                if isinstance(item, dict):
                    candidate_words.update(
                        _meaningful_words(
                            str(item.get("degree") or "")
                        )
                    )

            overlap = requirement_words.intersection(candidate_words)

            if requirement_words and overlap:
                education_assessment = "met"
                education_score = 100.0
            else:
                education_assessment = "unverified"

        else:
            education_assessment = "unverified"

    # --------------------------------------------------
    # 7. Build applicable scoring components
    # --------------------------------------------------

    component_scores = {}
    weights = {}

    if required:
        component_scores["required_skills"] = round(
            len(matched_required) / len(required) * 100, 1
        )
        weights["required_skills"] = 35

        component_scores["practical_evidence"] = round(
            len(evidence_backed) / len(required) * 100, 1
        )
        weights["practical_evidence"] = 25

    if responsibilities:
        component_scores["responsibilities"] = round(
            len(matched_responsibilities) / len(responsibilities) * 100,
            1,
        )
        weights["responsibilities"] = 15

    if has_numeric_experience and experience_score is not None:
        component_scores["experience"] = experience_score
        weights["experience"] = 10

    if education_score is not None:
        component_scores["education"] = education_score
        weights["education"] = 5

    if preferred:
        component_scores["preferred_skills"] = round(
            len(matched_preferred) / len(preferred) * 100,
            1,
        )
        weights["preferred_skills"] = 10

    # --------------------------------------------------
    # 8. Score availability and normalization
    # --------------------------------------------------

    assessable_criteria = list(component_scores.keys())

    all_criteria = [
        "required_skills",
        "practical_evidence",
        "responsibilities",
        "experience",
        "education",
        "preferred_skills",
    ]

    unassessed_criteria = [
        criterion
        for criterion in all_criteria
        if criterion not in component_scores
    ]

    limitations = [
        "This is a resume-to-JD comparison, not a hiring probability.",
        "Skills mentioned in the resume are not automatically proof of practical experience.",
        "Missing information means not found in the resume; it does not prove the candidate lacks that qualification.",
    ]

    if experience_assessment == "unverified":
        limitations.append(
            "Experience requirements could not be reliably verified from the available dates or JD details."
        )

    if education_assessment == "unverified":
        limitations.append(
            "Education requirements could not be reliably verified from the available degree information."
        )

    if locations:
        location_assessment = "unverified"
        limitations.append(
            "Job location was extracted, but the resume location was not available for comparison."
        )
    else:
        location_assessment = "not_specified"

    if not weights:
        score = None
        score_available = False
        message = (
            "The job description does not contain enough assessable "
            "criteria to calculate a reliable match score."
        )
        score_method = "No score generated."
    else:
        total_weight = sum(weights.values())

        score = round(
            sum(
                component_scores[key] * weights[key]
                for key in weights
            ) / total_weight,
            1,
        )

        score_available = True
        message = None

        score_method = (
            "Required skills 35%, practical evidence 25%, "
            "responsibilities 15%, experience 10%, education 5%, "
            "preferred skills 10%. Only applicable and assessable "
            "components are included; their weights are normalized "
            "proportionally to 100%."
        )

    return {
        "job_title": job_data.get("job_title", ""),
        "match_score": score,
        "score_available": score_available,
        "message": message,

        "matched_skills": matched_required,
        "missing_skills": missing_required,
        "preferred_matches": matched_preferred,
        "evidence_backed_skills": evidence_backed,

        "mentioned_skills": mentioned_skills,
        "described_skills": described_skills,
        "demonstrated_skills": demonstrated_skills,

        "relevant_projects": relevant_projects,
        "relevant_experience": relevant_experience,

        "required_skill_count": len(required),
        "matched_required_count": len(matched_required),
        "preferred_skill_count": len(preferred),
        "matched_preferred_count": len(matched_preferred),

        "required_skills": required,
        "preferred_skills": preferred,
        "responsibilities": responsibilities,
        "experience_requirements": experience_requirements,
        "education_requirements": education_requirements,
        "locations": locations,

        "component_scores": component_scores,
        "assessable_criteria": assessable_criteria,
        "unassessed_criteria": unassessed_criteria,

        "matched_responsibilities": matched_responsibilities,
        "missing_responsibilities": missing_responsibilities,

        "experience_assessment": experience_assessment,
        "education_assessment": education_assessment,
        "location_assessment": location_assessment,

        "limitations": limitations,
        "score_method": score_method,
    }
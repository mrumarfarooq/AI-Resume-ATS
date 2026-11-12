import spacy
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Optional
from backend.services.groq_parser import parse_resume
from backend.services.role_matcher import calculate_role_match
from backend.services.groq_parser import parse_job_description
from backend.services.job_description_matcher import calculate_job_description_match
from backend.services.feedback_engine import analyze_issues, generate_issues_summary
from backend.utils.experience_utils import calculate_experience
from backend.services.ats_scorer import (
    calculate_overall_score, validate_skills_with_projects,
    generate_critical_issues,
)


def analyze_full_resume(
    resume_text: str,
    nlp: spacy.Language,
    embedder: SentenceTransformer,
    job_role: Optional[str] = None,
    job_description: Optional[str] = None,
) -> Dict:
    import logging
    logger = logging.getLogger('ats_resume_scorer')
    parsed_resume = parse_resume(resume_text)
    logger.info(f"Groq parsed summary length: {len(parsed_resume.get('professional_summary', ''))} characters")
    logger.info(f"Groq parsed skills count: {len(parsed_resume.get('skills', []))}")
    logger.info(f"Groq parsed experience count: {len(parsed_resume.get('experience', []))}")

    skills          = parsed_resume.get('skills', [])
    projects        = parsed_resume.get('projects', [])
    keywords        = parsed_resume.get('keywords', [])
    action_verbs    = parsed_resume.get('action_verbs', [])

    experience_calculation = calculate_experience(
        parsed_resume.get('experience', [])
    )

    experience_months = experience_calculation["total_months"]

    contact_info = {
        'email':     parsed_resume.get('email'),
        'phone':     parsed_resume.get('phone'),
        'linkedin':  parsed_resume.get('linkedin'),
        'github':    parsed_resume.get('github'),
        'portfolio': None,
    }
    skill_validation = validate_skills_with_projects(
        skills=skills,
        projects=projects,
        experience_entries=parsed_resume.get('experience', []),
        embedder=embedder,
    )

    role_match_result = None
    if job_role and job_role.strip():
        role_match_result = calculate_role_match(
            role=job_role.strip(),
            skills=skills,
            keywords=keywords,
            projects=projects,
            experience=parsed_resume.get('experience', []),
        )


    job_description_match_result = None

    if job_description and job_description.strip():
        job_data = parse_job_description(job_description)

        job_description_match_result = (
            calculate_job_description_match(
                job_data=job_data,
                skills=skills,
                projects=projects,
                experience=parsed_resume.get('experience', []),
                education=parsed_resume.get('education', []),
                experience_months=experience_months,
                experience_status=experience_calculation["status"],
            )
        )


    from backend.utils.file_utils import (
        get_default_grammar_results, get_default_location_results,
    )
    grammar_results  = get_default_grammar_results()
    location_results = get_default_location_results()

    scores = calculate_overall_score(
        text=resume_text,
        parsed_resume=parsed_resume,
        skills=skills,
        keywords=keywords,
        action_verbs=action_verbs,
        skill_validation_results=skill_validation,
        grammar_results=grammar_results,
        location_results=location_results,
        experience_months=experience_months,
    )


    detailed_feedback = analyze_issues(
        resume_text=resume_text,
        parsed_resume=parsed_resume,
        skills=skills,
        projects=projects,
        action_verbs=action_verbs,
        skill_validation=skill_validation,
        scores=scores,
        contact_info=contact_info,
    )

    issues_summary = generate_issues_summary(detailed_feedback)

    validated_raw   = skill_validation.get('validated_skills', [])
    unvalidated_raw = skill_validation.get('unvalidated_skills', [])
    total_skills    = len(validated_raw) + len(unvalidated_raw)
    val_pct         = round((len(validated_raw) / total_skills * 100) if total_skills > 0 else 0, 1)

    skill_validation_details = {
        "validated": [
            {
                "skill":    item['skill'],
                "projects": item.get('projects', []),
            }
            for item in validated_raw
        ],
        "unvalidated":     unvalidated_raw,
        "total":           total_skills,
        "validated_count": len(validated_raw),
        "validation_pct":  val_pct,
    }

    return {
        "ATS_score":          scores['overall_score'],
        "ats_score":          scores['overall_score'],
        "job_role":           job_role.strip() if job_role else None,
        "role_match_analysis": role_match_result,
        "job_description_match_analysis": job_description_match_result,
        "component_scores": {
            "formatting":       scores['formatting_score'],
            "keywords":         scores['keywords_score'],
            "content":          scores['content_score'],
            "skill_validation": scores['skill_validation_score'],
            "ats_compatibility": scores['ats_compatibility_score'],
        },
        "issues_summary":    issues_summary,
        "detailed_feedback": detailed_feedback,
        "critical_issues": generate_critical_issues(scores, grammar_results, location_results),
        "suggestions": generate_resume_recommendations(
            parsed_resume=parsed_resume,
            scores=scores,
            detailed_feedback=detailed_feedback,
            contact_info=contact_info,
            job_role=job_role,
            role_match_result=role_match_result,
            job_description_match_result=job_description_match_result,
        ),
        "warnings": [
            "Grammar checking is not configured; no grammar-quality bonus was applied.",
            "Location privacy detection is not configured; no location-based deduction was applied.",
        ],
        "skills":            skills,
        "matched_keywords":  list(keywords[:20]),
        "missing_keywords":  [],
        "strengths": _generate_strengths(parsed_resume, skills, projects, action_verbs, skill_validation, scores),
        "interpretation":    scores.get('overall_interpretation', ''),
        "skill_validation_details": skill_validation_details,
        "experience_months": experience_months,
        "experience_calculation": experience_calculation,
    }

def generate_resume_recommendations(
    parsed_resume: Dict,
    scores: Dict,
    detailed_feedback: List[Dict],
    contact_info: Dict,
    job_role: Optional[str] = None,
    role_match_result: Optional[Dict] = None,
    job_description_match_result: Optional[Dict] = None,
) -> List[str]:

    recommendations = []

    # Collect existing feedback to avoid duplicate suggestions
    covered_text = " ".join(
        str(
            issue.get(field, "")
            if isinstance(issue, dict)
            else getattr(issue, field, "")
        )
        for issue in detailed_feedback
        for field in [
            "issue_title",
            "explanation",
            "where_it_appears",
            "how_to_fix",
        ]
    ).lower()

    def already_covered(*terms):
        return any(term.lower() in covered_text for term in terms)

    def add_recommendation(message: str):
        if message not in recommendations and len(recommendations) < 3:
            recommendations.append(message)

    skills = parsed_resume.get("skills") or []
    projects = parsed_resume.get("projects") or []
    summary = str(
        parsed_resume.get("professional_summary") or ""
    ).strip()


    # --------------------------------------------------
    # 1. Job Description-based recommendations
    # --------------------------------------------------

    if job_description_match_result:

        jd_missing = job_description_match_result.get(
            "missing_skills", []
        )

        if jd_missing:
            missing_list = ", ".join(str(s) for s in jd_missing[:5])

            add_recommendation(
                f"The job description requires skills not found in "
                f"your resume: {missing_list}. Add them only if you "
                f"genuinely possess those skills; otherwise, prioritize "
                f"learning and demonstrating them through practical work."
            )

        jd_mentioned = job_description_match_result.get(
            "mentioned_skills", []
        )

        jd_described = job_description_match_result.get(
            "described_skills", []
        )

        jd_demonstrated = job_description_match_result.get(
            "demonstrated_skills", []
        )

        skills_without_evidence = [
            skill
            for skill in jd_mentioned
            if skill not in jd_described
            and skill not in jd_demonstrated
        ]

        if skills_without_evidence:
            mentioned_list = ", ".join(
                str(s) for s in skills_without_evidence[:5]
            )
            add_recommendation(
                f"Your resume lists {mentioned_list} in the Skills section, "
                f"but does not provide practical evidence of these skills. Where "
                f"applicable, describe how you used {mentioned_list} in an "
                f"actual project or professional work."
            )

        missing_responsibilities = (
            job_description_match_result.get(
                "missing_responsibilities", []
            )
        )

        if missing_responsibilities:
            responsibility = str(
                missing_responsibilities[0]
            ).strip()

            add_recommendation(
                f"The job description mentions this responsibility, "
                f"which is not clearly demonstrated in your resume: "
                f"{responsibility}. If you have performed this work, "
                f"describe your actual contribution."
            )

        if (
            job_description_match_result.get("experience_assessment")
            == "unverified"
        ):
            add_recommendation(
                "Review your experience dates and role descriptions "
                "so recruiters can assess your employment timeline "
                "against the job requirements."
            )

    # --------------------------------------------------
    # 2. Selected job role-based recommendations
    # --------------------------------------------------

    elif (
        job_role
        and role_match_result
        and role_match_result.get("score_available")
    ):

        missing_required = role_match_result.get(
            "missing_skills", []
        )

        if missing_required:
            missing_list = ", ".join(
                str(s) for s in missing_required[:5]
            )

            add_recommendation(
                f"For the {job_role} role, these baseline required "
                f"skills are not listed in your resume: {missing_list}. "
                f"Include only skills you genuinely possess; work on "
                f"the remaining gaps before claiming them."
            )

        matched_required = role_match_result.get(
            "matched_skills", []
        )

        evidence_backed = role_match_result.get(
            "evidence_backed_skills", []
        )

        skills_without_evidence = [
            skill for skill in matched_required
            if skill not in evidence_backed
        ]

        if skills_without_evidence:
            skill_list = ", ".join(
                str(s) for s in skills_without_evidence[:5]
            )

            add_recommendation(
                f"For your selected {job_role} role, strengthen the "
                f"project or experience evidence for these listed "
                f"skills: {skill_list}. Describe actual implementation "
                f"work rather than simply repeating skill names."
            )

    # --------------------------------------------------
    # 3. Resume-specific recommendations
    # --------------------------------------------------

    if not summary and not already_covered(
        "professional summary",
        "summary section",
    ):
        add_recommendation(
            "Add a concise Professional Summary describing your "
            "actual technical background, experience level, and "
            "career focus."
        )

    if not projects and not already_covered(
        "project section",
        "projects section",
    ):
        add_recommendation(
            "Include relevant technical projects that demonstrate "
            "your practical use of the skills listed in your resume."
        )

    if projects:
        weak_projects = []

        for project in projects:
            if not isinstance(project, dict):
                continue

            description = str(
                project.get("description") or ""
            ).strip()

            technologies = project.get("technologies") or []

            if isinstance(technologies, list):
                has_technologies = bool(technologies)
            else:
                has_technologies = bool(
                    str(technologies).strip()
                )

            if len(description) < 80 or not has_technologies:
                weak_projects.append(project)

        if weak_projects and not already_covered(
            "project description",
            "project details",
            "project contributions",
        ):
            add_recommendation(
                "Expand your project descriptions with the actual "
                "problem solved, technologies used, implementation "
                "details, and your individual contribution."
            )


    # Project source-code visibility
    if (
        projects
        and not contact_info.get("github")
        and not already_covered(
            "github",
            "github profile",
            "repository link",
            "source code link",
        )
    ):

        project_titles = [
            str(project.get("title"))
            for project in projects[:2]
            if isinstance(project, dict) and project.get("title")
        ]

        project_names = (
            ", ".join(project_titles[:-1]) + " and " + project_titles[-1]
            if len(project_titles) > 1
            else project_titles[0] if project_titles
            else ""
        )

        project_reference = (
            f" such as {project_names}"
            if project_names
            else ""
        )

        add_recommendation(
            f"Your resume includes technical projects{project_reference}, "
            "but your resume does not include a detectable GitHub profile link. If you have public "
            "repositories for these projects, add their direct links to "
            "the corresponding project entries. Include a README explaining "
            "the problem, technologies, implementation, and setup instructions "
            "so recruiters can review your actual development work."
        )

    has_profile_link = any(
        contact_info.get(field)
        for field in ["github", "linkedin", "portfolio"]
    )

    if not has_profile_link and not already_covered(
        "github",
        "linkedin",
        "portfolio",
        "profile link",
    ):
        add_recommendation(
            "Add your GitHub, LinkedIn, or portfolio link if you have "
            "a relevant public profile to showcase your work."
        )

    # --------------------------------------------------
    # 4. Score-based recommendations
    # --------------------------------------------------

    if (
        scores.get("formatting_score", 0) < 14
        and not already_covered(
            "formatting",
            "section organization",
            "resume layout",
        )
    ):
        add_recommendation(
            "Improve resume organization using consistent section "
            "headings, readable spacing, and clearly structured content."
        )

    if (
        scores.get("keywords_score", 0) < 18
        and not already_covered(
            "keyword",
            "technical skills",
        )
    ):
        add_recommendation(
            "Review relevant job descriptions and include matching "
            "technical keywords only where they accurately reflect "
            "your skills and experience."
        )

    if (
        scores.get("ats_compatibility_score", 0) < 12
        and not already_covered(
            "ats compatibility",
            "ats-friendly",
            "tables",
            "columns",
        )
    ):
        add_recommendation(
            "Use a simple, readable resume layout and avoid complex "
            "tables, multiple columns, and decorative elements."
        )

    # Return only meaningful, resume-specific recommendations.
    return recommendations[:3]


def _generate_strengths(
    parsed_resume: Dict, skills: List, projects: List,
    action_verbs: List, skill_validation: Dict, scores: Dict,
) -> List[str]:
    """Generate evidence-based strengths from actual resume content."""

    strengths = []

    # 1. Experience: Require meaningful work details
    experience = parsed_resume.get("experience") or []

    if any(
        isinstance(item, dict) and any(
            str(item.get(field) or "").strip()
            for field in ["job_title", "company", "description"]
        )
        for item in experience
    ):
        strengths.append(
            "Professional experience is documented with relevant role, "
            "organization, or responsibility details."
        )

    # 2. Projects: Require actual project details
    if any(
        isinstance(project, dict)
        and str(project.get("title") or "").strip()
        and str(project.get("description") or "").strip()
        for project in projects
    ):
        strengths.append(
            "Technical projects demonstrate practical implementation "
            "and the use of relevant technologies."
        )

    # 3. Education: Require actual academic details
    education = parsed_resume.get("education") or []

    if any(
        isinstance(item, dict) and any(
            str(item.get(field) or "").strip()
            for field in ["degree", "institution", "university", "college"]
        )
        for item in education
    ):
        strengths.append(
            "Academic qualifications include identifiable degree "
            "or institution details."
        )

    # 4. Skills: Require actual skill entries
    if (
        parsed_resume.get("skills_section_present") is True
        and any(str(skill).strip() for skill in skills)
    ):
        strengths.append(
            "Technical skills are clearly listed for recruiter reference."
        )
    # 5. Professional Summary: Require actual summary text
    summary = str(
        parsed_resume.get("professional_summary") or ""
    ).strip()

    if summary:
        strengths.append(
            "Professional Summary provides a concise overview "
            "of the candidate's background and career focus."
        )


    # 6. Formatting: Require a strong formatting score
    if scores.get("formatting_score", 0) >= 16:
        strengths.append(
            "Resume follows a well-organized format with clear "
            "sections and ATS-friendly structure."
        )

    return strengths

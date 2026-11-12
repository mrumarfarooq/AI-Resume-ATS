import pytest

from backend.services.job_description_matcher import (
    calculate_job_description_match,
)


JOB_DATA = {
    "job_title": "Python Developer",
    "required_skills": ["Python"],
    "preferred_skills": [],
    "responsibilities": [],
    "experience_requirements": [],
    "education_requirements": [],
    "education_level": "unspecified",
    "locations": [],
    "experience_scope": "unspecified",
}


@pytest.mark.parametrize(
    (
        "skills",
        "projects",
        "expected_category",
        "expected_score",
    ),
    [
        pytest.param(
            ["Python"],
            [],
            "mentioned",
            58.3,
            id="skills-list-only",
        ),
        pytest.param(
            [],
            [
                {
                    "title": "My Project",
                    "description": "A web application.",
                    "technologies": ["Python"],
                }
            ],
            "mentioned",
            58.3,
            id="project-technologies-only",
        ),
        pytest.param(
            [],
            [
                {
                    "title": "My Project",
                    "description": "The application uses Python.",
                    "technologies": [],
                }
            ],
            "described",
            58.3,
            id="description-without-action",
        ),
        pytest.param(
            [],
            [
                {
                    "title": "My Project",
                    "description": "Developed a web application using Python.",
                    "technologies": ["Python"],
                }
            ],
            "demonstrated",
            100.0,
            id="description-with-implementation-action",
        ),
        pytest.param(
            [],
            [],
            "missing",
            0.0,
            id="skill-completely-missing",
        ),
    ],
)
def test_required_skill_evidence_classification(
    skills,
    projects,
    expected_category,
    expected_score,
):
    result = calculate_job_description_match(
        job_data=JOB_DATA,
        skills=skills,
        projects=projects,
        experience=[],
        education=[],
        experience_months=0,
        experience_status="unverified",
    )

    assert result["score_available"] is True
    assert result["match_score"] == pytest.approx(expected_score)

    assert result["mentioned_skills"] == (
        ["Python"] if expected_category == "mentioned" else []
    )

    assert result["described_skills"] == (
        ["Python"] if expected_category == "described" else []
    )

    assert result["demonstrated_skills"] == (
        ["Python"] if expected_category == "demonstrated" else []
    )

    assert result["missing_skills"] == (
        ["Python"] if expected_category == "missing" else []
    )

    assert result["evidence_backed_skills"] == (
        ["Python"] if expected_category == "demonstrated" else []
    )

from backend.services.job_description_matcher import (
    calculate_job_description_match,
)


job_data = {
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


def run_test(name, skills=None, projects=None):

    result = calculate_job_description_match(
        job_data=job_data,
        skills=skills or [],
        projects=projects or [],
        experience=[],
        education=[],
        experience_months=0,
        experience_status="unverified",
    )

    print(f"\n--- {name} ---")
    print("Mentioned:", result["mentioned_skills"])
    print("Described:", result["described_skills"])
    print("Demonstrated:", result["demonstrated_skills"])
    print("Missing:", result["missing_skills"])
    print("Evidence backed:", result["evidence_backed_skills"])
    print("Score:", result["match_score"])


run_test(
    "Skills list only",
    skills=["Python"],
)

run_test(
    "Project technologies only",
    projects=[
        {
            "title": "My Project",
            "description": "A web application.",
            "technologies": ["Python"],
        }
    ],
)

run_test(
    "Description without action",
    projects=[
        {
            "title": "My Project",
            "description": "The application uses Python.",
            "technologies": [],
        }
    ],
)

run_test(
    "Description with implementation action",
    projects=[
        {
            "title": "My Project",
            "description": "Developed a web application using Python.",
            "technologies": ["Python"],
        }
    ],
)

run_test(
    "Skill completely missing",
)

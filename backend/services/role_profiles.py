"""Curated role skill profiles used for transparent, deterministic role matching.

These are broad baseline profiles, not employer-specific job descriptions.
The score is based only on evidence present in the parsed resume.
"""
ROLE_PROFILES = {
    "Python Developer": {
        "required_skills": ["Python", "OOP", "SQL", "Git", "REST API", "Debugging"],
        "preferred_skills": ["Django", "FastAPI", "Flask", "Pytest", "Linux"],
    },
    "Python Full Stack Developer": {
        "required_skills": ["Python", "HTML", "CSS", "JavaScript", "SQL", "REST API", "Git"],
        "preferred_skills": ["Django", "FastAPI", "React", "MySQL", "PostgreSQL", "Docker"],
    },
    "Backend Developer": {
        "required_skills": ["Python", "SQL", "REST API", "Git", "Database", "Debugging"],
        "preferred_skills": ["FastAPI", "Django", "Flask", "PostgreSQL", "Docker", "Linux"],
    },
    "Data Analyst": {
        "required_skills": ["SQL", "Excel", "Data Analysis", "Data Visualization", "Statistics"],
        "preferred_skills": ["Python", "Pandas", "NumPy", "Power BI", "Tableau", "Matplotlib"],
    },
    "Data Scientist": {
        "required_skills": ["Python", "Statistics", "Data Analysis", "Machine Learning", "SQL"],
        "preferred_skills": ["Pandas", "NumPy", "Scikit-learn", "Matplotlib", "Seaborn", "Jupyter"],
    },
    "Machine Learning Engineer": {
        "required_skills": ["Python", "Machine Learning", "Data Structures", "SQL", "Git"],
        "preferred_skills": ["Scikit-learn", "TensorFlow", "PyTorch", "Docker", "REST API", "MLOps"],
    },
    "SQL Developer": {
        "required_skills": ["SQL", "Database", "Joins", "Subqueries", "Data Modeling"],
        "preferred_skills": ["MySQL", "PostgreSQL", "SQL Server", "Stored Procedures", "Indexes", "Python"],
    },
    "DevOps Engineer": {
        "required_skills": ["Linux", "Git", "Networking", "CI/CD", "Scripting"],
        "preferred_skills": ["Docker", "Kubernetes", "AWS", "Azure", "Jenkins", "Terraform", "Python"],
    },
}

JOB_ROLES = list(ROLE_PROFILES) + ["Other"]

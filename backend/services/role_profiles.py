"""Curated role profiles for transparent, deterministic role matching."""

ROLE_PROFILES = {
    "Python Developer": {
        "required_skills": [
            "Python", "OOP", "SQL", "Git", "REST API", "Debugging"
        ],
        "preferred_skills": [
            "Django", "FastAPI", "Flask", "Pytest", "Linux"
        ],
        "responsibilities": [
            "backend application development",
            "API development and integration",
            "database operations",
            "debugging and testing",
            "code maintenance",
        ],
    },

    "Python Full Stack Developer": {
        "required_skills": [
            "Python", "HTML", "CSS", "JavaScript", "SQL", "REST API", "Git"
        ],
        "preferred_skills": [
            "Django", "FastAPI", "React", "MySQL", "PostgreSQL", "Docker"
        ],
        "responsibilities": [
            "frontend application development",
            "backend application development",
            "API integration",
            "database management",
            "full stack application development",
        ],
    },

    "Backend Developer": {
        "required_skills": [
            "Python", "SQL", "REST API", "Git", "Database", "Debugging"
        ],
        "preferred_skills": [
            "FastAPI", "Django", "Flask", "PostgreSQL", "Docker", "Linux"
        ],
        "responsibilities": [
            "backend service development",
            "API design and development",
            "database operations",
            "server side application logic",
            "debugging and performance optimization",
        ],
    },

    "Data Analyst": {
        "required_skills": [
            "SQL", "Excel", "Data Analysis", "Data Visualization", "Statistics"
        ],
        "preferred_skills": [
            "Python", "Pandas", "NumPy", "Power BI", "Tableau", "Matplotlib"
        ],
        "responsibilities": [
            "data cleaning and preparation",
            "exploratory data analysis",
            "data visualization and reporting",
            "business data analysis",
            "identifying trends and patterns",
        ],
    },

    "Data Scientist": {
        "required_skills": [
            "Python", "Statistics", "Data Analysis", "Machine Learning", "SQL"
        ],
        "preferred_skills": [
            "Pandas", "NumPy", "Scikit-learn", "Matplotlib", "Seaborn", "Jupyter"
        ],
        "responsibilities": [
            "data preprocessing",
            "statistical analysis",
            "machine learning model development",
            "model evaluation",
            "data driven problem solving",
        ],
    },

    "Machine Learning Engineer": {
        "required_skills": [
            "Python", "Machine Learning", "Data Structures", "SQL", "Git"
        ],
        "preferred_skills": [
            "Scikit-learn", "TensorFlow", "PyTorch", "Docker", "REST API", "MLOps"
        ],
        "responsibilities": [
            "machine learning model development",
            "model training and evaluation",
            "model deployment",
            "data preprocessing pipelines",
            "model monitoring and maintenance",
        ],
    },

    "SQL Developer": {
        "required_skills": [
            "SQL", "Database", "Joins", "Subqueries", "Data Modeling"
        ],
        "preferred_skills": [
            "MySQL", "PostgreSQL", "SQL Server",
            "Stored Procedures", "Indexes", "Python"
        ],
        "responsibilities": [
            "SQL query development",
            "database design and maintenance",
            "stored procedure development",
            "query optimization",
            "data retrieval and reporting",
        ],
    },

    "DevOps Engineer": {
        "required_skills": [
            "Linux", "Git", "Networking", "CI/CD", "Scripting"
        ],
        "preferred_skills": [
            "Docker", "Kubernetes", "AWS", "Azure",
            "Jenkins", "Terraform", "Python"
        ],
        "responsibilities": [
            "deployment automation",
            "CI/CD pipeline management",
            "infrastructure management",
            "system monitoring",
            "server administration and troubleshooting",
        ],
    },
}

JOB_ROLES = list(ROLE_PROFILES) + ["Other"]
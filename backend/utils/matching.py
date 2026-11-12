import re
from typing import Dict


def _clean_skill_text(skill: str) -> str:
    """Normalize casing and whitespace without removing meaningful symbols."""
    cleaned = str(skill).strip().lower()
    cleaned = cleaned.replace("–", "-").replace("—", "-")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


SKILL_ALIASES: Dict[str, str] = {
    "reactjs": "react",
    "react.js": "react",
    "angularjs": "angular",
    "vuejs": "vue",
    "vue.js": "vue",
    "nextjs": "next.js",
    "nodejs": "node.js",
    "expressjs": "express",
    "express.js": "express",
    "springboot": "spring boot",
    "golang": "go",
    "natural language processing": "natural language processing",
    "k8s": "kubernetes",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "postgres": "postgresql",
    "dotnet": ".net",
    "tailwindcss": "tailwind",
    "amazon web services": "aws",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    "pyspark": "spark",
    "huggingface": "hugging face",
    "restful api": "rest api",
    "restful apis": "rest api",
    "rest apis": "rest api",
    "rest api development": "rest api",
    "object oriented programming": "oop",
    "object-oriented programming": "oop",
    "data analytics": "data analysis",
    "powerbi": "power bi",
    "ci cd": "ci/cd",
}


def normalize_skill(skill: str) -> str:
    """
    Return a canonical skill name using controlled aliases.

    Ambiguous abbreviations such as AI, ML, CV and Node are
    intentionally not expanded without additional context.
    """
    cleaned = _clean_skill_text(skill)
    return SKILL_ALIASES.get(cleaned, cleaned)
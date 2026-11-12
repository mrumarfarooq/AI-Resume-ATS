import json
import logging
import re
import os
from typing import Dict

from groq import Groq


logger = logging.getLogger("ats_resume_scorer")

GROQ_MODEL = "openai/gpt-oss-120b"

_client = None


def _get_client() -> Groq:
    global _client

    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")

        _client = Groq(api_key=api_key)

    return _client


def _call_groq(
    client: Groq,
    system_prompt: str,
    user_prompt: str
) -> str:

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0,
        max_tokens=4096
    )

    return response.choices[0].message.content.strip()


def _try_parse_json(text: str) -> dict | None:

    cleaned = text.strip()

    if cleaned.startswith("```"):
        first_newline = cleaned.index("\n") if "\n" in cleaned else len(cleaned)
        cleaned = cleaned[first_newline + 1:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


# ============================================================
# RESUME PARSER
# ============================================================

RESUME_SYSTEM_PROMPT = (
    "You are a resume parser. Extract information from the resume "
    "and return ONLY a valid JSON object. No explanation, no markdown."
)


RESUME_USER_PROMPT = """Extract the following from this resume and return as JSON:
{{
  "name": "full name",
  "email": "email address",
  "phone": "phone number",
  "linkedin": "LinkedIn URL if present, otherwise null",
  "github": "GitHub URL if present, otherwise null",
  "professional_summary": "the full text of the Summary, Profile, About Me, Objective, or Professional Summary section at the top of the resume. Copy the ENTIRE paragraph exactly as written. If no such section exists, return an empty string.",
  "skills": ["list", "of", "skills"],
  "skills_section_present": true,
  "experience": [
    {{
      "job_title": "",
      "company": "",
      "start_date": "",
      "end_date": "",
      "description": ""
    }}
  ],
  "education": [
    {{
      "degree": "",
      "institution": "",
      "year": ""
    }}
  ],
  "certifications": ["list of certifications"],
  "projects": [
    {{
      "title": "project name",
      "description": "what the project does and how it was built",
      "technologies": ["tech", "used"]
    }}
  ],
  "action_verbs": ["strong action verbs used in bullet points, e.g. developed, implemented, designed"],
  "keywords": ["important keywords and phrases from the resume for ATS matching"]
}}

Important instructions:
- Extract start_date and end_date exactly as stated in the resume.
- Do not calculate employment duration or infer missing dates.
- If a date is unavailable, return an empty string.
- Preserve values such as Present, Current, and date ranges accurately.
- For skills, extract ALL technical and soft skills mentioned anywhere in the resume.
- For action_verbs, find verbs that start bullet points or describe achievements.
- For keywords, extract noun phrases and technical terms relevant to ATS matching.
- Return ONLY valid JSON. No markdown code fences, no explanation.
- Set skills_section_present to true only when the resume contains a clearly identifiable dedicated Skills, Technical Skills, or Core Skills section with actual content under that heading. Do not set it to true merely because skills are mentioned in projects, experience, or other sections.

Resume Text:
{raw_text}"""


def _validate_resume_result(result: dict) -> dict:
    """Ensure the parsed resume contains the expected fields."""

    defaults = {
        "name": "",
        "email": None,
        "phone": None,
        "linkedin": None,
        "github": None,
        "professional_summary": "",
        "skills": [],
        "skills_section_present": False,
        "experience": [],
        "education": [],
        "certifications": [],
        "projects": [],
        "action_verbs": [],
        "keywords": [],
    }

    for key, default in defaults.items():
        if key not in result or result[key] is None:
            result[key] = default

        if isinstance(default, list) and not isinstance(result[key], list):
            result[key] = default

    # Validate experience entries.
    for exp in result.get("experience", []):
        if not isinstance(exp, dict):
            continue

        exp.setdefault("job_title", "")
        exp.setdefault("company", "")
        exp.setdefault("start_date", "")
        exp.setdefault("end_date", "")
        exp.setdefault("description", "")

    # Validate project entries.
    for proj in result.get("projects", []):
        if not isinstance(proj, dict):
            continue

        proj.setdefault("title", "")
        proj.setdefault("description", "")
        proj.setdefault("technologies", [])

        if not isinstance(proj["technologies"], list):
            proj["technologies"] = []

    return result


def parse_resume(raw_text: str) -> Dict:

    if not raw_text or not raw_text.strip():
        raise ValueError("Resume text cannot be empty.")

    client = _get_client()
    prompt = RESUME_USER_PROMPT.format(raw_text=raw_text)

    raw_response = _call_groq(
        client,
        RESUME_SYSTEM_PROMPT,
        prompt
    )

    result = _try_parse_json(raw_response)

    if isinstance(result, dict):
        return _validate_resume_result(result)

    logger.warning(
        "Groq resume parse: first attempt returned invalid JSON, retrying..."
    )

    strict_prompt = (
        "Your previous response was not valid JSON. "
        "Return ONLY the raw JSON object, no markdown, no explanation, no code fences.\n\n"
        + prompt
    )

    raw_response = _call_groq(
        client,
        RESUME_SYSTEM_PROMPT,
        strict_prompt
    )

    result = _try_parse_json(raw_response)

    if isinstance(result, dict):
        return _validate_resume_result(result)

    raise ValueError(
        f"Groq returned unparseable response after retry. "
        f"Raw response:\n{raw_response[:500]}"
    )


# ============================================================
# JOB DESCRIPTION PARSER
# ============================================================

JD_SYSTEM_PROMPT = (
    "You are a job description parser. Extract only requirements "
    "explicitly stated in the supplied job description. "
    "Return ONLY a valid JSON object. No markdown or explanation."
)


JD_USER_PROMPT = """Extract the following information from this job description:

{
  "job_title": "",
  "required_skills": [],
  "preferred_skills": [],
  "responsibilities": [],
  "experience_requirements": [],
  "minimum_experience_months": null,
  "maximum_experience_months": null,
  "experience_scope": "unspecified",
  "education_requirements": [],
  "education_level": "unspecified",
  "locations": []
}

Extraction rules:

1. Skills:
- Extract only explicitly stated skills.
- Keep mandatory and preferred skills separate.
- Do not invent skills from responsibilities.

2. Responsibilities:
- Extract explicitly stated job duties.
- Do not convert duties into assumed skills.

3. Experience:
- Preserve original experience requirements in experience_requirements.
- Extract minimum_experience_months as an integer when explicitly stated.
- Extract maximum_experience_months as an integer when explicitly stated.
- Convert years to months (1 year = 12 months).
- For "2+ years", minimum is 24 and maximum is null.
- For "1-3 years", minimum is 12 and maximum is 36.
- For "2-4 years", minimum is 24 and maximum is 48.
- If no numerical requirement is stated, use null for both.
- experience_scope must be:
  "relevant" only when specific relevant-role or skill experience is explicitly required.
  "overall" only when overall professional experience is explicitly required.
  "unspecified" when the scope is unclear.
- Never infer experience requirements.

4. Education:
- Preserve explicit education requirements.
- education_level must be one of:
  "high_school", "diploma", "bachelor", "master",
  "doctorate", "other", "unspecified".
- Use "unspecified" when no education level is explicitly required.

5. Location:
- Extract explicitly mentioned job locations into locations.
- Do not infer a location from company name or other context.

6. General:
- Return empty lists for categories with no information.
- Use null for unavailable numerical values.
- Never invent or assume requirements.
- Return ONLY valid JSON.

Job Description:
{job_description}"""



def _validate_job_description(text: str) -> None:
    """Validate that input contains meaningful job-related information."""

    if not isinstance(text, str):
        raise ValueError("Job description must be text.")

    cleaned = re.sub(r"\s+", " ", text).strip()

    if not cleaned:
        raise ValueError("Job description cannot be empty.")

    words = re.findall(
        r"\b[a-zA-Z][a-zA-Z+#.]*\b",
        cleaned
    )

    meaningful_words = [
        word for word in words
        if len(word) >= 2
    ]

    if len(meaningful_words) < 4:
        raise ValueError(
            "Please provide meaningful job-related information."
        )

    job_related_patterns = [
        # Job titles and professional roles
        r"\b(developer|engineer|analyst|designer|administrator|"
        r"consultant|manager|intern|tester|architect|specialist|"
        r"technician|scientist|recruiter|accountant|"
        r"programmer|executive)\b",

        # Employment level and experience
        r"\b(fresher|entry.level|junior|senior|internship|"
        r"experience|experienced|years?|months?)\b",

        # Skills and qualifications
        r"\b(skills?|proficient|proficiency|knowledge|ability|"
        r"qualification|degree|graduate|diploma|bachelor|master)\b",

        # Responsibilities and work activities
        r"\b(responsibilit(?:y|ies)|duties|develop|design|"
        r"manage|build|maintain|analy[sz]e|support|"
        r"implement|create|test|deploy)\b",
    ]

    has_job_related_content = any(
        re.search(pattern, cleaned, re.IGNORECASE)
        for pattern in job_related_patterns
    )

    if not has_job_related_content:
        raise ValueError(
            "Please include job-related information such as "
            "a job title, skills, experience, responsibilities, "
            "or qualifications."
        )


def _safe_months(value):
    """Accept only valid integer experience values between 0 and 600."""

    if isinstance(value, bool) or not isinstance(value, int):
        return None

    if value < 0 or value > 600:
        return None

    return value


def parse_job_description(job_description: str) -> Dict:

    if not isinstance(job_description, str) or not job_description.strip():
        raise ValueError("Job description cannot be empty.")

    _validate_job_description(job_description)

    client = _get_client()

    prompt = JD_USER_PROMPT.replace(
        "{job_description}",
        job_description.strip()
    )

    raw_response = _call_groq(
        client,
        JD_SYSTEM_PROMPT,
        prompt
    )

    result = _try_parse_json(raw_response)

    if not isinstance(result, dict):
        logger.warning(
            "Groq JD parse: invalid JSON on first attempt, retrying..."
        )

        strict_prompt = (
            "Return ONLY a valid raw JSON object. No markdown or explanation.\n\n"
            + prompt
        )

        raw_response = _call_groq(
            client,
            JD_SYSTEM_PROMPT,
            strict_prompt
        )

        result = _try_parse_json(raw_response)

    if not isinstance(result, dict):
        raise ValueError(
            "Groq could not extract valid job description data."
        )

    # Ensure all list fields have valid list values.
    list_fields = [
        "required_skills",
        "preferred_skills",
        "responsibilities",
        "experience_requirements",
        "education_requirements",
    ]

    for field in list_fields:
        value = result.get(field, [])

        if not isinstance(value, list):
            value = []

        result[field] = [
            item.strip()
            for item in value
            if isinstance(item, str) and item.strip()
        ]

    # Validate job title.
    result["job_title"] = str(
        result.get("job_title") or ""
    ).strip()

    # Validate numerical experience requirements.
    result["minimum_experience_months"] = _safe_months(
        result.get("minimum_experience_months")
    )

    result["maximum_experience_months"] = _safe_months(
        result.get("maximum_experience_months")
    )

    minimum = result["minimum_experience_months"]
    maximum = result["maximum_experience_months"]

    if minimum is not None and maximum is not None:
        if maximum < minimum:
            result["maximum_experience_months"] = None

    # Validate experience scope.
    valid_experience_scopes = {
        "relevant",
        "overall",
        "unspecified",
    }

    experience_scope = str(
        result.get("experience_scope") or "unspecified"
    ).strip().lower()

    result["experience_scope"] = (
        experience_scope
        if experience_scope in valid_experience_scopes
        else "unspecified"
    )

    # Validate education level.
    valid_education_levels = {
        "high_school",
        "diploma",
        "bachelor",
        "master",
        "doctorate",
        "other",
        "unspecified",
    }

    education_level = str(
        result.get("education_level") or "unspecified"
    ).strip().lower()

    result["education_level"] = (
        education_level
        if education_level in valid_education_levels
        else "unspecified"
    )

    # Validate job locations.
    locations = result.get("locations", [])

    if not isinstance(locations, list):
        locations = []

    result["locations"] = list(dict.fromkeys(
        item.strip()
        for item in locations
        if isinstance(item, str) and item.strip()
    ))

    return result

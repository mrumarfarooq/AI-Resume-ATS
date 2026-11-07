import json 
import logging
import re
import os
from typing import Dict


from groq import Groq

logger=logging.getLogger('ats_resume_scorer')


GROQ_MODEL='openai/gpt-oss-120b'

_client=None

def _get_client()->Groq:
    global _client
    if _client is None:
        api_key=os.getenv('GROQ_API_KEY')

        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        _client=Groq(api_key=api_key)
    return _client

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
  "experience": [
    {{
      "job_title": "",
      "company": "",
      "start_date": "",
      "end_date": "",
      "duration_months": 0,
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
- For duration_months, calculate the number of months between start_date and end_date. If end_date is "Present" or "Current", calculate from start_date to now.
- For skills, extract ALL technical and soft skills mentioned anywhere in the resume.
- For action_verbs, find verbs that start bullet points or describe achievements.
- For keywords, extract noun phrases and technical terms relevant to ATS matching.
- Return ONLY valid JSON. No markdown code fences, no explanation.

Resume Text:
{raw_text}"""

def _call_groq(client:Groq, system_prompt:str, user_prompt:str)->str:

    response=client.chat.completions.create(
        model=GROQ_MODEL, 
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ],
        temperature=0.0,
        max_tokens=4096
    )

    return response.choices[0].message.content.strip()

def _try_parse_json(text: str) -> dict | None:

    # Strip markdown code fences if present
    cleaned = text.strip()
    if cleaned.startswith("```"):

        # Remove opening fence (```json or ```)
        first_newline = cleaned.index("\n") if "\n" in cleaned else len(cleaned)
        cleaned = cleaned[first_newline + 1:]
        # Remove closing fence
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    
def parse_resume(raw_text: str)->Dict:

    client=_get_client()
    prompt=RESUME_USER_PROMPT.format(raw_text=raw_text)
    raw_response=_call_groq(client, RESUME_SYSTEM_PROMPT, prompt)
    result=_try_parse_json(raw_response)

    if result is not None:
        return _validate_resume_result(result)
    

    logger.warning("Groq resume parse: first attempt returned invalid JSON, retrying...")
    strict_prompt = (
        "Your previous response was not valid JSON. "
        "Return ONLY the raw JSON object, no markdown, no explanation, no code fences.\n\n"
        + prompt
    )
    raw_response = _call_groq(client, RESUME_SYSTEM_PROMPT, strict_prompt)
    result = _try_parse_json(raw_response)
    if result is not None:
        return _validate_resume_result(result)

    raise ValueError(
        f"Groq returned unparseable response after retry. Raw response:\n{raw_response[:500]}"
    )
    
#to make sure the parse json has all the valid json fields
def _validate_resume_result(result: dict) -> dict:

    defaults = {
        "name": "",
        "email": None,
        "phone": None,
        "linkedin": None,
        "github": None,
        "professional_summary": "",
        "skills": [],
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
            
        # Ensure list fields are actually lists
        if isinstance(default, list) and not isinstance(result[key], list):
            result[key] = default

    #Validate experience entries
    for exp in result.get("experience", []):
        if not isinstance(exp, dict):
            continue
        exp.setdefault("job_title", "")
        exp.setdefault("company", "")
        exp.setdefault("start_date", "")
        exp.setdefault("end_date", "")
        exp.setdefault("duration_months", 0)
        exp.setdefault("description", "")
        #Ensure duration_months is an int
        try:
            exp["duration_months"] = int(exp["duration_months"])
        except (ValueError, TypeError):
            exp["duration_months"] = 0

    #Validate project entries
    for proj in result.get("projects", []):
        if not isinstance(proj, dict):
            continue
        proj.setdefault("title", "")
        proj.setdefault("description", "")
        proj.setdefault("technologies", [])

    return result


JD_SYSTEM_PROMPT = (
    "You are a job description parser. Extract only requirements "
    "explicitly stated in the supplied job description. "
    "Return ONLY a valid JSON object. No markdown or explanation."
)

JD_USER_PROMPT = """Extract the following information from this job description:

{
  "job_title": "job title if mentioned, otherwise empty string",
  "required_skills": ["skills explicitly required or mandatory"],
  "preferred_skills": ["skills explicitly listed as preferred, desirable, or good to have"],
  "responsibilities": ["main job responsibilities"],
  "experience_requirements": ["explicit experience requirements"],
  "education_requirements": ["explicit education requirements"]
}

Rules:
- Do not invent or assume any skills or requirements.
- Keep required and preferred skills separate.
- Include technical and relevant soft skills when explicitly mentioned.
- Do not treat responsibilities as skills unless a specific skill is mentioned.
- If a category has no information, return an empty list.
- Return ONLY valid JSON.

Job Description:
{job_description}"""

def _validate_job_description(text: str) -> None:
    cleaned = re.sub(r"[*#%_\-+=|~`]", " ", text)
    words = re.findall(r"[a-zA-Z][a-zA-Z+#.]*", cleaned)

    if len(cleaned.strip()) < 100 or len(words) < 15:
        raise ValueError(
            "Please enter a genuine job description with meaningful text."
        )

    meaningful_words = [
        word for word in words
        if len(word) >= 2
    ]

    if len(meaningful_words) < 12:
        raise ValueError(
            "Job description contains insufficient meaningful text."
        )


def parse_job_description(job_description: str) -> Dict:
    if not job_description or not job_description.strip():
        raise ValueError("Job description cannot be empty.")

    _validate_job_description(job_description)

    client = _get_client()
    prompt = JD_USER_PROMPT.replace(
        "{job_description}", job_description.strip()
    )

    raw_response = _call_groq(client, JD_SYSTEM_PROMPT, prompt)
    result = _try_parse_json(raw_response)

    if result is None:
        logger.warning(
            "Groq JD parse: invalid JSON on first attempt, retrying..."
        )
        strict_prompt = (
            "Return ONLY a valid raw JSON object. No markdown or explanation.\n\n"
            + prompt
        )
        raw_response = _call_groq(
            client, JD_SYSTEM_PROMPT, strict_prompt
        )
        result = _try_parse_json(raw_response)

    if not isinstance(result, dict):
        raise ValueError(
            "Groq could not extract valid job description data."
        )

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
            str(item).strip()
            for item in value
            if isinstance(item, str) and item.strip()
        ]

    result["job_title"] = str(result.get("job_title") or "").strip()

    return result
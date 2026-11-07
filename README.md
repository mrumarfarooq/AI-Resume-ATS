# ResumeATS — AI Resume Analyzer

ResumeATS is a resume-review application built with **Streamlit**, **FastAPI**, **spaCy**, **Sentence Transformers**, **Groq**, and **Supabase**.

It provides two independent assessments:

1. **General ATS Score** — a project-defined estimate of resume structure, content, skill evidence, and parseability.
2. **Job Role Match** — a separate comparison against a curated baseline profile for one of eight job roles.

> Scores are guidance signals, not official ATS rankings or predictions of interviews or hiring outcomes. A role profile is a broad baseline, not a specific employer's job description.

## Product features

- Modern white, navy, and blue SaaS interface.
- Centered Sign In / Create Account experience.
- Supabase email/password authentication and optional Google OAuth.
- PDF/DOC/DOCX resume upload.
- General ATS score with component breakdown.
- Eight curated job-role profiles plus a custom role field.
- Explicit matched/missing skill lists and project/experience evidence.
- Downloadable multi-section PDF report and Markdown analysis summary.
- Account-scoped analysis history and resources page.

## Curated job roles

- Python Developer
- Python Full Stack Developer
- Backend Developer
- Data Analyst
- Data Scientist
- Machine Learning Engineer
- SQL Developer
- DevOps Engineer
- Other (custom role)

A custom role is accepted and shown in the report, but a numeric role score is intentionally withheld unless a curated skill profile exists. The app does not invent job requirements from a short title.

## Role-match scoring

For curated roles, the separate role score uses:

- 70% required-skill coverage
- 20% explicit mentions of matched skills in project/experience descriptions
- 10% preferred-skill coverage

The report displays the profile requirements, matches, gaps, and evidence. A match means a term was detected; it does not prove proficiency. Review the evidence and only claim skills you can demonstrate.

## General ATS scoring

The General ATS score remains independent of the selected job role. Its components are:

| Component | Maximum |
|---|---:|
| Formatting and section structure | 20 |
| Keywords and listed skills | 25 |
| Content quality and measurable outcomes | 25 |
| Skills supported by project/experience text | 15 |
| ATS compatibility heuristics | 15 |
| **Total** | **100** |

The scoring logic is heuristic and should be interpreted as a resume-quality checklist, not as a universal ATS formula. Grammar and location checks are currently not configured; the analyzer does not award a grammar bonus or apply a location penalty when those checks are unavailable. Skill validation now requires an explicit text mention in project/experience evidence rather than semantic similarity alone.

## Project structure

```text
ai-resume-ats/
├── backend/
│   ├── api/
│   ├── core/
│   ├── database/
│   ├── models/
│   ├── services/
│   │   ├── role_profiles.py
│   │   └── role_matcher.py
│   ├── templates/
│   └── utils/
├── frontend/
│   ├── assets/
│   ├── components/
│   ├── services/
│   ├── views/
│   └── streamlit_app.py
├── requirements.txt
└── README.md
```

## Setup

Use Python 3.11 or 3.12 for the most predictable compatibility with the NLP dependencies.

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_md
```

If CPU-only PyTorch installation is required, install the CPU wheel before the project requirements:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in the project root. Do not commit it.

```env
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY
SUPABASE_KEY=YOUR_SERVER_SIDE_SUPABASE_KEY
SUPABASE_JWT_SECRET=YOUR_JWT_SECRET
GROQ_API_KEY=YOUR_GROQ_API_KEY
AUTH_REDIRECT_URL=http://localhost:8501
```

`SUPABASE_KEY` is used by the backend for database operations and must remain server-side. Never expose it in frontend code, browser JavaScript, screenshots, or GitHub.

### 3. Configure Supabase authentication

In Supabase Authentication settings:

- Set the Site URL to your deployed Streamlit URL (or `http://localhost:8501` for local development).
- Add the same URL to the allowed Redirect URLs.
- Keep email confirmation enabled if you want users to prove they own the email address.
- Configure a working SMTP provider if confirmation emails are not being delivered.
- For Google OAuth, configure the provider credentials and allowed callback URLs in Supabase.

The app sends the configured `AUTH_REDIRECT_URL` as the email confirmation redirect. For production, set this variable to the exact deployed frontend URL. Disabling email confirmation removes proof of email ownership and is not recommended for a public account system.

### 4. Configure database table

The backend expects an `analyses` table with at least these columns:

- `id` — UUID primary key
- `user_id` — UUID
- `filename` — text
- `ats_score` — numeric
- `keyword_match` — numeric
- `missing_keywords` — jsonb
- `created_at` — timestamptz
- `analysis_result` — jsonb

Restrict reads/deletes to the owning user. The backend uses its server-side Supabase key; keep it secret and validate the authenticated user ID before database operations.

### 5. Start the backend

From the project root:

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

The backend loads the spaCy and Sentence Transformer models at startup. The first startup may take time while model files are loaded.

### 6. Start the frontend

In a second terminal, activate the same virtual environment and run:

```bash
streamlit run frontend/streamlit_app.py
```

Open `http://localhost:8501`.

## PDF export

PDF generation uses WeasyPrint. On Ubuntu/WSL, install its system dependencies if needed:

```bash
sudo apt update
sudo apt install -y libcairo2 libpango-1.0-0 libpangoft2-1.0-0 libffi-dev
```

## Important limitations

- The app is a resume review assistant, not an employer ATS simulator.
- Curated role profiles represent general skill expectations and may not match every vacancy.
- Custom role titles do not receive a numeric role score without a curated profile.
- Resume extraction and structured parsing can make mistakes; verify the detected information.
- Grammar and location privacy detection are not configured in the current pipeline.
- Do not add missing skills to a resume unless you genuinely have them.

## GitHub safety checklist

Before pushing:

- Keep `.env`, Supabase service keys, JWT secrets, and Groq keys out of Git.
- Keep `.venv`, `__pycache__`, model caches, and personal resume files out of Git.
- Rotate any credential that was previously committed or shared publicly.

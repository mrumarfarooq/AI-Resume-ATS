import re
from typing import List, Dict, Optional
from backend.models.schemas import IssueDetail

def analyze_issues(
        resume_text: str,
        parsed_resume: Dict,
        skills: List[str],
        projects: List[Dict],
        action_verbs: List[str],
        skill_validation: Dict,
        scores: Dict,
        contact_info: Optional[Dict]=None,
) -> List[IssueDetail]:

    detected: List[IssueDetail]=[]

    #Unpack frequently-used structured fields once at the top

    exp_entries  = [e for e in parsed_resume.get('experience', []) if isinstance(e, dict)]
    edu_entries  = [e for e in parsed_resume.get('education',  []) if isinstance(e, dict)]
    proj_entries = [p for p in parsed_resume.get('projects',   []) if isinstance(p, dict)]
    summary      = (parsed_resume.get('professional_summary') or '').strip()  # Handle None to prevent string concatenation errors

    #Build a combined experience text for regex-based checks that still need text
    experience_text = '\n'.join(e.get('description', '') for e in exp_entries).strip()


    #1. missig project section
    resume_lower = resume_text.lower()
    has_projects_signal = any(kw in resume_lower for kw in [
        'project', 'github.com', 'deployed', 'built a', 'developed a',
        'created a', 'implemented a', 'live demo', 'tech stack',
    ])

    if not proj_entries and len(projects) == 0 and not has_projects_signal:
        detected.append(IssueDetail(
            issue_title="Missing Projects Section",
            severity_level="High",
            ats_impact="High",
            explanation=(
                "Your resume does not have a dedicated Projects section. "
                "ATS systems and recruiters look for concrete projects to validate "
                "that your listed skills have been applied in practice."
            ),

            where_it_appears="Resume structure — no 'Projects' header was detected",

            how_to_fix=(
                "Add a 'Projects' section with 2–3 significant projects. "
                "For each project, include the title, technologies used, "
                "what you built, and a measurable outcome."
            ),

            action_items=[
                "Add a 'PROJECTS' section heading after your Experience section",
                "Include 2–3 projects (personal, academic, or open-source)",
                "For each project: write the title, tech stack used, what you built, and a measurable result",
                "Example: '[Actual Project Name] — [Technologies genuinely used]. "
                "Describe the features you implemented and your actual contribution.'",
                "Link to GitHub or a live demo if available (e.g., github.com/yourname/project)",
            ],

            example_improvement=(
                "Suggested structure:\n"
                "PROJECTS\n"
                "[Actual Project Name] — [Briefly describe what you built] "
                "using [technologies actually used].\n"
                "• Implemented [actual feature or functionality].\n"
                "• Describe your actual contribution and any verified outcome.\n\n"
                "Add only projects you have genuinely built. Do not invent "
                "technologies, features, users, or performance metrics."
            ),
        ))

    #2. missing experience section
    has_experience_signal = any(kw in resume_lower for kw in [
        'intern', 'internship', 'employed', 'worked at', 'working at',
        'company', 'organization', 'job', 'role', 'position', 'designation',
        'manager', 'engineer', 'developer', 'analyst', 'consultant',
    ])

    if not exp_entries and not has_experience_signal:
        detected.append(IssueDetail(
            issue_title="Missing Work Experience Section",
            severity_level="High",
            ats_impact="High",
            explanation=(
                "No work experience section was detected. Even for freshers, "
                "internships, freelance work, or volunteer experience help "
                "demonstrate professional capability."
            ),
            where_it_appears="Resume structure — no 'Experience' or 'Work History' header found",
            how_to_fix=(
                "Add an 'Experience' section. If you lack formal employment, "
                "include internships, freelance projects, open-source contributions, "
                "or relevant volunteer work."
            ),
            action_items=[
                "Add an 'EXPERIENCE' or 'INTERNSHIPS' section to your resume",
                "List each role with: Job Title — Company Name (Month Year – Month Year)",
                "Add 2–4 bullet points per role describing what you did and its impact",
                "If no formal job: include internships, freelance work, open-source, or college clubs",
                "Start every bullet with a past-tense action verb (Developed, Built, Led, etc.)",
            ],
            example_improvement=(
                "Suggested structure:\n"
                "EXPERIENCE\n"
                "[Actual Job Title] — [Actual Company or Organization]\n"
                "[Actual Start Date] – [Actual End Date or Present]\n"
                "• Describe a responsibility you genuinely handled using "
                "[actual technology or skill].\n"
                "• Explain a task you completed and its actual outcome.\n\n"
                "If you are a fresher without formal work experience, do not "
                "invent employment. Highlight genuine internships, training, "
                "academic work, or projects in their appropriate sections."
            ),
        ))

    #3. Missing Education Section
    has_education_signal = any(kw in resume_lower for kw in [
        'b.tech', 'btech', 'b.e.', 'b.sc', 'bsc', 'm.tech', 'mtech', 'm.sc',
        'bachelor', 'master', 'phd', 'university', 'college',
        'institute of technology', 'cgpa', 'gpa', 'graduated', 'diploma',
        'class of', '20', 'batch of',
    ])
    if not edu_entries and not has_education_signal:
        detected.append(IssueDetail(
            issue_title="Missing Education Section",
            severity_level="Moderate",
            ats_impact="Medium",
            explanation=(
                "No education section was found. Most ATS systems expect an "
                "Education section with at least your degree and institution."
            ),
            where_it_appears="Resume structure — no 'Education' header detected",
            how_to_fix=(
                "Add an 'Education' section listing your degree, university, "
                "graduation year, and optionally your GPA or relevant coursework."
            ),
            action_items=[
                "Add an 'EDUCATION' section (usually at the bottom for experienced candidates, top for freshers)",
                "Include: Degree name — Institution name (Start Year – End Year)",
                "Add your CGPA or percentage if it is 7.0+ or 70%+",
                "Optionally list 3–5 relevant courses (e.g., Data Structures, DBMS, ML)",
            ],
            example_improvement=(
                "Suggested structure:\n"
                "EDUCATION\n"
                "[Actual Degree or Diploma]\n"
                "[Actual College or Institution]\n"
                "[Actual Graduation Year]\n"
                "CGPA / Percentage: [Actual Score, if applicable]\n\n"
                "Use your real educational qualifications, institution, "
                "graduation year, and verified academic score."
            ),
        ))

    #4. Missing Skills Section
    if not parsed_resume.get('skills') and len(skills) < 3:  # only flag if extraction also found very few skills
        detected.append(IssueDetail(
            issue_title="Missing or Weak Skills Section",
            severity_level="High",
            ats_impact="High",
            explanation=(
                f"Only {len(skills)} skill(s) were detected. ATS systems "
                "rely heavily on keyword matching from a dedicated Skills section. "
                "Without clear skills listed, your resume may fail automated filters."
            ),
            where_it_appears="Skills section — either missing or contains very few items",
            how_to_fix=(
                "Add a clear 'Skills' section organized by category. "
                "Include programming languages, frameworks, tools, and soft skills "
                "that match your target role."
            ),
            action_items=[
                "Add a 'TECHNICAL SKILLS' or 'SKILLS' section",
                "Organize by category: Languages, Frameworks, Tools, Databases, Cloud",
                "List at least 10–15 skills relevant to your target role",
                "Use the exact names that appear in job descriptions (e.g., 'React.js' not just 'React')",
                "Include tools you use daily: Git, VS Code, Postman, Docker, etc.",
            ],
            example_improvement=(
                "Suggested structure:\n"
                "TECHNICAL SKILLS\n"
                "Programming Languages: [Languages you genuinely know]\n"
                "Frameworks: [Frameworks you have actually used]\n"
                "Databases: [Databases you have actually worked with]\n"
                "Tools: [Tools you have genuinely used]\n\n"
                "Include only skills you can explain and demonstrate in an "
                "interview. Do not add technologies just because they appear "
                "in a job description."
            ),
        ))

    # 5. Skills Lack Supporting Evidence
    unvalidated = skill_validation.get('unvalidated_skills', [])
    validated   = skill_validation.get('validated_skills', [])
    total_skills = len(unvalidated) + len(validated)

    if unvalidated:
        unsupported_list = ', '.join(unvalidated[:8])
        pct_unsupported = round((len(unvalidated) / total_skills) * 100)
        action_items_skills = [
            f"Mention '{skill}' in a project or experience bullet point" for skill in unvalidated[:5]
        ]
        action_items_skills.append("Remove skills you cannot demonstrate with any project or experience")

        detected.append(IssueDetail(
            issue_title=(
                "Most Skills Lack Supporting Evidence"
                if len(unvalidated) > len(validated)
                else "Some Skills Lack Supporting Evidence"
            ),
            severity_level="Moderate",
            ats_impact="High",
            explanation=(
                f"{pct_unsupported}% of your listed skills ({len(unvalidated)} out of "
                f"{total_skills}) are not backed by any mention in your projects or "
                "experience sections. Recruiters and ATS systems cross-reference "
                "skills against actual work to verify credibility."
            ),
            where_it_appears=f"These skills have no supporting context: {unsupported_list}",
            how_to_fix=(
                "For each skill in your Skills section, ensure it appears at least "
                "once in a project description or experience bullet point. "
                "Describe how and where you used that technology."
            ),
            action_items=action_items_skills,
            example_improvement=(
                f"Your skill '{unvalidated[0]}' has no supporting evidence.\n\n"
                f"Suggested improvement: If you have genuinely used "
                f"{unvalidated[0]}, describe the specific project, task, "
                "or experience where you applied it.\n"
                "Explain what you implemented and what your actual contribution was.\n\n"
                "Do not invent project details, responsibilities, or performance metrics."
            ),
        ))

    #6. Weak Action Verbs
    description_lines = [
        line.strip()
        for exp in exp_entries
        for line in exp.get('description', '').split('\n')
        if line.strip()
    ]

    if len(description_lines) > 3 and len(action_verbs) < 3:
        detected.append(IssueDetail(
            issue_title="Bullet Points Lack Strong Action Verbs",
            severity_level="Moderate",
            ats_impact="Medium",
            explanation=(
                f"Your experience section has {len(description_lines)} bullet points but "
                f"only {len(action_verbs)} start with strong action verbs. "
                "ATS systems and recruiters favor bullets that begin with verbs like "
                "'Developed', 'Implemented', 'Designed', 'Optimized'."
            ),
            where_it_appears="Experience section — bullet point openings",
            how_to_fix=(
                "Start every bullet point with a past-tense action verb. "
                "Avoid starting with 'Responsible for', 'Worked on', or 'Helped with'. "
                "Use verbs like: Developed, Built, Designed, Implemented, Led, Automated, Optimized."
            ),
            action_items=[
                "Rewrite every bullet that starts with 'Responsible for', 'Helped', 'Worked on', or 'Assisted'",
                "Use: Developed, Built, Designed, Implemented, Led, Automated, Optimized, Deployed, Reduced, Increased",
                "Make verbs past-tense for previous roles, present-tense for current role",
                f"Review all {len(description_lines)} bullet points — at least {len(description_lines)} should start with action verbs",
                "Avoid weak openers like 'Was responsible for...' or 'Involved in...'",
            ],
            example_improvement=(
                "Before — Generic bullet points:\n"
                "• Responsible for building the backend\n"
                "• Worked on the payment feature\n\n"
                "After — More specific and evidence-based:\n"
                "• Developed backend functionality using [actual technology used]\n"
                "• Implemented [actual feature] to support [specific application functionality]\n\n"
                "Replace the placeholders with technologies and features you "
                "actually used. Add measurable results only when they can be verified."
            ),
        ))

    #7. No Quantifiable Achievements
    number_pattern = r'\d+[%+]?|\$\d+'
    has_metrics = bool(re.findall(number_pattern, experience_text)) if experience_text else False

    if experience_text and not has_metrics:
        detected.append(IssueDetail(
            issue_title="No Quantifiable Achievements Found",
            severity_level="Moderate",
            ats_impact="Medium",
            explanation=(
                "Your experience section does not contain any measurable outcomes "
                "(numbers, percentages, or dollar amounts). Quantified achievements "
                "make your impact concrete and are strongly preferred by recruiters."
            ),
            where_it_appears="Experience section — bullet point content",
            how_to_fix=(
                "Add numbers to at least 50% of your bullet points. "
                "Include metrics like: users served, response time improved, "
                "revenue generated, lines of code, team size, etc."
            ),
            action_items=[
                "Go through each bullet point and ask: 'How much?', 'How many?', 'By what %?'",
                "Add metrics: users served, requests/day, % improvement, team size, time saved",
                "Use only verified figures from actual project records, logs, reports, or documented results.",
                "If exact numbers are unavailable, do not invent or guess metrics. Describe the actual impact qualitatively using truthful, verifiable details.",
                "Quantify relevant experience bullets wherever reliable, verifiable metrics are available.",
            ],
            example_improvement=(
                "BEFORE — Generic resume bullets:\n"
                "• Worked on improving application performance.\n"
                "• Responsible for database operations.\n"
                "• Worked with a team to develop application features.\n\n"
                "AFTER — More specific and evidence-based:\n"
                "• Improved [actual application functionality] using "
                "[technology genuinely used].\n"
                "• Implemented [actual database task] to support "
                "[specific application requirement].\n"
                "• Developed [actual feature] as part of [actual project or role].\n\n"
                "Include measurable results only when you have reliable evidence. "
                "If metrics are unavailable, describe your actual contribution "
                "without inventing numbers."
            ),
        ))

    #8. Missing Contact Information
    if contact_info:
        missing_contacts = []
        if not contact_info.get('email'):
            missing_contacts.append('email')
        if not contact_info.get('phone'):
            missing_contacts.append('phone number')
        if not contact_info.get('linkedin'):
            missing_contacts.append('LinkedIn URL')

        if len(missing_contacts) >= 2:
            contact_action_items = [f"Add your {item} to the header section" for item in missing_contacts]
            contact_action_items += [
                "Format the contact line as: email | phone | linkedin | github",
                "Make sure your LinkedIn URL is a custom short URL (linkedin.com/in/yourname)",
                "Add a GitHub link if you have public projects (github.com/yourname)",
            ]
            detected.append(IssueDetail(
                issue_title="Incomplete Contact Information",
                severity_level="High",
                ats_impact="High",
                explanation=(
                    f"Your resume is missing: {', '.join(missing_contacts)}. "
                    "Recruiters need reliable ways to reach you. Missing contact "
                    "details can cause your application to be skipped entirely."
                ),
                where_it_appears="Header / Contact section at the top of the resume",
                how_to_fix=(
                    "Add your full name, email, phone number, LinkedIn profile, "
                    "and optionally a GitHub or portfolio link at the top of your resume."
                ),
                action_items=contact_action_items,
                example_improvement=(
                    "Suggested contact section:\n"
                    "[Your Full Name]\n"
                    "[Your Professional Email] | [Your Phone Number]\n"
                    "[Your LinkedIn Profile URL]\n"
                    "[Your GitHub or Portfolio URL, if available]\n\n"
                    "Use your own valid contact details. Include only links "
                    "and information that belong to you."
                ),
            ))

    # 9. Low Formatting Score
    formatting_score = scores.get('formatting_score', 20)
    if formatting_score < 10:
        detected.append(IssueDetail(
            issue_title="Poor Resume Formatting",
            severity_level="High",
            ats_impact="High",
            explanation=(
                f"Your formatting score is {formatting_score}/20, which indicates "
                "problems like missing section headers, inconsistent structure, "
                "or non-standard layout that ATS parsers struggle with."
            ),
            where_it_appears="Overall document structure and formatting",
            how_to_fix=(
                "Use a clean, single-column layout with standard section headers "
                "(Experience, Education, Skills, Projects). Use consistent bullet "
                "points, standard fonts, and avoid tables, columns, or graphics."
            ),
            action_items=[
                "Switch to a single-column layout (avoid two-column templates for ATS)",
                "Use standard section headers: EXPERIENCE, EDUCATION, SKILLS, PROJECTS",
                "Use bullet points (•) consistently — don't mix with dashes or asterisks",
                "Remove all tables, text boxes, headers/footers, and images — ATS cannot parse them",
                "Use a standard font (Calibri, Arial, Times New Roman) at 10–12pt",
                "Order sections: Contact → Summary → Experience → Projects → Education → Skills",
            ],
            example_improvement=(
                "Use this structure:\n"
                "NAME & CONTACT\n"
                "SUMMARY (2-3 lines)\n"
                "EXPERIENCE (reverse chronological)\n"
                "PROJECTS (2-3 key projects)\n"
                "EDUCATION\n"
                "SKILLS (categorized)"
            ),
        ))

    #10. Missing Summary/Objective
    if not summary:
        detected.append(IssueDetail(
            issue_title="Missing Professional Summary",
            severity_level="Low",
            ats_impact="Low",
            explanation=(
                "Your resume does not include a Professional Summary or Objective "
                "section at the top. While not required, a 2-3 line summary helps "
                "recruiters quickly understand your profile and target role."
            ),
            where_it_appears="Top of resume — below contact info",
            how_to_fix=(
                "Add a 2-3 sentence summary highlighting your experience level, "
                "key skills, and career focus. Tailor it to the job you're applying for."
            ),
            action_items=[
                "Add a 'PROFESSIONAL SUMMARY' or 'OBJECTIVE' section at the top of your resume",
                "Write 2–3 sentences: who you are, your key skills, and what role you seek",
                "Mention your years of experience or education level upfront",
                "Tailor this section for each job application — reference the specific role",
                "Keep it under 60 words — recruiters spend only 6 seconds on first scan",
            ],
            example_improvement=(
                "Suggested structure:\n"
                "PROFESSIONAL SUMMARY\n"
                "[Your actual education or experience level] with knowledge of "
                "[your verified technical skills]. Built [actual project or "
                "application] using [technologies genuinely used]. "
                "Seeking opportunities in [your target role].\n\n"
                "Replace every placeholder with your actual details. "
                "Do not claim experience, skills, or achievements you cannot verify."
            ),
        ))

    return detected


def generate_issues_summary(detected_issues: List[IssueDetail]) -> List[str]:
    """Extract issue titles to formulate the issues_summary list."""
    return [issue.issue_title for issue in detected_issues]

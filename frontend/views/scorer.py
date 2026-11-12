from datetime import datetime
import re

import markdown
from weasyprint import HTML

import requests
import streamlit as st

from frontend.services import api_client
from frontend.components.dashboard import display_results_dashboard

JOB_ROLES = [
    "Python Developer",
    "Python Full Stack Developer",
    "Backend Developer",
    "Data Analyst",
    "Data Scientist",
    "Machine Learning Engineer",
    "SQL Developer",
    "DevOps Engineer",
]


def _show_backend_error(exc: Exception) -> None:
    if isinstance(exc, requests.ConnectionError):
        st.error("Could not reach the analysis server. Check that the backend is running.")
    elif isinstance(exc, requests.Timeout):
        st.error("The analysis took too long. Please retry with a smaller resume.")
    elif isinstance(exc, requests.HTTPError) and exc.response is not None:
        try:
            detail = exc.response.json().get("detail", exc.response.text)
        except ValueError:
            detail = exc.response.text
        st.error(f"Analysis server returned {exc.response.status_code}: {detail}")
    else:
        st.error(f"Unexpected error: {exc}")


def _summary_text(analysis: dict) -> str:
    """Create a readable, evidence-led Markdown summary for download."""
    score = float(analysis.get("ATS_score", analysis.get("ats_score", 0)) or 0)
    role = analysis.get("job_role") or "Not selected"
    role_data = analysis.get("role_match_analysis") or {}
    jd_data = analysis.get("job_description_match_analysis") or {}
    lines = [
        "# Resume Analysis Summary",
        f"Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}",
        "",
        "## Overall ATS assessment",
        f"**ATS score: {score:.1f}/100**",
        analysis.get("interpretation", "This score is a heuristic resume-quality estimate, not a hiring prediction."),
        "",
    ]
    components = analysis.get("component_scores") or {}
    if components:
        lines.extend(["## Score breakdown"])
        for label, key, maximum in [
            ("Formatting", "formatting", 20),
            ("Keywords and skills", "keywords", 25),
            ("Content quality", "content", 25),
            ("Skill validation", "skill_validation", 15),
            ("ATS compatibility", "ats_compatibility", 15),
        ]:
            lines.append(f"- {label}: {components.get(key, 0)}/{maximum}")
        lines.append("")

    lines.extend(["## Job Role Match", f"**Selected role:** {role}"])
    if role_data.get("score_available"):
        lines.append(f"**Role match score: {role_data.get('match_score', 0):.1f}%**")
        lines.append("")
        lines.append("### Matched required skills")
        lines.extend([f"- {x}" for x in role_data.get("matched_skills", [])] or ["- No required skills matched."])
        lines.append("")
        lines.append("### Missing required skills")
        lines.extend([f"- {x}" for x in role_data.get("missing_skills", [])] or ["- No missing required skills in this profile."])
        lines.append("")
        lines.append("### Skills supported by project or experience text")
        lines.extend([f"- {x}" for x in role_data.get("evidence_backed_skills", [])] or ["- No direct project/experience evidence detected."])
        lines.append("")
        lines.append("### Relevant projects")
        lines.extend([f"- {x}" for x in role_data.get("relevant_projects", [])] or ["- No relevant project entry detected."])
        lines.append("")
        lines.append("### Relevant experience")
        lines.extend([f"- {x}" for x in role_data.get("relevant_experience", [])] or ["- No relevant experience entry detected."])
        lines.append("")
        lines.append(f"_Scoring method: {role_data.get('score_method', '')}_")
    elif role_data:
        lines.extend(["", role_data.get("message", "A curated profile is not available for this custom role.")])
    elif not jd_data:
        lines.extend(["", "No job role was selected."])


    if jd_data:
        lines.extend([
            "",
            "## Job Description Match",
            f"**Target position:** {jd_data.get('job_title') or 'Provided job description'}",
            "",
        ])

        if jd_data.get("score_available"):
            lines.append(
                f"**JD match score: {jd_data.get('match_score', 0):.1f}%**"
            )
            lines.append("")

        else:
            lines.append(
                jd_data.get(
                    "message",
                    "A reliable match score could not be calculated."
                )
            )
            lines.append("")

        lines.append("### Matched required skills")
        lines.extend([
            f"- {x}" for x in jd_data.get("matched_skills", [])
        ] or ["- No required skills matched."])

        lines.extend(["", "### Missing required skills"])
        lines.extend([
            f"- {x}" for x in jd_data.get("missing_skills", [])
        ] or ["- No missing required skills detected."])

        lines.extend(["", "### Preferred skills matched"])
        lines.extend([
            f"- {x}" for x in jd_data.get("preferred_matches", [])
        ] or ["- No preferred skills matched."])

        lines.extend(["", "### Skills supported by project or experience"])
        lines.extend([
            f"- {x}" for x in jd_data.get("evidence_backed_skills", [])
        ] or ["- No direct evidence detected."])

        lines.extend(["", "### Relevant projects"])
        lines.extend([
            f"- {x}" for x in jd_data.get("relevant_projects", [])
        ] or ["- No relevant project detected."])

        lines.extend(["", "### Relevant experience"])
        lines.extend([
            f"- {x}" for x in jd_data.get("relevant_experience", [])
        ] or ["- No relevant experience detected."])

        if jd_data.get("score_method"):
            lines.extend([
                "",
                f"_Scoring method: {jd_data.get('score_method')}_"
            ])

    lines.extend(["", "## Strengths"])
    lines.extend([f"- {x}" for x in analysis.get("strengths", [])] or ["- No specific strengths were returned."])
    lines.extend(["", "## Priority improvements"])
    issues = analysis.get("issues_summary") or analysis.get("critical_issues") or []
    lines.extend([f"- {x}" for x in issues] or ["- Review the detailed report for improvement opportunities."])
    lines.extend(["", "## Recommendations"])
    lines.extend([f"- {x}" for x in analysis.get("suggestions", [])] or ["- Add specific, measurable outcomes to relevant project and experience bullets."])
    lines.extend(["", "---", "_This report is an automated resume review aid. It does not predict interview or hiring outcomes. Only claim skills you can demonstrate._"])
    return "\n".join(lines)

def _summary_pdf(analysis: dict) -> bytes:
    """Convert the existing Markdown summary into a PDF."""
    summary_md = _summary_text(analysis)

    summary_html = markdown.markdown(
        summary_md,
        extensions=["extra"],
    )

    html_document = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4;
                margin: 22mm;
            }}
            body {{
                font-family: Arial, sans-serif;
                color: #1e293b;
                font-size: 11pt;
                line-height: 1.6;
            }}
            h1, h2, h3 {{
                color: #0f1c2e;
            }}
            h1 {{
                font-size: 24pt;
                border-bottom: 2px solid #2563eb;
                padding-bottom: 10px;
            }}
            h2 {{
                font-size: 16pt;
                margin-top: 22px;
            }}
            li {{
                margin-bottom: 5px;
            }}
        </style>
    </head>
    <body>
        {summary_html}
    </body>
    </html>
    """

    return HTML(string=html_document).write_pdf()

def _render_role_selector() -> str:
    st.markdown("#### Select a target job role")
    st.caption("Choose one of the curated role profiles. The role score is separate from your General ATS score.")
    selected = st.session_state.get("selected_job_role", JOB_ROLES[0])
    for start in (0, 4):
        cols = st.columns(4)
        for col, role in zip(cols, JOB_ROLES[start:start + 4]):
            with col:
                if st.button(
                    role,
                    key=f"role_{role}",
                    type="primary" if selected == role else "secondary",
                    use_container_width=True,
                ):
                    st.session_state.selected_job_role = role
                    st.rerun()
    other_selected = selected == "Other"
    if st.button(
        "Other — enter a custom role",
        key="role_other",
        type="primary" if other_selected else "secondary",
        use_container_width=True,
    ):
        st.session_state.selected_job_role = "Other"
        st.rerun()

    if st.session_state.get("selected_job_role") == "Other":
        return st.text_input(
            "Your custom job role",
            key="custom_job_role",
            placeholder="e.g. Cloud Support Associate",
        ).strip()
    return st.session_state.get("selected_job_role", JOB_ROLES[0])


def _render_export_buttons(analysis: dict) -> None:
    st.markdown("### Export your results")
    c1, c2 = st.columns(2)
    token = st.session_state["access_token"]
    with c1:
        if st.button("Generate PDF report", use_container_width=True, type="primary"):
            try:
                with st.spinner("Preparing your PDF report..."):
                    st.session_state["scorer_pdf_bytes"] = api_client.generate_pdf(
                        analysis, access_token=token
                    )
            except requests.RequestException as exc:
                _show_backend_error(exc)
        if st.session_state.get("scorer_pdf_bytes"):
            st.download_button(
                "Download PDF report",
                data=st.session_state["scorer_pdf_bytes"],
                file_name="resume_analysis_report.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="download_pdf_report",
            )
    with c2:
        
        st.download_button(
            "Download analysis summary",
            data=_summary_pdf(analysis),
            file_name="resume_analysis_summary.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="download_summary",
        )


def render() -> None:
    st.markdown(
        '<div class="page-heading"><div class="page-eyebrow">RESUME INTELLIGENCE</div>'
        '<h1>Resume Analyzer</h1><p>Review resume quality and, optionally, compare it with a target role.</p></div>',
        unsafe_allow_html=True,
    )


    with st.container(border=True):
        st.markdown("#### Upload your resume")
        resume_file = st.file_uploader(
            "Choose a PDF or DOCX file",
            type=["pdf", "doc", "docx"],
            help="Maximum file size: 5 MB",
            key="resume_upload",
            label_visibility="collapsed",
        )
        if resume_file:
            st.success(
                f"Resume ready: {resume_file.name} · {resume_file.size / 1024:.0f} KB"
            )

    mode = st.radio(
        "Analysis type",
        ["General ATS Score", "Job Matching"],
        horizontal=True,
        key="analysis_mode",
    )

    job_role = ""
    job_description = ""
    job_matching_type = ""

    if mode == "Job Matching":
        job_matching_type = st.radio(
            "Match against",
            ["Job Role", "Job Description"],
            horizontal=True,
            key="job_matching_type",
        )

        if job_matching_type == "Job Role":
            with st.container(border=True):
                job_role = _render_role_selector()

                if st.session_state.get("selected_job_role") == "Other":
                    if not job_role:
                        st.caption("Enter the custom role name to continue.")
                    else:
                        st.info(
                            "Custom role names are accepted. A numeric "
                            "match score is only shown when a curated "
                            "requirements profile exists; we will not "
                            "invent skills from a title."
                        )

        elif job_matching_type == "Job Description":
            with st.container(border=True):
                st.markdown("#### Paste the job description")
                job_description = st.text_area(
                    "Job description",
                    height=220,
                    max_chars=12000,
                    placeholder=(
                        "Paste the complete job description here, "
                        "including required skills, responsibilities "
                        "and experience..."
                    ),
                    key="job_description_input",
                    label_visibility="collapsed",
                )
                st.caption(
                    "Paste the actual job description, not just a list "
                    "of keywords."
                )

    token = st.session_state.get("access_token")
    if not token:
        st.warning("Sign in to analyze a resume.")
        return

    if st.button("Analyze resume", type="primary", use_container_width=True, key="run_resume_analysis"):
        if not resume_file:
            st.warning("Upload your resume before starting the analysis.")
            return
        if mode == "Job Matching" and job_matching_type == "Job Role" and not job_role:
            st.warning("Select a role or enter your custom job role.")
            return
        if (
            mode == "Job Matching"
            and job_matching_type == "Job Description"
            and not job_description.strip()
        ):
            st.warning("Paste a job description before starting the analysis.")
            return


        st.session_state.pop("scorer_pdf_bytes", None)
        st.session_state.pop("scorer_analysis", None)
        try:
            with st.spinner("Analyzing your resume. This may take 10–30 seconds..."):
                analysis = api_client.analyze_resume(
                    resume_file=resume_file,
                    access_token=token,
                    job_role=(
                        job_role
                        if mode == "Job Matching"
                        and job_matching_type == "Job Role"
                        else ""
                    ),
                    job_description=(
                        job_description
                        if mode == "Job Matching"
                        and job_matching_type == "Job Description"
                        else ""
                    ),
                )
        except requests.RequestException as exc:
            _show_backend_error(exc)
            return
        st.session_state["scorer_analysis"] = analysis
        st.success("Analysis complete.")
        st.rerun()

    analysis = st.session_state.get("scorer_analysis")
    if analysis:
        st.markdown("---")
        display_results_dashboard(analysis)
        _render_export_buttons(analysis)

        st.markdown("---")
        st.caption(
            "This is a transparent, project-defined resume-quality estimate—not an official ATS score or a prediction of hiring outcomes."
        )

from typing import Any, Dict
import streamlit as st


def display_job_description_match(data: Dict[str, Any]) -> None:
    if not data:
        return

    st.markdown("### Job Description Match")

    job_title = data.get("job_title") or "Provided job description"
    st.caption(f"Target position: {job_title}")

    st.caption(
        "This comparison evaluates your resume against the requirements "
        "extracted from the supplied job description."
    )

    if not data.get("score_available"):
        st.info(
            data.get("message")
            or "A reliable match score could not be calculated."
        )
        return

    score = float(data.get("match_score") or 0)

    st.metric("Job description match score", f"{score:.1f}%")
    st.progress(max(0.0, min(1.0, score / 100)))

    st.caption(data.get("score_method", ""))

    left, right = st.columns(2)

    with left:
        st.markdown("**Matched required skills**")

        matched = data.get("matched_skills", [])

        for skill in matched:
            st.markdown(f"- {skill}")

        if not matched:
            st.caption("No required skills matched.")

    with right:
        st.markdown("**Missing required skills**")

        missing = data.get("missing_skills", [])

        for skill in missing:
            st.markdown(f"- {skill}")

        if not missing:
            st.caption("No missing required skills detected.")

    st.markdown("**Preferred skills matched**")

    preferred = data.get("preferred_matches", [])

    st.write(
        ", ".join(preferred)
        if preferred
        else "No preferred skills matched."
    )

    st.markdown("**Project / experience evidence detected**")

    evidence = data.get("evidence_backed_skills", [])

    st.write(
        ", ".join(evidence)
        if evidence
        else "No direct evidence was detected in project or experience descriptions."
    )

    st.markdown("**Relevant resume evidence**")

    projects = data.get("relevant_projects", [])
    experience = data.get("relevant_experience", [])

    st.write(
        "Projects: "
        + (
            ", ".join(projects)
            if projects
            else "No matching project evidence detected."
        )
    )

    st.write(
        "Experience: "
        + (
            ", ".join(experience)
            if experience
            else "No matching experience evidence detected."
        )
    )

    st.caption(
        "This is a resume-to-job-description comparison, "
        "not a prediction of hiring probability."
    )

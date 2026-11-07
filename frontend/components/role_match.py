from typing import Any, Dict
import streamlit as st


def display_role_match(data: Dict[str, Any]) -> None:
    if not data:
        return

    st.markdown("### Job Role Match")
    st.caption(f"Target role: {data.get('job_role', 'Custom role')}")
    if not data.get("score_available"):
        st.info(data.get("message") or "A curated profile is not available for this custom role, so no match score is generated.")
        return

    score = float(data.get("match_score") or 0)
    st.metric("Role match score", f"{score:.1f}%")
    st.progress(max(0.0, min(1.0, score / 100)))
    st.caption(data.get("score_method", ""))

    left, right = st.columns(2)
    with left:
        st.markdown("**Matched required skills**")
        for skill in data.get("matched_skills", []):
            st.markdown(f"- {skill}")
        if not data.get("matched_skills"):
            st.caption("No required skills matched.")
    with right:
        st.markdown("**Missing required skills**")
        for skill in data.get("missing_skills", []):
            st.markdown(f"- {skill}")
        if not data.get("missing_skills"):
            st.caption("No missing required skills in this profile.")

    st.markdown("**Project / experience evidence detected**")
    evidence = data.get("evidence_backed_skills", [])
    st.write(", ".join(evidence) if evidence else "No direct evidence was detected in project or experience descriptions.")
    preferred = data.get("preferred_matches", [])
    if preferred:
        st.markdown("**Additional matching skills**")
        st.write(", ".join(preferred))
    projects = data.get("relevant_projects", [])
    experience = data.get("relevant_experience", [])
    st.markdown("**Relevant resume evidence**")
    st.write("Projects: " + (", ".join(projects) if projects else "No matching project evidence detected."))
    st.write("Experience: " + (", ".join(experience) if experience else "No matching experience evidence detected."))

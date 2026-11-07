import requests
import streamlit as st
from frontend.services import api_client


def _show_backend_error(exc: Exception) -> None:
    if isinstance(exc, requests.ConnectionError):
        st.error("Could not reach the analysis server. Check that the backend is running.")
    elif isinstance(exc, requests.HTTPError) and exc.response is not None:
        st.error(f"Analysis server returned {exc.response.status_code}: {exc.response.text}")
    else:
        st.error(f"Unexpected error: {exc}")


def render() -> None:
    st.markdown(
        '<div class="page-heading"><div class="page-eyebrow">YOUR WORKSPACE</div>'
        '<h1>Analysis History</h1><p>Review previous resume assessments saved to your account.</p></div>',
        unsafe_allow_html=True,
    )
    token = st.session_state.get("access_token")
    if not token:
        st.warning("Sign in to view your analysis history.")
        return
    try:
        history = api_client.get_history(token)
    except requests.RequestException as exc:
        _show_backend_error(exc)
        return

    if not history:
        st.markdown(
            '<div class="empty-state-card"><h3>No analyses yet</h3>'
            '<p>Your completed resume assessments will appear here.</p></div>',
            unsafe_allow_html=True,
        )
        if st.button("Start your first analysis", type="primary"):
            st.session_state.current_view = "scorer"
            st.rerun()
        return

    st.metric("Saved analyses", len(history))
    for idx, entry in enumerate(history):
        analysis = entry.get("analysis_result") or {}
        role_data = analysis.get("role_match_analysis") or {}
        jd_data = analysis.get("job_description_match_analysis") or {}
        role = (analysis.get("job_role") or jd_data.get("job_title") or "General ATS")
        score = float(entry.get("ats_score", analysis.get("ats_score", 0)) or 0)
        filename = entry.get("filename", "Resume")
        created = entry.get("created_at", "")
        with st.container(border=True):
            top = st.columns([3, 1, 1])
            with top[0]:
                st.markdown(f"**{filename}**")
                st.caption(f"{created} · {role}")
            with top[1]:
                st.metric("ATS score", f"{score:.0f}/100")
            with top[2]:    
                if jd_data.get("score_available"):
                    st.metric(
                        "JD match",
                        f"{jd_data.get('match_score', 0):.0f}%"
                    )
                elif role_data.get("score_available"):
                    st.metric("Role match", f"{role_data.get('match_score', 0):.0f}%")
                else:
                    st.metric("Match score", "—")
            with st.expander("View analysis details"):
                component = analysis.get("component_scores") or {}
                c1, c2, c3, c4, c5 = st.columns(5)
                for col, (label, key, maximum) in zip(
                    [c1, c2, c3, c4, c5],
                    [("Formatting", "formatting", 20), ("Keywords", "keywords", 25),
                     ("Content", "content", 25), ("Skill validation", "skill_validation", 15),
                     ("ATS compatibility", "ats_compatibility", 15)]
                ):
                    col.metric(label, f"{component.get(key, 0):.0f}/{maximum}")
                if role_data:
                    st.markdown("**Matched role skills:** " + (", ".join(role_data.get("matched_skills", [])) or "None detected"))
                    st.markdown("**Missing role skills:** " + (", ".join(role_data.get("missing_skills", [])) or "None detected"))

                if jd_data:
                    st.markdown("**Matched JD skills:** " + (
                        ", ".join(jd_data.get("matched_skills", [])) or "None detected"
                    ))

                    st.markdown("**Missing JD skills:** " + (
                        ", ".join(jd_data.get("missing_skills", [])) or "None detected"
                    ))

                    st.markdown("**Preferred skills matched:** " + (
                        ", ".join(jd_data.get("preferred_matches", [])) or "None detected"
                    ))

                    st.markdown("**Evidence-backed skills:** " + (
                        ", ".join(jd_data.get("evidence_backed_skills", [])) or "None detected"
                    ))

                if analysis.get("strengths"):
                    st.markdown("**Strengths**")
                    for item in analysis["strengths"][:5]:
                        st.markdown(f"- {item}")
            entry_id = entry.get("id")
            actions = st.columns([1, 1, 4])
            if entry_id:
                with actions[0]:
                    if st.button("Download PDF", key=f"history_pdf_{idx}"):
                        try:
                            pdf = api_client.get_history_pdf(str(entry_id), token)
                            st.download_button(
                                "Save PDF", data=pdf,
                                file_name=f"resume_analysis_{idx + 1}.pdf",
                                mime="application/pdf", key=f"history_pdf_save_{idx}"
                            )
                        except requests.RequestException as exc:
                            _show_backend_error(exc)
                with actions[1]:
                    if st.button("Delete", key=f"delete_{idx}"):
                        try:
                            api_client.delete_history_entry(str(entry_id), token)
                            st.success("Analysis deleted.")
                            st.rerun()
                        except requests.RequestException as exc:
                            _show_backend_error(exc)

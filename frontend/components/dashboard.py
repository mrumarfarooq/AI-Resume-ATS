from typing import Any, Dict

import streamlit as st

from frontend.components.score_display import display_overall_score, display_score_breakdown
from frontend.components.strengths_issues import display_strengths, display_critical_issues
from frontend.components.skill_validation import display_skill_validation
from frontend.components.role_match import display_role_match
from frontend.components.job_description_match import display_job_description_match
from frontend.components.detailed_feedback import display_detailed_feedback
from frontend.components.action_items import display_action_items
from frontend.components.recommendations import display_recommendations


def display_results_dashboard(analysis: Dict[str, Any]) -> None:
    """
    Render the full results page from one backend response dict.

    `analysis` is the JSON body returned by POST /api/v1/analyze-resume
    (i.e. an AnalysisResponse). No transformation is done here — every
    section reads the fields it needs directly.
    """
    display_overall_score(analysis)
    warnings = analysis.get("warnings") or []
    if warnings:
        with st.expander("Analysis coverage and limitations"):
            for warning in warnings:
                st.write(f"- {warning}")
    st.markdown("---")

    display_score_breakdown(analysis)
    st.markdown("---")

    display_strengths(analysis.get("strengths") or [])
    st.markdown("---")

    display_critical_issues(analysis)
    st.markdown("---")

    display_skill_validation(analysis)
    st.markdown("---")

    role_match = analysis.get("role_match") or analysis.get("role_match_analysis")
    if role_match:
        display_role_match(role_match)
        st.markdown("---")

    job_description_match = analysis.get("job_description_match_analysis")

    if job_description_match:
        display_job_description_match(job_description_match)
        st.markdown("---")



    display_detailed_feedback(analysis)
    st.markdown("---")

    display_action_items(analysis)
    st.markdown("---")

    display_recommendations(analysis)

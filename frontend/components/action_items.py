from typing import Any, Dict, List, Tuple

import streamlit as st


SEVERITY_RANK = {"critical": 0, "high": 1, "moderate": 2, "medium": 2, "low": 3}


def _collect_action_items(analysis: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    """Return list of (severity, source_title, action_text)."""
    items: List[Tuple[str, str, str]] = []

    for issue in analysis.get("detailed_feedback") or []:
        level = (issue.get("severity_level") or "low").lower()
        title = issue.get("issue_title", "")
        for action in issue.get("action_items") or []:
            items.append((level, title, action))

    if not items:
        for suggestion in analysis.get("suggestions") or []:
            items.append(("medium", "General", suggestion))

    items.sort(key=lambda row: SEVERITY_RANK.get(row[0], 99))
    return items


def display_action_items(analysis: Dict[str, Any]) -> None:
    items = _collect_action_items(analysis)

    if not items:
        return

    grouped_items = {}

    for level, source, action in items:
        key = (level, source)

        if key not in grouped_items:
            grouped_items[key] = []

        if action not in grouped_items[key]:
            grouped_items[key].append(action)

    st.markdown("### Improvement Checklist")
    st.caption(
        "Complete these tasks to strengthen your resume. "
        "Each issue is grouped to make improvements easier to track."
    )

    for group_index, ((level, source), actions) in enumerate(grouped_items.items()):
        st.markdown(f"**{source}**")
        st.caption(f"Priority: {level.title()}")

        for action_index, action in enumerate(actions):
            st.checkbox(
                action,
                key=f"improvement_action_{group_index}_{action_index}",
            )

        st.divider()
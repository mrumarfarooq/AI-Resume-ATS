import streamlit as st


def render():
    st.markdown(
        '<div class="page-heading"><div class="page-eyebrow">CAREER TOOLKIT</div>'
        '<h1>Resources</h1><p>Practical guidance to make your resume clearer, more credible, and easier to scan.</p></div>',
        unsafe_allow_html=True,
    )

    st.markdown("### Build an ATS-readable resume")
    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.markdown("#### Recommended practices")
            for item in [
                "Use standard section headings such as Experience, Education, Skills, and Projects.",
                "Use a simple single-column layout with readable fonts.",
                "Describe work with action verbs and specific outcomes.",
                "List tools and technologies only when you can discuss or demonstrate them.",
                "Use consistent date formats and clear bullet points.",
            ]:
                st.markdown(f"- {item}")
    with right:
        with st.container(border=True):
            st.markdown("#### Common pitfalls")
            for item in [
                "Avoid placing important details only inside images, charts, or text boxes.",
                "Do not add keywords that do not reflect your real experience.",
                "Avoid long paragraphs that hide important contributions.",
                "Do not invent metrics or inflate responsibilities.",
                "Check the extracted text after exporting your resume to PDF.",
            ]:
                st.markdown(f"- {item}")

    st.markdown("### Technical resume checklist")
    tabs = st.tabs(["Software development", "Data roles", "Cloud & DevOps"])
    with tabs[0]:
        st.markdown("**Useful evidence to show**")
        st.write("Programming language usage, API development, database work, testing, version control, deployment, and project outcomes.")
    with tabs[1]:
        st.markdown("**Useful evidence to show**")
        st.write("SQL queries, data cleaning, exploratory analysis, visualization, statistical reasoning, and business questions answered.")
    with tabs[2]:
        st.markdown("**Useful evidence to show**")
        st.write("Linux administration, networking fundamentals, scripting, CI/CD workflows, containers, cloud services, and troubleshooting examples.")

    st.info("A resume checker can identify patterns and missing evidence, but it cannot guarantee ATS ranking, interviews, or hiring outcomes.")

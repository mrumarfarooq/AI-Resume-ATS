import streamlit as st
import streamlit.components.v1 as components

def render():
    st.markdown("""
    <section class="saas-hero">
      <div class="saas-eyebrow"><span class="eyebrow-dot"></span> AI-POWERED RESUME INTELLIGENCE</div>
      <h1>Make your resume<br><span>work harder for you</span></h1>
      <p class="saas-hero-copy">Get a clearer picture of your resume's strengths, identify skill gaps, and receive practical feedback to improve your next application.</p>
    </section>
    """, unsafe_allow_html=True)

    left, center, right = st.columns([1, 1.35, 1])
    with center:
        if st.button("Start analyzing your resume", type="primary", use_container_width=True, key="landing_analyze_button"):
            if st.session_state.get("access_token"):
                st.session_state.current_view = "scorer"
            else:
                st.session_state.current_view = "auth"
                st.session_state.auth_info = "Sign in or create an account to start your resume analysis."
            st.rerun()

    st.markdown(
      '<div id="features-section" class="saas-section-intro">'
      '<div class="saas-kicker">WHAT YOU GET</div>'
      '<h2>Everything you need to improve</h2>'
      '<p>Useful resume insights, presented clearly and transparently.</p>'
      '</div>',
      unsafe_allow_html=True,
    )

    if st.session_state.pop("scroll_to_features", False):
        components.html(
            """
            <script>
            let attempts = 0;

            const scrollToFeatures = () => {
                const doc = window.parent.document;
                const target = doc.getElementById("features-section");

                if (!target) {
                    attempts++;
                    if (attempts < 20) {
                        setTimeout(scrollToFeatures, 70);
                    }
                    return;
                }

                const scroller =
                    doc.querySelector('[data-testid="stMain"]') ||
                    doc.querySelector("section.main") ||
                    doc.scrollingElement;

                const targetTop = target.getBoundingClientRect().top;
                const scrollTop = scroller.getBoundingClientRect
                    ? scroller.scrollTop + targetTop -
                      scroller.getBoundingClientRect().top - 20
                    : targetTop;

                scroller.scrollTo({
                    top: scrollTop,
                    behavior: "smooth"
                });
            };

            setTimeout(scrollToFeatures, 120);
            </script>
            """,
            height=1,
        )

    features = [
      ("01", "Comprehensive scoring", "Understand your resume across formatting, keywords, content quality, skill validation, and ATS compatibility.", ["Five scoring dimensions", "Clear score breakdown", "Practical improvement areas"]),
      ("02", "AI skill validation", "See whether the skills you list are supported by the projects and experience described in your resume.", ["Semantic skill analysis", "Evidence-based feedback", "Spot unsupported claims"]),
      ("03", "Job role matching", "Compare your resume with a curated target-role profile and identify skills that are present, missing, or supported by project evidence.", ["Eight curated job roles", "Matched and missing skills", "Separate role-match score"]),
    ]
    cols = st.columns(3, gap="large")
    for col, (number, title, desc, bullets) in zip(cols, features):
      with col:
        st.markdown(f'''<article class="saas-feature-card">
          <div class="saas-card-top"><span class="saas-feature-number">{number}</span><span class="saas-card-mark">↗</span></div>
          <h3>{title}</h3><p>{desc}</p>
          <ul>{''.join(f'<li>{item}</li>' for item in bullets)}</ul>
        </article>''', unsafe_allow_html=True)

    st.markdown('<div class="saas-section-intro how-intro"><div class="saas-kicker">A SIMPLE WORKFLOW</div><h2>From upload to useful insight</h2><p>Three straightforward steps. You stay in control throughout.</p></div>', unsafe_allow_html=True)
    steps = [
      ("01", "Upload your resume", "Add your PDF or DOCX resume securely to begin."),
      ("02", "Review the analysis", "Explore your ATS score, skill evidence, and optional job role match."),
      ("03", "Improve with confidence", "Use clear feedback and download your report."),
    ]
    step_cols = st.columns(3, gap="large")
    for col, (n, title, desc) in zip(step_cols, steps):
      with col:
        st.markdown(f'<article class="saas-step"><span>{n}</span><h3>{title}</h3><p>{desc}</p></article>', unsafe_allow_html=True)

    st.markdown('''<div class="saas-privacy"><div class="privacy-icon">✓</div><div><strong>Your resume. Your decision.</strong><p>Review your document before uploading. Resume analysis is intended to provide guidance, not guarantee hiring outcomes.</p></div></div>
    <footer class="saas-footer"><strong>ResumeATS</strong><span>Thoughtful feedback for your next career move.</span><span>© 2026 ResumeATS</span></footer>''', unsafe_allow_html=True)

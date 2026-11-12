import io
import logging

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_INSTALLED = True
except ImportError:
    WEASYPRINT_INSTALLED = False

logger = logging.getLogger('ats_resume_scorer')


def generate_combined_pdf(html_docs: dict[str, str]) -> bytes:
    if not WEASYPRINT_INSTALLED:
        raise ImportError("WeasyPrint is not installed. PDF generation unavailable.")

    if not html_docs:
        raise ValueError("No HTML reports available for PDF generation.")

    documents = []

    # Render each report with consistent A4 page settings.
    page_css = CSS(string="""
        @page {
            size: A4;
            margin: 18mm 18mm 20mm 18mm;
        }

        html, body {
            margin: 0;
            padding: 0;
        }

        .footer {
            break-inside: avoid;
            page-break-inside: avoid;
        }
    """)

    for name, html_str in html_docs.items():
        doc = HTML(string=html_str).render(stylesheets=[page_css])
        documents.append(doc)

    # Merge rendered pages in report order.
    first_doc = documents[0]
    for other_doc in documents[1:]:
        first_doc.pages.extend(other_doc.pages)

    return first_doc.write_pdf()

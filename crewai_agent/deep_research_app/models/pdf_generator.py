from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
import tempfile

# Task 6: Implements create_pdf function

def create_pdf(summary, content, links):
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(temp_pdf.name, pagesize=letter,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)

    styles = getSampleStyleSheet()
    flowables = [
        Paragraph("<b>Deep Research Report</b>", styles["Title"]),
        Spacer(1, 0.2 * inch),
        Paragraph(f"<b>{summary}</b>", styles["Heading2"]),
        Spacer(1, 0.2 * inch),
        Paragraph("<b>Research Findings:</b>", styles["Heading3"])
    ]

    for line in content.split('\n'):
        if line.strip():
            flowables.append(Paragraph(line.strip(), styles["BodyText"]))
            flowables.append(Spacer(1, 0.1 * inch))

    if links:
        flowables.append(Spacer(1, 0.3 * inch))
        flowables.append(Paragraph("<b>Links Used:</b>", styles["Heading3"]))
        for i, link in enumerate(links, 1):
            flowables.append(Paragraph(f"{i}. <a href='{link}' color='blue'>{link}</a>", styles["BodyText"]))
            flowables.append(Spacer(1, 0.1 * inch))

    doc.build(flowables)
    return temp_pdf.name
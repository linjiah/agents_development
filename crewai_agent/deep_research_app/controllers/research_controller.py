from services.agents_service import setup_agents_and_tasks, extracted_links
from models.pdf_generator import create_pdf
from utils.markdown_cleaner import clean_markdown
import base64

# Task 7: Implements run_deep_research function

def run_deep_research(query, breadth, depth):
    extracted_links.clear()
    crew, _, _ = setup_agents_and_tasks(query, breadth, depth)

    # Execute the crew workflow
    result = crew.kickoff()

    # CrewAI may return complex objects; convert to string for post-processing
    raw_output = getattr(result, "raw", getattr(result, "output", result))
    cleaned_output = clean_markdown(str(raw_output))

    # Deduplicate any links collected by the Firecrawl tool
    unique_links = list(dict.fromkeys(extracted_links))

    # Build PDF and encode to base64 for Streamlit rendering
    pdf_path = create_pdf(f"Research summary for {query}", cleaned_output, unique_links)
    with open(pdf_path, "rb") as pdf_file:
        pdf_data = pdf_file.read()

    base64_pdf = base64.b64encode(pdf_data).decode("utf-8")

    return cleaned_output, pdf_data, base64_pdf
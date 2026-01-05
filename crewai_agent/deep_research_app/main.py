import streamlit as st
from controllers.research_controller import run_deep_research


# Task 8: Create the GUI for the Deep Research Tool

st.title("Deep Research Assistant with CrewAI")
st.markdown("Enter your research topic and configure parameters below:")

query = st.text_input("Research Query")
breadth = st.slider("Search Breadth (Number of Queries)", 1, 10, 3)
depth = st.slider("Search Depth (Recursion Levels)", 1, 5, 2)

if st.button("Run Deep Research"):
    if not query:
        st.error("Please enter a research query.")
    else:
        with st.spinner("Running research process with CrewAI agents..."):
            cleaned_output, pdf_data, base64_pdf = run_deep_research(query, breadth, depth)

            st.success("Research complete!")
            st.markdown("### Cleaned Final Report")
            st.text_area("Preview", cleaned_output, height=400)

            st.download_button(
                label="Download Report as PDF",
                data=pdf_data,
                file_name="deep_research_report.pdf",
                mime="application/pdf"
            )

            st.markdown("### PDF Preview")
            st.markdown(
                f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600px" type="application/pdf"></iframe>',
                unsafe_allow_html=True
            )
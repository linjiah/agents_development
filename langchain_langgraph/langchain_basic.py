import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

project_dir = Path(__file__).resolve().parent
load_dotenv(dotenv_path=project_dir / ".env")
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY not set in environment or .env file.")

llm = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct", api_key=groq_api_key)

parse_template = PromptTemplate(
    input_variables=["raw_feedback"],
    template="Parse and clean the following customer feedback for key information:\n\n{raw_feedback}"
)

summary_template = PromptTemplate(
    input_variables=["parsed_feedback"],
    template="Summarize this customer feedback in one concise sentence:\n\n{parsed_feedback}"
)

sentiment_template = PromptTemplate(
    input_variables=["feedback"],
    template="Determine the sentiment of this feedback and reply in one word as either 'Positive', 'Neutral', or 'Negative':\n\n{feedback}"
)

thankyou_template = PromptTemplate(
    input_variables=["feedback"],
    template="Given the feedback, draft a thank you message for the user and request them to leave a positive rating on our webpage:\n\n{feedback}"
)

details_template = PromptTemplate(
    input_variables=["feedback"],
    template="Given the feedback, draft a message for the user and request them provide more details about their concern:\n\n{feedback}"
)

apology_template = PromptTemplate(
    input_variables=["feedback"],
    template="Given the feedback, draft an apology message for the user and mention that their concern has been forwarded to the relevant department:\n\n{feedback}"
)

thankyou_chain = thankyou_template | llm | StrOutputParser()
details_chain = details_template | llm | StrOutputParser()
apology_chain = apology_template | llm | StrOutputParser()

def route(info):
    sentiment = info["sentiment"].strip().lower()
    if sentiment.startswith("positive"):
        return thankyou_chain
    elif sentiment.startswith("negative"):
        return apology_chain
    else:
        return details_chain

# Neutral
user_feedback = "The delivery was late, and the product was damaged when it arrived. However, the customer support team was very helpful in resolving the issue quickly."

# Postive
# user_feedback = "The customer service was fantastic. The representative was friendly, knowledgeable, and resolved my issue quickly."

# Negative
# user_feedback = "I was extremely disappointed with the customer service. The representative was unhelpful and rude."

format_parsed_output = RunnableLambda(lambda output: {"parsed_feedback": output})

summary_chain = parse_template | llm | format_parsed_output | summary_template | llm | StrOutputParser()
sentiment_chain = sentiment_template| llm | StrOutputParser()

summary = summary_chain.invoke({'raw_feedback' : user_feedback})
sentiment = sentiment_chain.invoke({'feedback': user_feedback})

print("The summary of the user's message is:", summary)
print("The sentiment was classifed as:", sentiment)

full_chain = {"feedback": lambda x: x['feedback'], 'sentiment' : lambda x : x['sentiment']} | RunnableLambda(route)

print(full_chain.invoke({'feedback': summary, 'sentiment': sentiment}))
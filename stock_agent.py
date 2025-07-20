import os
import json
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from models.stock_report import TrendingStocksReport

load_dotenv()  # Load environment variables from .env file

# --- Configuration ---
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
MODEL_ID = "gemini-2.5-flash"

# --- Helper Functions ---
def get_client():
    """Initializes and returns the GenAI client, checking for project ID."""
    if not PROJECT_ID:
        raise ValueError("Error: GOOGLE_CLOUD_PROJECT environment variable not set.")
    # print(f"Using Google Cloud Project: {PROJECT_ID} and Location: {LOCATION}")
    return genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

def find_trending_stocks_data(user_query: str):
    """Uses Google Search grounding to find data on trending stocks based on a user query."""
    print(f"--- [Step 1] Finding trending stocks data for query: '{user_query}' ---")
    client = get_client()
    search_tool = Tool(google_search=GoogleSearch())
    
    prompt = f"""Based on the user's query: '{user_query}', what are the top 5 trending stocks in the US market right now? 
I'm looking for a list of the top 5 companies that are currently generating a lot of buzz relevant to the query. 
Please provide the stock ticker, the company name, and a brief (one-sentence) reason for why each stock is trending. 
If the query is not specific, provide general trending stocks."""

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config=GenerateContentConfig(tools=[search_tool])
    )
    
    print("--- [Step 1] Raw search data received ---")
    # print(response.text)
    return response.text

def generate_structured_report(raw_data: str):
    """Uses LangChain and OpenRouter to parse raw data into a structured report."""
    llm = ChatOpenAI(
        model="google/gemini-flash-1.5",
        temperature=0.0,
        openai_api_key=os.environ.get("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
    )
    parser = JsonOutputParser(pydantic_object=TrendingStocksReport)
    prompt = PromptTemplate(
        template="""You are a financial data processing agent.\n
        Your task is to extract key stock information from a raw text blob and format it into a structured JSON report.

        The output should be a JSON object that strictly follows this Pydantic model:
        {format_instructions}

        Here is the raw data:
        {raw_text}
        """,
        input_variables=["raw_text"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    chain = prompt | llm | parser
    structured_response = chain.invoke({"raw_text": raw_data})
    return structured_response

def get_trending_stocks(user_query: str):
    """Fetches, processes, and returns a structured report of trending stocks based on a user query."""
    print(f"--- [AGENT] Fetching trending stocks for query: {user_query} ---")
    raw_data = find_trending_stocks_data(user_query)
    print("--- [AGENT] Generating structured report for trending stocks ---")
    structured_report = generate_structured_report(raw_data)
    return structured_report

# --- Main Execution ---
if __name__ == '__main__':
    try:
        # Step 1: Get raw data using Google Search
        trending_stocks_report = get_trending_stocks()
        raw_trending_data = find_trending_stocks_data()
        
        # Step 2: Convert raw data into a structured report
        structured_report = generate_structured_report(raw_trending_data)
        
        # Step 3: Print the final, structured report
        print("\n--- Top 10 Trending Stocks Report ---")
        # Pretty-print the JSON output
        print(json.dumps(structured_report, indent=2))
        
    except Exception as e:
        print(f"\nAn error occurred: {e}")
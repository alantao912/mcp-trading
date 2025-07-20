import os
import json
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
from dotenv import load_dotenv
from langchain_google_vertexai import VertexAI
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
    print(f"Using Google Cloud Project: {PROJECT_ID} and Location: {LOCATION}")
    return genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

def find_trending_stocks_data():
    """Uses Google Search grounding to find data on trending stocks."""
    print("--- [Step 1] Finding trending stocks data via Google Search ---")
    client = get_client()
    search_tool = Tool(google_search=GoogleSearch())
    
    prompt = """What are the top 10 trending stocks in the US market right now? ALWAYS USE SEARCH TOOL to find the data. Include the company name, ticker symbol, and a brief reason for why each is trending. Just give me what you have. it not important"""
    
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config=GenerateContentConfig(tools=[search_tool])
    )
    
    print("--- [Step 1] Raw search data received ---")
    print(response.text)
    return response.text

def generate_structured_report(raw_data: str):
    """Uses LangChain and VertexAI to parse raw data into a structured report."""
    print("--- [Step 2] Generating structured report from raw data ---")
    llm = VertexAI(model_name=MODEL_ID, project=PROJECT_ID, location=LOCATION)
    parser = JsonOutputParser(pydantic_object=TrendingStocksReport)
    
    prompt = PromptTemplate(
        template="Parse the following raw text to extract the top 10 trending stocks. Format the output as a JSON object that follows the provided schema.\n{format_instructions}\n\nRaw Text:\n{raw_text}\n",
        input_variables=["raw_text"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    
    chain = prompt | llm | parser
    structured_response = chain.invoke({"raw_text": raw_data})
    
    print("--- [Step 2] Structured report generated ---")
    return structured_response

# --- Main Execution ---
if __name__ == '__main__':
    try:
        # Step 1: Get raw data using Google Search
        raw_trending_data = find_trending_stocks_data()
        
        # Step 2: Convert raw data into a structured report
        structured_report = generate_structured_report(raw_trending_data)
        
        # Step 3: Print the final, structured report
        print("\n--- Top 10 Trending Stocks Report ---")
        # Pretty-print the JSON output
        print(json.dumps(structured_report, indent=2))
        
    except Exception as e:
        print(f"\nAn error occurred: {e}")
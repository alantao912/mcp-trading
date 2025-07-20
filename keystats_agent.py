import os
import json
import argparse
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from models.key_stats import KeyStats

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

def get_key_stats_data(stock_symbol: str):
    """Uses Google Search grounding to find key stats for a stock symbol."""
    print(f"--- [Step 1] Finding key stats for {stock_symbol} via Google Search ---")
    client = get_client()
    search_tool = Tool(google_search=GoogleSearch())
    
    prompt = f"Go to https://www.cnbc.com/quotes/{stock_symbol} and find the 'KEY STATS' section. Extract all the values from that section. USE SEARCH to find the data. I need all the values listed in the KEY STATS section, including Open, Day High, Day Low, Prev Close, 52 Week High, 52 Week High Date, 52 Week Low, 52 Week Low Date, Market Cap, Shares Out, 10 Day Average Volume, Dividend, Dividend Yield, Beta, YTD % Change, EPS (TTM), P/E (TTM), Fwd P/E (NTM), EBITDA (TTM), ROE (TTM), Revenue (TTM), Gross Margin (TTM), Net Margin (TTM), Debt To Equity (MRQ), Earnings Date, Ex Div Date, Div Amount, Split Date, and Split Factor."
    
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config=GenerateContentConfig(tools=[search_tool])
    )
    
    print("--- [Step 1] Raw search data received ---")
    print(response.text)
    return response.text

def generate_structured_report(raw_data: str):
    """Uses LangChain and OpenRouter to parse raw data into a structured report."""
    llm = ChatOpenAI(
        model="google/gemini-flash-1.5",
        temperature=0.0,
        openai_api_key=os.environ.get("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
    )
    parser = JsonOutputParser(pydantic_object=KeyStats)
    
    prompt = PromptTemplate(
        template="""You are a financial data processing agent.\n
        Your task is to extract key statistics from a raw text blob and format it into a structured JSON report.

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
    
    print("--- [Step 2] Structured report generated ---")
    return structured_response

def get_key_stats(stock_symbol: str):
    """Fetches and processes key stats for a given stock symbol."""
    print(f"--- [AGENT] Fetching key stats for {stock_symbol} ---")
    raw_data = get_key_stats_data(stock_symbol)
    print(f"--- [AGENT] Generating structured report for {stock_symbol} ---")
    structured_report = generate_structured_report(raw_data)
    return structured_report

# --- Main Execution ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fetch key stock statistics.')
    parser.add_argument('symbol', type=str, help='The stock symbol to look up (e.g., GOOG, AAPL).')
    args = parser.parse_args()

    try:
        # Step 1: Get raw data using Google Search
        raw_stats_data = get_key_stats_data(args.symbol)
        
        # Step 2: Convert raw data into a structured report
        structured_report = generate_structured_report(raw_stats_data)
        
        # Step 3: Print the final, structured report
        print(f"\n--- Key Stats for {args.symbol.upper()} ---")
        print(json.dumps(structured_report, indent=2))
        
    except Exception as e:
        print(f"\nAn error occurred: {e}")

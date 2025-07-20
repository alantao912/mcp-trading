import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from models.final_report import FinalReport

# Load environment variables
load_dotenv()

def generate_summary(user_query: str, trending_stocks: list, key_stats: dict, news: dict, portfolio_holdings: dict):
    """
    Generates a final summary and analysis based on all gathered data and a user query.
    This function now streams the response chunk by chunk.
    """
    """
    Generates a final summary and analysis based on all gathered data and a user query.
    """
    print("--- [AGENT] Generating final summary ---")

    # Initialize the LLM
    llm = ChatOpenAI(
        model="google/gemini-2.5-flash", 
        temperature=0.1,
        openai_api_key=os.environ.get("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1"
    )

    # Set up the parser
    parser = JsonOutputParser(pydantic_object=FinalReport)

    # Create the prompt template
    prompt = PromptTemplate(
        template="""
You are an expert financial analyst AI. Your task is to provide a comprehensive analysis of trending stocks based on the data provided and answer the user's specific query.

**Disclaimer**: Start your final response with a clear and prominent disclaimer formatted in markdown that this is not financial advice and users should consult with a qualified professional before making any investment decisions. Use **bold** formatting for emphasis.

**User's Query**:
{user_query}

**Collected Data**:

1. **Trending Stocks**:
{trending_stocks}

2. **Key Statistics**:
{key_stats}

3. **Recent News**:
{news}

4. **Current Portfolio Holdings**:
{portfolio_holdings}

**Instructions**:

1.  **Market Overview**: Begin with a high-level summary of the current market sentiment based on the list of trending stocks. Are they mostly tech, finance, etc.? What does this suggest about the current market focus? Format this as markdown with proper headings and bullet points.

2.  **Detailed Stock Analysis**: For each stock, provide a detailed analysis using markdown formatting:
    - Use **bold** for key metrics and important points
    - Use bullet points for listing key statistics
    - Use *italics* for emphasis on sentiment or trends
    - Include clear sections for fundamentals, technicals, and news sentiment

3.  **Portfolio Analysis**: Analyze the user's current portfolio in the context of the trending stocks and market overview. Identify any overlaps, risks, or opportunities. For example, is the portfolio well-diversified? Is it heavily exposed to a particular sector that is currently volatile? Provide insights on how the trending stocks could impact the user's holdings.

4.  **Actionable Recommendation**: Based on your analysis and the user's query, provide a specific recommendation for each stock (e.g., 'buy', 'sell', 'hold', 'monitor'). Format recommendations using markdown:
    - Use **bold** for the recommendation type
    - Use bullet points for reasoning
    - Include risk assessment where relevant

5.  **Final Summary**: Conclude with a final summary that directly answers the user's query, using markdown formatting:
    - Use headings (##) for different sections
    - Use bullet points for key takeaways
    - Use **bold** for important conclusions

6.  **Markdown Formatting**: Use proper markdown syntax throughout:
    - Headers: ## for main sections, ### for subsections
    - Lists: - for bullet points, 1. for numbered lists
    - Emphasis: **bold** for important points, *italic* for emphasis
    - Code: `backticks` for stock tickers or specific values

7.  **Format**: Ensure your entire output is a single, valid JSON object that conforms to the provided schema. All text content should be properly formatted markdown.

8. **Final Output**: The final output must be ONLY the JSON object. Do not include any other text or markdown formatting, such as ```json ... ```, outside of the JSON structure.

{format_instructions}
""",
        input_variables=["user_query", "trending_stocks", "key_stats", "news", "portfolio_holdings"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    # Create the chain
    chain = prompt | llm | parser

    # Invoke the chain with the collected data
    response = chain.invoke({
        "user_query": user_query,
        "trending_stocks": trending_stocks,
        "key_stats": key_stats,
        "news": news,
        "portfolio_holdings": portfolio_holdings
    })

    print("--- [AGENT] Final summary generated ---")
    return response

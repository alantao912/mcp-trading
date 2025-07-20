import os
import json
import operator
from typing import TypedDict, List, Annotated
from dotenv import load_dotenv
from phoenix.otel import register
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
from langchain_core.callbacks import BaseCallbackHandler
from concurrent.futures import ThreadPoolExecutor
import asyncio
from queue import Queue
import threading

# Import agent functions
from stock_agent import get_trending_stocks
from keystats_agent import get_key_stats
from news_agent import get_news_for_stock
from summary_agent import generate_summary

# Load environment variables
load_dotenv()

# Set up Arize Phoenix for local Docker instance
# os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = "http://localhost:6006"

# configure the Phoenix tracer
tracer_provider = register(
    project_name="mcp-trading",
    auto_instrument=True
)

# 1. Define the state for the graph
class GraphState(TypedDict):
    user_query: str
    trending_stocks: List[dict]
    key_stats: dict
    news: dict
    final_report: dict
    messages: Annotated[list, operator.add]

# 2. Define the nodes for the graph
def fetch_trending_stocks_node(state: GraphState):
    """Fetches the list of trending stocks based on the user query and updates the state."""
    print("---FETCHING TRENDING STOCKS---")
    user_query = state.get('user_query')
    if not user_query:
        raise ValueError("User query is missing from the state.")
    
    trending_stocks_report = get_trending_stocks(user_query)
    return {"trending_stocks": trending_stocks_report.get('stocks', [])}

def fetch_key_stats_node(state: GraphState):
    """Fetches key statistics, streams results, and updates state."""
    print("---FETCHING KEY STATS---")
    stocks_to_process = state['trending_stocks']
    all_stats = {}
    
    # Process stocks sequentially to maintain order and provide immediate feedback
    for stock in stocks_to_process:
        ticker = stock['ticker']
        try:
            stats = get_key_stats(ticker)
            all_stats[ticker] = stats
            print(f"Completed key stats for {ticker}")
        except Exception as e:
            print(f"Error fetching stats for {ticker}: {e}")
            all_stats[ticker] = {"error": str(e)}
    
    return {"key_stats": all_stats}

def fetch_news_node(state: GraphState):
    """Fetches news, streams results, and updates state."""
    print("---FETCHING NEWS---")
    stocks_to_process = state['trending_stocks']
    all_news = {}
    
    # Process stocks sequentially to maintain order and provide immediate feedback
    for stock in stocks_to_process:
        ticker = stock['ticker']
        try:
            news_items = get_news_for_stock(ticker)
            all_news[ticker] = news_items
            print(f"Completed news for {ticker}")
        except Exception as e:
            print(f"Error fetching news for {ticker}: {e}")
            all_news[ticker] = {"error": str(e)}
    
    return {"news": all_news}

def generate_summary_node(state: GraphState):
    """Generates the final summary report and streams it."""
    print("---GENERATING FINAL SUMMARY---")
    
    report = generate_summary(
        user_query=state['user_query'],
        trending_stocks=state['trending_stocks'],
        key_stats=state['key_stats'],
        news=state['news']
    )
    
    return {"final_report": report}

# 3. Build the graph
workflow = StateGraph(GraphState)
workflow.add_node("fetch_trending_stocks", fetch_trending_stocks_node)
workflow.add_node("fetch_key_stats", fetch_key_stats_node)
workflow.add_node("fetch_news", fetch_news_node)
workflow.add_node("generate_summary", generate_summary_node)

workflow.add_edge(START, "fetch_trending_stocks")
workflow.add_edge("fetch_trending_stocks", "fetch_key_stats")
workflow.add_edge("fetch_trending_stocks", "fetch_news")
workflow.add_edge(["fetch_key_stats", "fetch_news"], "generate_summary")
workflow.add_edge("generate_summary", END)

app = workflow.compile()

# 4. Define the streaming workflow to run the graph
async def run_workflow_streaming(user_query: str):
    """Runs the LangGraph workflow and streams events for the frontend."""
    yield {"event": "start", "message": "Workflow initiated..."}
    yield {"event": "update_tracker", "step": "start", "status": "completed"}

    # Initial state with user query
    initial_state = {"user_query": user_query, "messages": []}

    try:
        # Use LangGraph's built-in streaming
        async for chunk in app.astream(initial_state):
            # chunk contains the node name and its output
            for node_name, node_output in chunk.items():
                print(f"Node '{node_name}' completed with output keys: {list(node_output.keys())}")
                
                if node_name == "fetch_trending_stocks":
                    if "trending_stocks" in node_output:
                        yield {
                            "event": "trending_stocks", 
                            "data": node_output["trending_stocks"]
                        }
                
                elif node_name == "fetch_key_stats":
                    if "key_stats" in node_output:
                        # Stream each stock's key stats as they complete
                        for ticker, stats in node_output["key_stats"].items():
                            yield {
                                "event": "key_stat",
                                "ticker": ticker,
                                "data": stats
                            }
                
                elif node_name == "fetch_news":
                    if "news" in node_output:
                        # Stream each stock's news as they complete
                        for ticker, news_items in node_output["news"].items():
                            yield {
                                "event": "news",
                                "ticker": ticker,
                                "data": news_items
                            }
                
                elif node_name == "generate_summary":
                    if "final_report" in node_output:
                        yield {
                            "event": "final_summary",
                            "data": node_output["final_report"]
                        }
        
        # Stream end event
        yield {"event": "end", "message": "Workflow completed."}
        
    except Exception as e:
        print(f"Error in graph execution: {e}")
        yield {"event": "error", "message": f"Error: {str(e)}"}


import os
import json
from typing import TypedDict, List
from dotenv import load_dotenv
from phoenix.otel import register

# Load environment variables from .env file
load_dotenv()

# configure the Phoenix tracer
tracer_provider = register(
    project_name="mcp-trading",
    auto_instrument=True
)

from concurrent.futures import ThreadPoolExecutor, as_completed
from langgraph.graph import StateGraph, END
from stock_agent import find_trending_stocks_data, generate_structured_report as generate_stock_report
from keystats_agent import get_key_stats_data, generate_structured_report as generate_keystats_report
from models.stock_report import Stock

class GraphState(TypedDict):
    trending_stocks: List[Stock]
    key_stats: dict

# Helper function for parallel execution
def fetch_stats_for_stock(stock):
    """Fetches and processes key stats for a single stock."""
    try:
        print(f"--- Fetching stats for {stock['ticker']} ---")
        raw_stats = get_key_stats_data(stock['ticker'])
        structured_stats = generate_keystats_report(raw_stats)
        return stock['ticker'], structured_stats
    except Exception as e:
        print(f"--- Error fetching stats for {stock['ticker']}: {e} ---")
        return stock['ticker'], {"error": str(e)}

# Nodes
def get_trending_stocks(state):
    print("--- [Node] Finding trending stocks ---")
    raw_data = find_trending_stocks_data()
    structured_report = generate_stock_report(raw_data)
    return {"trending_stocks": structured_report['stocks']}

def get_key_stats_for_stocks_parallel(state):
    print("--- [Node] Fetching key stats for each stock in parallel ---")
    trending_stocks = state.get('trending_stocks', [])
    all_stats = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_stock = {executor.submit(fetch_stats_for_stock, stock): stock for stock in trending_stocks}
        for future in as_completed(future_to_stock):
            ticker, stats = future.result()
            all_stats[ticker] = stats
    return {"key_stats": all_stats}

# Graph Definition
workflow = StateGraph(GraphState)

workflow.add_node("get_trending_stocks", get_trending_stocks)
workflow.add_node("get_key_stats_for_stocks_parallel", get_key_stats_for_stocks_parallel)

workflow.set_entry_point("get_trending_stocks")
workflow.add_edge("get_trending_stocks", "get_key_stats_for_stocks_parallel")
workflow.add_edge("get_key_stats_for_stocks_parallel", END)

app = workflow.compile()

# --- Main Execution ---
if __name__ == '__main__':
    initial_state = {}
    final_state = app.invoke(initial_state)
    print("\n--- Final State ---")
    print(json.dumps(final_state, indent=2))

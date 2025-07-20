
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

import asyncio
from concurrent.futures import ThreadPoolExecutor
from stock_agent import find_trending_stocks_data, generate_structured_report as generate_stock_report
from keystats_agent import get_key_stats_data, generate_structured_report as generate_keystats_report

async def fetch_stats_for_stock(stock):
    """Asynchronously fetches and processes key stats for a single stock."""
    try:
        loop = asyncio.get_running_loop()
        # Use a thread pool to run the synchronous data fetching functions
        with ThreadPoolExecutor() as pool:
            raw_stats = await loop.run_in_executor(pool, get_key_stats_data, stock['ticker'])
            structured_stats = await loop.run_in_executor(pool, generate_keystats_report, raw_stats)
        return stock['ticker'], structured_stats
    except Exception as e:
        return stock['ticker'], {"error": str(e)}

async def run_workflow_streaming():
    """Runs the stock analysis workflow and yields events for SSE."""
    # 1. Initial event
    yield {"event": "start", "message": "Starting to fetch trending stocks..."}

    # 2. Fetch trending stocks
    raw_data = find_trending_stocks_data()
    structured_report = generate_stock_report(raw_data)
    trending_stocks = structured_report['stocks']
    yield {"event": "trending_stocks", "data": trending_stocks}

    # 3. Fetch key stats in parallel
    tasks = [fetch_stats_for_stock(stock) for stock in trending_stocks]
    for future in asyncio.as_completed(tasks):
        ticker, stats = await future
        yield {"event": "key_stat", "ticker": ticker, "data": stats}

    # 4. Final event
    print("Workflow completed.")
    yield {"event": "end", "message": "Workflow completed."}

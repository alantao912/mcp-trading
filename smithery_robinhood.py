import mcp
from mcp.client.streamable_http import streamablehttp_client
import asyncio
import json
import os

SMITHERY_API_KEY = "7bbc003f-9f83-416b-966a-14e49d3e73b3"
PROFILE = "coming-toucan-igPIzg"
URL = f"https://server.smithery.ai/@joshuajerin/trading-mcp/mcp?api_key={SMITHERY_API_KEY}&profile={PROFILE}"

PORTFOLIO_PATH = os.path.join(os.path.dirname(__file__), 'portfolio.json')

def load_mock_portfolio():
    with open(PORTFOLIO_PATH, 'r') as f:
        return json.load(f)

# Track demo login state in memory (for hackathon/demo only)
demo_logged_in = False

def is_demo_login(username, password):
    return username == 'srishti' and password == 'test1234'

async def list_tools():
    async with streamablehttp_client(URL) as (read_stream, write_stream, _):
        async with mcp.ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            return [t.name for t in tools_result.tools]

async def initiate_login(username=None, password=None):
    global demo_logged_in
    print(f"Login attempt: username={username}, password={password}")
    demo_logged_in = False  # Always reset before checking
    if is_demo_login(username, password):
        print("Demo login successful")
        demo_logged_in = True
        return {"status": "connected (demo)", "demo": True}
    print("Real login attempted")
    async with streamablehttp_client(URL) as (read_stream, write_stream, _):
        async with mcp.ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool('initiate_login', {'username': username, 'password': password})
            # Only return success if real API returns a success status
            if not result or 'error' in result or result.get('status') != 'connected':
                print("Real login failed or invalid credentials")
                return {"error": "Invalid credentials or login failed"}
            print("Real login successful")
            return result

async def logout():
    global demo_logged_in
    demo_logged_in = False
    async with streamablehttp_client(URL) as (read_stream, write_stream, _):
        async with mcp.ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool('logout', {})
            return result

async def get_portfolio():
    print(f"get_portfolio: demo_logged_in={demo_logged_in}")
    if demo_logged_in:
        print("Returning mock portfolio")
        return load_mock_portfolio()
    async with streamablehttp_client(URL) as (read_stream, write_stream, _):
        async with mcp.ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool('get_portfolio', {})
            return result

# Example usage
if __name__ == "__main__":
    tools = asyncio.run(list_tools())
    print("Available tools:", tools) 
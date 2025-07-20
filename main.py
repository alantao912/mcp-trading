from fastapi import FastAPI, Request
import uvicorn
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from smithery_robinhood import list_tools, initiate_login, logout, get_portfolio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/robinhood/tools")
async def get_tools():
    tools = await list_tools()
    return {"tools": tools}

@app.post("/api/robinhood/connect")
async def connect_robinhood(request: Request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return {"error": "Username and password required"}
    result = await initiate_login(username, password)
    return result

@app.post("/api/robinhood/disconnect")
async def disconnect_robinhood():
    result = await logout()
    return result

@app.get("/api/robinhood/portfolio")
async def robinhood_portfolio():
    result = await get_portfolio()
    return result

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

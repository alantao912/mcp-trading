import os
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END
import json
from pathlib import Path
from langchain_community.document_loaders import JSONLoader
from langchain.agents import AgentExecutor, create_json_chat_agent # You might need to import JsonSpec as well depending on your setup
from langchain_community.chat_models import ChatOpenAI # Or your preferred chat model
from langchain.prompts import PromptTemplate
from langchain_community.agent_toolkits import JsonToolkit
from langchain_community.tools.json.tool import JsonSpec
from langchain_community.agent_toolkits.json.base import create_json_agent
from langchain.chat_models import init_chat_model

# -- load keys from env --
load_dotenv()  # Load environment variables from .env file
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
openrouter_base_url = os.getenv("OPENROUTER_BASE_URL")

# -- initialize llm --
llm = init_chat_model(
model="openai:gpt-4.1",  # or "openai:gpt-4o" for GPT-4o
    temperature=0,
    api_key=openrouter_api_key,
    base_url=openrouter_base_url)

# -- class to handle portfolio queries --
class Portfolio():
    def __init__(self):
        # Initialize session and client objects
        self.file_path: str = 'portfolio.json'
        
    def getPortfolioData(self):
        try:
            with open(self.file_path, 'r') as file:
                data = json.load(file)

            json_spec = JsonSpec(dict_=data, max_value_length=4000)
            json_toolkit = JsonToolkit(spec=json_spec)

            json_agent_executor = create_json_agent(
                llm,  # Replace with your desired LLM
                toolkit=json_toolkit,
                verbose=True
            )
            response = json_agent_executor.run("how should be the asset allocation done provide excact percentage details?")
            return response
        except Exception as e:
            print('\n Error reading json file', e)


if __name__ == '__main__':
    try:
        userPortfolio = Portfolio()
        print(userPortfolio.getPortfolioData())
    except Exception as e:
        print('\n Error getting json/llm response', e)

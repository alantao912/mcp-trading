from pydantic import BaseModel, Field
from typing import List

class StockAnalysis(BaseModel):
    """
    A detailed analysis for a single stock, including a summary of its outlook
    and a recommendation based on the user's query.
    """
    ticker: str = Field(description="The stock ticker symbol.")
    analysis: str = Field(description="A detailed analysis of the stock based on its key stats and recent news.")
    recommendation: str = Field(description="A specific recommendation for the stock (e.g., 'buy', 'sell', 'hold') based on the user's query, with justification.")

class FinalReport(BaseModel):
    """
    A final, comprehensive report that synthesizes all gathered information
    to provide a market overview and answer a user's specific query.
    """
    market_overview: str = Field(description="A high-level overview of the current market trends based on the trending stocks.")
    detailed_analysis: List[StockAnalysis] = Field(description="A list of detailed analyses for each of the trending stocks.")
    final_summary: str = Field(description="A concluding summary that directly answers the user's query, drawing from the individual stock analyses.")
    disclaimer: str = Field(description="A disclaimer stating that this is not financial advice.")

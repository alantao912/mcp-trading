from pydantic import BaseModel, Field
from typing import List

class Stock(BaseModel):
    """Represents a single trending stock."""
    ticker: str = Field(description="The stock ticker symbol (e.g., 'GOOGL').")
    name: str = Field(description="The full name of the company (e.g., 'Alphabet Inc.').")
    reason_for_trending: str = Field(description="A brief explanation of why the stock is currently trending.")

class TrendingStocksReport(BaseModel):
    """The root model for the trending stocks report."""
    stocks: List[Stock] = Field(description="A list of the top 10 trending stocks.")

def from_json_string(json_string: str) -> TrendingStocksReport:
    """Construct TrendingStocksReport from a JSON string."""
    return TrendingStocksReport.model_validate_json(json_string)
import json

def get_portfolio_holdings():
    """
    Loads portfolio data from portfolio.json.
    """
    print("--- [AGENT] Loading portfolio holdings ---")
    try:
        with open('portfolio.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("--- [AGENT] portfolio.json not found, returning empty portfolio ---")
        return {"holdings": [], "cash": 0.0}
    except json.JSONDecodeError:
        print("--- [AGENT] Error decoding portfolio.json, returning empty portfolio ---")
        return {"holdings": [], "cash": 0.0}

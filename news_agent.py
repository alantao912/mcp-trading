from bs4 import BeautifulSoup as bs
from dotenv import load_dotenv
from googlesearch import search
from models.stock_report import from_json_string, TrendingStocksReport
import json
from openai import OpenAI
import os
import re
import requests

load_dotenv()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0'
}

def get_all_p_tags(link: str) -> str:
    page = requests.get(link, headers=headers)
    tree = bs(page.text, features='html.parser')
    p_tags = tree.find_all('p')
    text = ''
    for tag in p_tags:
        text += tag.text
        text += ' '
    return text

def generate_summaries(page: str) -> str:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv('OPENROUTER_API_KEY')
    )

    completion = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=[
            {
                "role": "user",
                "content": "Shorten the following article, which may contain messy extra text:\n\n{}".format(page)
            }
        ]
    )

    return (completion.choices[0].message.content)

def get_news_for_stock(stock_ticker: str) -> list:
    """Fetches and summarizes news articles for a single stock ticker."""
    list_item_regex = re.compile(".*story-item.*")
    url = f"https://www.finance.yahoo.com/quote/{stock_ticker}/news"
    print(f"--- Fetching news for {stock_ticker} from {url} ---")
    
    try:
        page = requests.get(url, headers=headers)
        page.raise_for_status() # Raise an exception for bad status codes
        tree = bs(page.text, 'html.parser')
        story_items = tree.find_all('li', class_=list_item_regex)
        
        article_summaries = []
        first_n = 3 # Limit to 3 articles to be faster
        
        for story_item in story_items:
            if len(article_summaries) >= first_n:
                break
            
            story_title_tag = story_item.find('h3', class_=re.compile("clamp .*"))
            story_link_tag = story_item.find('a', class_=re.compile("subtle-link.*"))
            
            if story_title_tag and story_link_tag:
                story_title = story_title_tag.get_text(strip=True)
                story_link = story_link_tag.get('href')
                if not story_link.startswith('http'):
                    story_link = f"https://finance.yahoo.com{story_link}"
                
                print(f"--- Summarizing article: {story_title} ---")
                page_text = get_all_p_tags(story_link)
                if page_text:
                    page_summary = generate_summaries(page_text)
                    summary_item = {
                        "title": story_title,
                        "summary": page_summary
                    }
                    article_summaries.append(summary_item)

        return article_summaries
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news for {stock_ticker}: {e}")
        return [] # Return empty list on error

def get_news_for_stocks_parallel(stocks: list) -> dict:
    """Fetches news for a list of stocks in parallel."""
    all_news = {}
    with ThreadPoolExecutor(max_workers=len(stocks)) as executor:
        future_to_ticker = {executor.submit(get_news_for_stock, stock['ticker']): stock['ticker'] for stock in stocks}
        for future in future_to_ticker:
            ticker = future_to_ticker[future]
            try:
                news_items = future.result()
                all_news[ticker] = news_items
            except Exception as e:
                print(f"Error fetching news for {ticker}: {e}")
                all_news[ticker] = {"error": str(e)}
    return all_news

def query(inputs: TrendingStocksReport):
    """Main query function to fetch news for a report of trending stocks."""
    return get_news_for_stocks_parallel(inputs.stocks)
        

def main():
    input_json = None
    stock_data = None
    with open('sample_response.json', 'r') as f:
        input_json = f.read()
        stock_report = from_json_string(input_json)
        result = query(stock_report)
        print(result)
    

if __name__ == "__main__":
    main()
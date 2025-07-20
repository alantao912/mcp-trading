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

def query(inputs: TrendingStocksReport):
    list_item_regex = re.compile(".*story-item.*")
    url = "https://www.finance.yahoo.com/quote/{}/news"
    results = []
    first_n = 5
    for stock in inputs.stocks:
        page = requests.get(url.format(stock.ticker), headers=headers)
        tree = bs(page.text, features='html.parser')
        story_items = tree.find_all('li', class_=list_item_regex)

        article_summaries = []
        for story_item in story_items:
            story_title = story_item.find('h3', class_=re.compile("clamp .*"))
            story_link = story_item.find('a', class_=re.compile("subtle-link fin-size-small titles.*")).get('href')
            page_text = get_all_p_tags(story_link)
            page_summary = generate_summaries(page_text)
            summary_item = {
                "title": story_title,
                "summary": page_summary
            }
            article_summaries.append(summary_item)
            if len(article_summaries) >= first_n:
                break
        result = {
            'ticker': stock.ticker,
            'name': stock.name,
            'summaries': article_summaries
        }
        results.append(result)
    return results
        

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
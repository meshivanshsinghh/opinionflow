import os
import json
import asyncio
import httpx
from typing import List, Dict
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import re

load_dotenv()

BRIGHT_DATA_API_KEY = os.getenv("BRIGHT_DATA_API_KEY")
BRIGHT_DATA_ZONE = "opinionflow_serp_zone"

# Proxy-based access credentials
PROXY_USERNAME = os.getenv("BRIGHT_DATA_USERNAME")
PROXY_PASSWORD = os.getenv("BRIGHT_DATA_PASSWORD")
PROXY_HOST = "brd.superproxy.io"
PROXY_PORT = "33335"


class BrightDataClient:

    def __init__(self):
        if not PROXY_PASSWORD:
            raise ValueError("BRIGHT_DATA_PASSWORD not found")

        self.proxy_url = f"http://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}"

    async def discover(self, product: str) -> Dict[str, List[str]]:
        stores = {
            "amazon": f"{product} site:amazon.com",
            "walmart": f"{product} site:walmart.com",
            "target": f"{product} site:target.com"
        }

        patterns = {
            "amazon": r'amazon\.com.*/(dp|gp/product)/[A-Z0-9]{10}',
            "walmart": r'walmart\.com/ip/[^/]+/\d+',
            "target": r'target\.com/p/[^/]+/-/A-\d+'
        }

        results = {}

        for store_name, query in stores.items():
            try:
                async with httpx.AsyncClient(
                    proxies={
                        "http://": self.proxy_url,
                        "https://": self.proxy_url
                    },
                    verify=False
                ) as client:
                    response = await client.get(
                        f"https://www.google.com/search",
                        params={"q": query},
                        timeout=30.0
                    )

                    if response.status_code == 200:
                        text = response.text

                        # assigning to bs4
                        soup = BeautifulSoup(text, "html.parser")

                        # looking for all links in google search
                        all_links = [a.get('href') for a in soup.select('a[href]')
                                     if a.get('href') and a.get('href').startswith('http')]

                        product_urls = []
                        # filtering links for current store
                        for url in all_links:
                            if re.search(patterns.get(store_name, ''), url):
                                # cleaning utm and tracking parameters
                                clean_url = url.split(
                                    '&utm_')[0].split('?utm_')[0]
                                if clean_url not in product_urls:
                                    product_urls.append(clean_url)

                        results[store_name] = product_urls[:3]

                    else:
                        results[store_name] = []

            except Exception as e:
                print(f"Error discovering URLs for {store_name}: {str(e)}")
                results[store_name] = []

        return results


async def test():
    client = BrightDataClient()
    urls = await client.discover("azzaro perfume")
    print(json.dumps(urls, indent=2))

if __name__ == "__main__":
    asyncio.run(test())

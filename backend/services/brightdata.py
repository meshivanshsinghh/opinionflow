from backend.core.config import get_settings
from backend.core.exceptions import ExtractionError
from backend.utils.retry import with_retry
import httpx
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional


class BrightDataClient:

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.BRIGHT_DATA_API_KEY
        self.username = settings.BRIGHT_DATA_USERNAME
        self.password = settings.BRIGHT_DATA_PASSWORD
        self.serp_zone = settings.BRIGHT_DATA_SERP_ZONE
        self.browser_zone = settings.BRIGHT_DATA_BROWSER_ZONE

        if not self.password:
            raise ValueError("BRIGHT_DATA_PASSWORD not found")

        self.proxy_url = f"http://{self.username}:{self.password}@brd.superproxy.io:22225"

    # making request
    @with_retry(max_retries=3)
    async def _make_request(self, url: str, params: Optional[Dict] = None) -> str:
        async with httpx.AsyncClient(
            proxies={"http://": self.proxy_url, "https://": self.proxy_url},
            verify=False,
            timeout=30.0
        ) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.text

    # discovering urls
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
                html = await self._make_request(
                    "https://www.google.com/search",
                    params={"q": query}
                )

                soup = BeautifulSoup(html, "html.parser")
                all_links = [
                    a.get('href') for a in soup.select('a[href]')
                    if a.get('href') and a.get('href').startswith('http')
                ]

                product_urls = []
                for url in all_links:
                    if re.search(patterns.get(store_name, ''), url):
                        clean_url = url.split('&utm_')[0].split('?utm_')[0]
                        if clean_url not in product_urls:
                            product_urls.append(clean_url)

                results[store_name] = product_urls[:3]

            except Exception as e:
                raise ExtractionError(store_name, query, str(e))

        return results

    async def get_browser_page(self, url: str) -> str:
        """Get page content using Web Unlocker"""
        try:
            return await self._make_request(url)
        except Exception as e:
            print(f"Error fetching page with Web Unlocker: {str(e)}")
            raise

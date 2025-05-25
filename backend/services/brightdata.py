from backend.core.config import get_settings
from backend.core.exceptions import ExtractionError
from backend.utils.retry import with_retry
import httpx
from bs4 import BeautifulSoup
import re
from typing import Dict, List
from urllib.parse import quote_plus
import json
import asyncio

class BrightDataClient:

    def __init__(self):
        settings = get_settings()

        self.api_key = settings.BRIGHT_DATA_API_KEY
        self.serp_zone = settings.BRIGHT_DATA_SERP_ZONE
        self.webunlocker_zone = settings.BRIGHT_DATA_WEBUNLOCKER_ZONE   

        # # Proxy based auth
        # self.host = settings.BRIGHT_DATA_HOST
        # self.port = settings.BRIGHT_DATA_PORT
        # # Serp zone credentials 
        # self.serp_username = settings.BRIGHT_DATA_SERP_USERNAME
        # self.serp_password = settings.BRIGHT_DATA_SERP_PASSWORD

        # # web unlocker credentials
        # self.webunlocker_username = settings.BRIGHT_DATA_WEBUNLOCKER_USERNAME
        # self.webunlocker_password = settings.BRIGHT_DATA_WEBUNLOCKER_PASSWORD
        
        # browser api credentials
        self.browserapi_username = settings.BRIGHT_DATA_BROWSER_API_USERNAME
        self.browserapi_password = settings.BRIGHT_DATA_BROWSER_API_PASSWORD
        
    @property
    def auth(self):
        return f"{self.browserapi_username}:{self.browserapi_password}"
    
    # making request
    @with_retry(max_retries=3)
    async def _make_request(self, url: str, zone: str, format: str = 'raw') -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                'https://api.brightdata.com/request',
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'zone': zone,
                    'url': url,
                    'format': format
                }
            )
            print(f"Response status: {response.status_code}")  
            if response.status_code != 200:
                print(f"Error response: {response.text}") 
                
            response.raise_for_status()
            return response.text

    # discovering urls
    async def discover(self, product: str) -> Dict[str, List[str]]:
        """Use SERP API to discover product URLs"""
        stores = {
            "amazon": f"{product} site:amazon.com",
            "walmart": f"{product} site:walmart.com",
            # "target": f"{product} site:target.com"
        }

        patterns = {
            "amazon": r'amazon\.com.*/(dp|gp/product)/[A-Z0-9]{10}',
            "walmart": r'walmart\.com/ip/[^/]+/\d+',
            # "target": r'target\.com/p/[^/]+/-/A-\d+'
        }

        async def search_store(store_name, query):
            try:
                encoded_query = quote_plus(query)
                search_url = f"https://www.google.com/search?q={encoded_query}"
                print(f"Searching for {store_name} products: {search_url}")

                response_text = await self._make_request(
                    url=search_url,
                    zone=self.serp_zone,
                    format='json'
                )

                response_data = json.loads(response_text)
                html_content = response_data.get('body', '')

                soup = BeautifulSoup(html_content, "html.parser")
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

                print(f"Found {len(product_urls)} URLs for {store_name}")
                return (store_name, product_urls[:3])
            except Exception as e:
                print(f"Error discovering {store_name} products: {str(e)}")
                return (store_name, [])

        # Prepare all search tasks
        tasks = [
            search_store(store_name, query)
            for store_name, query in stores.items()
        ]

        # Run all searches concurrently
        results = await asyncio.gather(*tasks)

        # Build the final results dict
        return {store: urls for store, urls in results}


    async def get_product_page(self, url: str) -> str:
        """Get product page content using Web Unlocker API"""
        try:
            response_text = await self._make_request(
                url=url,
                zone=self.webunlocker_zone,
                format='json'
            )
            
            # Parse JSON response
            response_data = json.loads(response_text)
            
            # Extract HTML from body
            html_content = response_data.get('body', '')
            
            if not html_content:
                raise Exception("No HTML content in response body")
                
            return html_content
            
        except Exception as e:
            print(f"Error fetching product page: {str(e)}")
            raise

from core.config import get_settings
from utils.retry import with_retry
import httpx
from bs4 import BeautifulSoup
import re
from typing import Dict, List
from urllib.parse import quote_plus
import json
import asyncio
import aiohttp

class BrightDataClient:

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.BRIGHT_DATA_API_KEY
        self.serp_zone = settings.BRIGHT_DATA_SERP_ZONE
        self.webunlocker_zone = settings.BRIGHT_DATA_WEBUNLOCKER_ZONE   
        
        self.session = None
    
    async def _ensure_session(self):
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
     
    async def __aenter__(self):
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    # making request
    @with_retry(max_retries=2)
    async def _make_request(self, url: str, zone: str, format: str = 'raw') -> str:
        await self._ensure_session()
        try:
            async with self.session.post(
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
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    response.raise_for_status()
                
                return await response.text()
        except Exception as e:
            await self.close()
            raise

    # discovering urls
    async def discover(self, product: str, max_per_store: int = 5) -> Dict[str, List[str]]:
        """Use SERP API to discover product URLs with timeout"""
        stores = {
            "amazon": f"{product} site:amazon.com",
            "walmart": f"{product} site:walmart.com",
        }

        patterns = {
            "amazon": r'amazon\.com.*/(dp|gp/product)/[A-Z0-9]{10}',
            "walmart": r'walmart\.com/ip/[^/]+/\d+',
        }

        async def search_store_with_timeout(store_name, query):
            try:
                async with asyncio.timeout(45):
                    return await self._search_store(store_name, query, max_per_store, patterns)
            except asyncio.TimeoutError:
                print(f"Search timeout for {store_name}")
                return (store_name, [])
            except Exception as e:
                print(f"Error searching {store_name}: {e}")
                return (store_name, [])

        tasks = [
            search_store_with_timeout(store_name, query)
            for store_name, query in stores.items()
        ]

        try:
            async with asyncio.timeout(60):
                results = await asyncio.gather(*tasks, return_exceptions=True)
        except asyncio.TimeoutError:
            print("Discovery phase timed out")
            return {}

        final_results = {}
        for result in results:
            if isinstance(result, Exception):
                print(f"Store search failed: {result}")
                continue
            if isinstance(result, tuple) and len(result) == 2:
                store, urls = result
                final_results[store] = urls

        return final_results

    async def _search_store(self, store_name, query, max_per_store, patterns):
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

            if not html_content:
                print(f"No HTML content received for {store_name}")
                return (store_name, [])

            soup = BeautifulSoup(html_content, "html.parser")
            all_links = [
                a.get('href') for a in soup.select('a[href]')
                if a.get('href') and a.get('href').startswith('http')
            ]

            product_urls = []
            pattern = patterns.get(store_name, '')
            
            for url in all_links:
                if pattern and re.search(pattern, url):
                    clean_url = url.split('&utm_')[0].split('?utm_')[0]
                    if clean_url not in product_urls:
                        product_urls.append(clean_url)
                        
                    if len(product_urls) >= max_per_store:
                        break

            print(f"Found {len(product_urls)} URLs for {store_name}")
            return (store_name, product_urls[:max_per_store])
        
        except Exception as e:
            print(f"Error discovering {store_name} products: {str(e)}")
            return (store_name, [])
    
    async def get_product_page(self, url: str) -> str:
        try:
            async with asyncio.timeout(25):
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
            
        except asyncio.TimeoutError:
            print(f"Timeout fetching product page: {url}")
            raise
        except Exception as e:
            print(f"Error fetching product page: {str(e)}")
            raise

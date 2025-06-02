from abc import ABC, abstractmethod
from models.product import Product
import httpx
from utils.retry import with_retry


class BaseProductExtractor(ABC):
    def __init__(self, proxy_url: str):
        self.proxy_url = proxy_url

    @abstractmethod
    async def extract_product_info(self, url: str) -> Product:
        pass

    @with_retry(max_retries=3)
    async def _fetch_page(self, url: str) -> str:
        async with httpx.AsyncClient(
            proxies={"http://": self.proxy_url, "https://": self.proxy_url},
            verify=False,
            timeout=30.0
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

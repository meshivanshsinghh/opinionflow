from typing import Dict, List, Optional
from backend.services.brightdata import BrightDataClient
from backend.extractors import WalmartExtractor, AmazonExtractor, TargetExtractor
from backend.models.product import Product
import asyncio
from datetime import datetime


class ProductService:
    def __init__(self, bright_data_client: Optional[BrightDataClient] = None):

        self.bright_data = bright_data_client or BrightDataClient()

        self.extractors = {
            "walmart": WalmartExtractor(self.bright_data.proxy_url),
            "amazon": AmazonExtractor(self.bright_data.proxy_url),
            "target": TargetExtractor(self.bright_data.proxy_url)
        }

        self.selected_products: Dict[str, Product] = {}

    def _detect_store(self, url: str) -> str:
        if "walmart.com" in url:
            return "walmart"
        elif "amazon.com" in url:
            return "amazon"
        elif "target.com" in url:
            return "target"
        raise ValueError("Unsupported store URL")

    async def discover_products(self, query: str, max_per_store: int = 3) -> Dict[str, List[Product]]:
        store_urls = await self.bright_data.discover(query)
        results = Dict[str, List[Product]] = {}

        for store, urls in store_urls.items():
            if store not in self.extractors:
                continue

            extractor = self.extractors[store]
            products = []

            for url in urls[:max_per_store]:
                try:
                    product = await extractor.extract_product_info(url)
                    products.append(product)
                except Exception as e:
                    print(f"Error extracting {store} product: {str(e)}")

            if products:
                results[store] = products

        return results

    async def add_custom_product(self, url: str) -> Product:
        try:
            store = self._detect_store(url)
            if store not in self.extractors:
                raise ValueError(f"Unsupported store: {store}")

            extractor = self.extractors[store]
            product = await extractor.extract_product_info(url)

            # udpating last_updated timestamp
            product.last_updated = datetime.now()

            return product

        except Exception as e:
            print(f"Error adding custom product {url}: {str(e)}")
            raise

    def select_product(self, store: str, product: Product) -> None:
        if store in self.selected_products:
            self.selected_products[store].is_selected = False

        # selecting new product
        product.is_selected = True
        self.selected_products[store] = Product

    def get_selected_products(self) -> Dict[str, Product]:
        return self.selected_products

    async def refresh_product(self, product: Product) -> Product:
        store = self._detect_store(str(product.url))
        extractor = self.extractors[store]

        updated_product = await extractor.extract_product_info(str(product.url))
        updated_product.is_selected = product.is_selected

        return updated_product

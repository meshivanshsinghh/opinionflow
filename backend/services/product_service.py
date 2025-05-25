import asyncio
from typing import Dict, List, Optional
from backend.services.brightdata import BrightDataClient
from backend.extractors import WalmartExtractor, AmazonExtractor
from backend.models.product import Product
from datetime import datetime
from backend.services.gemini import GeminiModel
from uuid import uuid4
from backend.services.pinecone_service import PineconeService

class ProductService:
    def __init__(
            self, 
            bright_data_client: Optional[BrightDataClient] = None,
            gemini_model: Optional[GeminiModel] = None,
            pinecone_service: Optional[PineconeService] = None
        ):

        self.bright_data = bright_data_client or BrightDataClient()
        self.gemini = gemini_model or GeminiModel()
        self.pinecone = pinecone_service or PineconeService()
        
        self.extractors = {
            "walmart": WalmartExtractor(self.bright_data),
            "amazon": AmazonExtractor(self.bright_data),
            # "target": TargetExtractor(self.bright_data)
        }
        self.selected_products = {}

    def _detect_store(self, url: str) -> str:
        if "walmart.com" in url:
            return "walmart"
        elif "amazon.com" in url:
            return "amazon"
        # elif "target.com" in url:
        #     return "target"
        raise ValueError("Unsupported store URL")

    async def discover_products(self, query: str, max_per_store: int = 5) -> Dict[str, List[Product]]:
        # checking cache first
        cached_results = await self.pinecone.search_discovery_cache(query)
        if cached_results:
            print(f"Cache hit for query: {query} (similarity: {cached_results['similarity_score']:.3f})")
            return self._convert_cached_to_products(cached_results["discovered_products"])

        # doing a fresh discovery
        store_urls = await self.bright_data.discover(query, max_per_store)
        all_products = []
        results: Dict[str, List[Product]] = {}

        # Prepare all extraction tasks
        extraction_tasks = []
        task_metadata = []

        for store, urls in store_urls.items():
            if store not in self.extractors:
                continue
            extractor = self.extractors[store]
            for url in urls[:max_per_store]:
                extraction_tasks.append(extractor.extract_product_info(url))
                task_metadata.append((store, url))

        # Run all extractions concurrently (once, after collecting all tasks)
        extraction_results = await asyncio.gather(*extraction_tasks, return_exceptions=True)

        # Organize results by store
        for (store, url), prod_dict in zip(task_metadata, extraction_results):
            if isinstance(prod_dict, Exception):
                print(f"Error extracting {store} product: {prod_dict}")
                continue
            
            
            prod_dict["id"] = str(uuid4())
            if store not in results:
                results[store] = []
            results[store].append(prod_dict)
            all_products.append(prod_dict)

        # 2. Batch Gemini call for all products
        gemini_specs = await self.gemini.batch_extract_specifications(all_products)
        for prod, specs in zip(all_products, gemini_specs):
            prod["specifications"] = specs

        # 3. Convert dicts to Product models for API response
        for store, products in results.items():
            results[store] = [
                Product(
                    id=prod["id"],
                    name=prod["name"],
                    url=prod["url"],
                    source=prod["source"],
                    price=prod["price"],
                    review_count=prod["review_count"],
                    last_scraped=prod["last_scraped"],
                    specifications=prod["specifications"],
                    rating=prod["rating"],
                    image_url=prod["image_url"],
                )
                for prod in products
                if prod.get("name") and prod.get("url")
            ]
            
        # caching the results
        products_for_cache = {}
        
        # 4. Cache the results
        for store, product_dicts in results.items():
            products_for_cache[store] = [
                {
                    "id": prod.id,
                    "name": prod.name,
                    "url": str(prod.url),
                    "source": prod.source,
                    "price": prod.price,
                    "review_count": prod.review_count,
                    "rating": prod.rating,
                    "image_url": prod.image_url,
                    "specifications": prod.specifications
                }
                for prod in product_dicts
            ]
        
        await self.pinecone.cache_discovery_results(query, products_for_cache)
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
    
    
    def _convert_cached_to_products(self, cached_products: Dict[str, List[Dict]]) -> Dict[str, List[Product]]:
        results = {}
        for store, products in cached_products.items():
            results[store] = [
                Product(
                    id=prod["id"],
                    name=prod["name"],
                    url=prod["url"],
                    source=prod["source"],
                    price=prod["price"],
                    review_count=prod["review_count"],
                    rating=prod["rating"],
                    image_url=prod["image_url"],
                    specifications=prod["specifications"]
                )
                for prod in products
            ]
        return results

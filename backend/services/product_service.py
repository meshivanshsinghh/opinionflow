import asyncio
from typing import Dict, List, Optional
from services.brightdata import BrightDataClient
from extractors import WalmartExtractor, AmazonExtractor
from models.product import Product
from datetime import datetime
from services.gemini import GeminiModel
from uuid import uuid4
from services.pinecone_service import PineconeService
from fastapi import HTTPException

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
        }
        self.selected_products = {}
        self.product_store = {}
        self.extraction_semaphore = asyncio.Semaphore(6)
        self.gemini_semaphore = asyncio.Semaphore(3)  

    def _detect_store(self, url: str) -> str:
        if "walmart.com" in url:
            return "walmart"
        elif "amazon.com" in url:
            return "amazon"
        raise ValueError("Unsupported store URL")


    # discover products
    async def discover_products_fast(self, query: str, max_per_store: int = 5) -> Dict[str, List[Product]]:
        """Fast discovery that returns products immediately without specifications"""
        try:
            async with asyncio.timeout(60):
                return await self._discover_products_fast_impl(query, max_per_store)
        except asyncio.TimeoutError:
            raise HTTPException(status_code=408, detail="Discovery request timed out")

    async def _discover_products_fast_impl(self, query: str, max_per_store: int = 5) -> Dict[str, List[Product]]:
        cached_results = await self.pinecone.search_discovery_cache_exact(query)
        if cached_results:
            print(f"Exact cache hit for query: {query} (similarity: {cached_results['similarity_score']:.3f})")
            return self._convert_cached_to_products(cached_results["discovered_products"])

        try:
            store_urls = await self.bright_data.discover(query, max_per_store)
        except Exception as e:
            print(f"Error during discovery: {e}")
            return {}
            
        if not store_urls:
            print("No URLs found during discovery")
            return {}

        extraction_tasks = []
        task_metadata = []

        for store, urls in store_urls.items():
            if store not in self.extractors:
                continue
            extractor = self.extractors[store]
            for url in urls[:max_per_store]:
                task = self._extract_with_semaphore(extractor, url)
                extraction_tasks.append(task)
                task_metadata.append((store, url))

        if not extraction_tasks:
            print("No extraction tasks created")
            return {}

        try:
            async with asyncio.timeout(45):
                extraction_results = await asyncio.gather(*extraction_tasks, return_exceptions=True)
        except asyncio.TimeoutError:
            print("Some product extractions timed out, proceeding with partial results")
            extraction_results = [None] * len(extraction_tasks)

        results: Dict[str, List[Product]] = {}
        all_products = []
        
        for (store, url), prod_dict in zip(task_metadata, extraction_results):
            if isinstance(prod_dict, Exception) or prod_dict is None:
                print(f"Error/timeout extracting {store} product from {url}: {prod_dict}")
                continue
            
            if not isinstance(prod_dict, dict):
                print(f"Invalid product data format from {store}: {type(prod_dict)}")
                continue
            
            prod_dict["id"] = str(uuid4())
            prod_dict["specifications"] = {}
            if store not in results:
                results[store] = []
            results[store].append(prod_dict)
            all_products.append(prod_dict)

        if not all_products:
            print("No products successfully extracted")
            return results

        # Convert to Product objects and return immediately
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
                    specifications={},
                    rating=prod["rating"],
                    image_url=prod["image_url"],
                )
                for prod in products
                if prod.get("name") and prod.get("url")
            ]
            
            # Store products for later enhancement
            for i, product in enumerate(results[store]):
                original_data = products[i]
                self.product_store[product.id] = {
                    "product": product,
                    "raw_data": original_data
                }
        
        # Start background specification enhancement
        if all_products:
            asyncio.create_task(self._enhance_products_with_specs_background(query, all_products, results))
        
        return results

    async def _enhance_products_with_specs_background(self, query: str, products: List[dict], results: Dict[str, List[Product]]):
        try:
            async with asyncio.timeout(60):
                print(f"Starting background specification enhancement for {len(products)} products")
                gemini_specs = await self._batch_extract_with_chunking(products)
                
                # Update stored products with specifications
                for prod, specs in zip(products, gemini_specs):
                    prod["specifications"] = specs
                    
                    # Update the product in product_store
                    if prod["id"] in self.product_store:
                        self.product_store[prod["id"]]["product"].specifications = specs
                        self.product_store[prod["id"]]["raw_data"]["specifications"] = specs
                
                # Prepare data for caching
                products_for_cache = {}
                for store, product_list in results.items():
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
                            "specifications": next((p["specifications"] for p in products if p["id"] == prod.id), {})
                        }
                        for prod in product_list
                    ]
                
                # Cache the enhanced results
                await self.pinecone.cache_discovery_results_exact(query, products_for_cache)
                print(f"Background enhancement completed and cached for query: {query}")
                
        except asyncio.TimeoutError:
            print("Background specification enhancement timed out")
        except Exception as e:
            print(f"Error in background specification enhancement: {e}")
    
    async def _extract_with_semaphore(self, extractor, url):
        async with self.extraction_semaphore:
            try:
                async with asyncio.timeout(30):
                    return await extractor.extract_product_info(url)
            except asyncio.TimeoutError:
                print(f"Extraction timeout for URL: {url}")
                return None
            except Exception as e:
                print(f"Extraction error for URL {url}: {e}")
                return None
            
    async def _batch_extract_with_chunking(self, products, chunk_size=3):
        all_specs = []
        
        for i in range(0, len(products), chunk_size):
            chunk = products[i:i + chunk_size]
            try:
                async with self.gemini_semaphore:
                    specs = await self.gemini.batch_extract_specifications(chunk)
                    if len(specs) == len(chunk):
                        all_specs.extend(specs)
                    else:
                        print(f"Gemini returned wrong number of specs for chunk {i//chunk_size + 1}")
                        all_specs.extend([{}] * len(chunk))
            except Exception as e:
                print(f"Error processing chunk {i//chunk_size + 1}: {e}")
                all_specs.extend([{}] * len(chunk))
        
        return all_specs

    async def add_custom_product(self, url: str) -> Product:
        try:
            store = self._detect_store(url)
            if store not in self.extractors:
                raise ValueError(f"Unsupported store: {store}")

            extractor = self.extractors[store]
            
            async with asyncio.timeout(45):
                product = await extractor.extract_product_info(url)

            product.last_updated = datetime.now()

            return product

        except asyncio.TimeoutError:
            raise HTTPException(status_code=408, detail="Product extraction timed out")
        except Exception as e:
            print(f"Error adding custom product {url}: {str(e)}")
            raise

    def select_product(self, store: str, product: Product) -> None:
        if store in self.selected_products:
            self.selected_products[store].is_selected = False
        
        product.is_selected = True
        self.selected_products[store] = product

    def get_selected_products(self) -> Dict[str, Product]:
        return self.selected_products

    async def refresh_product(self, product: Product) -> Product:
        try:
            store = self._detect_store(str(product.url))
            extractor = self.extractors[store]

            async with asyncio.timeout(45):
                updated_product = await extractor.extract_product_info(str(product.url))
            
            updated_product.is_selected = product.is_selected
            return updated_product
            
        except asyncio.TimeoutError:
            raise HTTPException(status_code=408, detail="Product refresh timed out")
        except Exception as e:
            print(f"Error refreshing product: {e}")
            raise
    
    
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

    async def get_specifications_for_products(self, product_ids: List[str]) -> Dict[str, Dict]:
        enhanced_products = {}
        products_needing_specs = []
        for product_id in product_ids:
            if product_id in self.product_store:
                stored_product = self.product_store[product_id]["product"]
                if stored_product.specifications:
                    enhanced_products[product_id] = stored_product.specifications
                    print(f"Using cached specs for product {product_id}")
                else:
                    raw_data = self.product_store[product_id]["raw_data"]
                    products_needing_specs.append(raw_data)
                    print(f"Need to process specs for product {product_id}")
            else:
                print(f"Product {product_id} not found in store")
                enhanced_products[product_id] = {}
        
        if products_needing_specs:
            print(f"Processing specifications for {len(products_needing_specs)} products")
            try:
                specs = await self._batch_extract_with_chunking(products_needing_specs)
                
                for i, prod in enumerate(products_needing_specs):
                    spec_data = specs[i] if i < len(specs) else {}
                    enhanced_products[prod["id"]] = spec_data
                    
                    if prod["id"] in self.product_store:
                        self.product_store[prod["id"]]["product"].specifications = spec_data
                        self.product_store[prod["id"]]["raw_data"]["specifications"] = spec_data
                        
            except Exception as e:
                print(f"Error enhancing specifications: {e}")
                for prod in products_needing_specs:
                    enhanced_products[prod["id"]] = {}
        
        print(f"Returning specs for {len(enhanced_products)} products")
        return enhanced_products

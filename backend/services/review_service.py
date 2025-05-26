import asyncio
import re 
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from services.brightdata import BrightDataClient
from services.pinecone_service import PineconeService
from core.config import get_settings
import httpx
import json
from services.gemini import GeminiModel
from datetime import datetime, timedelta
from uuid import uuid4

class ReviewExtractionService: 
    def __init__(self):
        self.bright_data = BrightDataClient()
        self.pinecone = PineconeService()
        self.settings = get_settings()
        self.gemini = GeminiModel()
        
    # extracting reviews for product
    async def extract_reviews_for_products(
        self, 
        session_id: str, 
        selected_products: Dict[str, Dict],
    ) -> Dict[str, List[Dict]]:
        
        # checking the cache first
        try:
            cached_reviews = await self._check_review_cache(selected_products)
            if cached_reviews: 
                print(f"Review cache hit - storing reviews with session_id: {session_id}")
                
                # Store cached reviews in Pinecone with current session_id
                try:
                    for store, store_reviews in cached_reviews.items():
                        if store in selected_products:
                            product = selected_products[store]
                            
                            # Split reviews into smaller batches to avoid metadata size limits
                            batch_size = 10
                            for i in range(0, len(store_reviews), batch_size):
                                batch_reviews = store_reviews[i:i + batch_size]
                                
                                try:
                                    await self.pinecone.store_reviews(
                                        reviews=batch_reviews,
                                        session_id=session_id, 
                                        product_id=product["id"],
                                        store=store
                                    )
                                except Exception as e:
                                    print(f"Error storing review batch {i//batch_size + 1} for {store}: {e}")
                                    continue
                            
                    print(f"Successfully stored {sum(len(reviews) for reviews in cached_reviews.values())} cached reviews with session_id")
                    
                except Exception as e:
                    print(f"Error storing cached reviews with session_id: {e}")
                
                # Return cached reviews - NO need to cache again
                return cached_reviews
                
        except Exception as e:
            print(f"Error checking review cache: {e}")

        # extracting reviews concurrently (fresh extraction)
        print("No cache found - extracting fresh reviews")
        tasks = []
        for store, product in selected_products.items():
            if store == "amazon":
                tasks.append(self._extract_amazon_reviews(product))
                
            elif store == "walmart":
                tasks.append(self._extract_walmart_reviews(product))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # organizing results
        all_reviews = {}
        for (store, product), reviews in zip(selected_products.items(), results):
            if isinstance(reviews, Exception):
                print(f"Error extracting {store} reviews: {reviews}")
                all_reviews[store] = []
            else:
                all_reviews[store] = reviews[:100]
        
        # storing fresh reviews in pinecone
        try:
            for store, store_reviews in all_reviews.items():
                if store in selected_products:
                    product = selected_products[store]
                    
                    # Split reviews into smaller batches to avoid metadata size limits
                    batch_size = 10  # Process 10 reviews at a time
                    for i in range(0, len(store_reviews), batch_size):
                        batch_reviews = store_reviews[i:i + batch_size]
                        
                        try:
                            await self.pinecone.store_reviews(
                                reviews=batch_reviews,
                                session_id=session_id, 
                                product_id=product["id"],
                                store=store
                            )
                        except Exception as e:
                            print(f"Error storing review batch {i//batch_size + 1} for {store}: {e}")
                            continue
            
            print(f"Successfully stored {sum(len(reviews) for reviews in all_reviews.values())} fresh reviews with session_id")
            
        except Exception as e:
            print(f"Error storing fresh reviews: {e}")
        
        # Cache fresh reviews for future use (ONLY for fresh extractions)
        try:
            await self._cache_reviews(session_id, selected_products, all_reviews)
            print("Successfully cached fresh reviews for future use")
        except Exception as e:
            print(f"Error caching fresh review results: {e}")
        
        return all_reviews
    # async def extract_reviews_for_products(
    #     self, 
    #     session_id: str, 
    #     selected_products: Dict[str, Dict],
    # ) -> Dict[str, List[Dict]]:
        
    #     # checking the cache first
    #     try:
    #         cached_reviews = await self._check_review_cache(selected_products)
    #         if cached_reviews: 
    #             print(f"Review cache hit - storing reviews with session_id: {session_id}")
                
    #             # Store cached reviews in Pinecone with current session_id
    #             try:
    #                 for store, store_reviews in cached_reviews.items():
    #                     if store in selected_products:
    #                         product = selected_products[store]
                            
    #                         # Split reviews into smaller batches to avoid metadata size limits
    #                         batch_size = 10
    #                         for i in range(0, len(store_reviews), batch_size):
    #                             batch_reviews = store_reviews[i:i + batch_size]
                                
    #                             try:
    #                                 await self.pinecone.store_reviews(
    #                                     reviews=batch_reviews,
    #                                     session_id=session_id, 
    #                                     product_id=product["id"],
    #                                     store=store
    #                                 )
    #                             except Exception as e:
    #                                 print(f"Error storing review batch {i//batch_size + 1} for {store}: {e}")
    #                                 continue
                                
    #                 print(f"Successfully stored {sum(len(reviews) for reviews in cached_reviews.values())} cached reviews with session_id")
                    
    #             except Exception as e:
    #                 print(f"Error storing cached reviews with session_id: {e}")
                
    #             return cached_reviews
                
    #     except Exception as e:
    #         print(f"Error checking review cache: {e}")

    #     # extracting reviews concurrently (fresh extraction)
    #     tasks = []
    #     for store, product in selected_products.items():
    #         if store == "amazon":
    #             tasks.append(self._extract_amazon_reviews(product))
                
    #         elif store == "walmart":
    #             tasks.append(self._extract_walmart_reviews(product))
            
    #     results = await asyncio.gather(*tasks, return_exceptions=True)
        
    #     # organizing results
    #     all_reviews = {}
    #     for (store, product), reviews in zip(selected_products.items(), results):
    #         if isinstance(reviews, Exception):
    #             print(f"Error extracting {store} reviews: {reviews}")
    #             all_reviews[store] = []
    #         else:
    #             all_reviews[store] = reviews[:100]
        
    #     # storing in pinecone
    #     try:
    #         for store, store_reviews in all_reviews.items():
    #             if store in selected_products:
    #                 product = selected_products[store]
                    
    #                 # Split reviews into smaller batches to avoid metadata size limits
    #                 batch_size = 10  # Process 10 reviews at a time
    #                 for i in range(0, len(store_reviews), batch_size):
    #                     batch_reviews = store_reviews[i:i + batch_size]
                        
    #                     try:
    #                         await self.pinecone.store_reviews(
    #                             reviews=batch_reviews,
    #                             session_id=session_id, 
    #                             product_id=product["id"],
    #                             store=store
    #                         )
    #                     except Exception as e:
    #                         print(f"Error storing review batch {i//batch_size + 1} for {store}: {e}")
    #                         continue
            
    #         print(f"Successfully stored {sum(len(reviews) for reviews in all_reviews.values())} fresh reviews with session_id")
            
    #     except Exception as e:
    #         print(f"Error storing fresh reviews: {e}")
        
    #     # Cache aggregated results with reduced metadata
    #     try:
    #         await self._cache_reviews(session_id, selected_products, all_reviews)
    #     except Exception as e:
    #         print(f"Error caching aggregated review results: {e}")
        
    #     return all_reviews
    
    
    # extracting amazon reviews
    async def _extract_amazon_reviews(self, product: Dict) -> List[Dict]:
        """Extract Amazon reviews using Bright Data Scraper API"""
        try:
            clean_url = self._clean_amazon_url(product["url"])
            print(f"Starting Amazon review extraction for: {product['name']}")
            print(f"Cleaned URL: {clean_url}")
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                # Step 1: Trigger the scraping job
                response = await client.post(
                    "https://api.brightdata.com/datasets/v3/trigger",
                    headers={
                        "Authorization": f"Bearer {self.settings.BRIGHT_DATA_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json=[{"url": clean_url}],
                    params={
                        "dataset_id": "gd_le8e811kzy4ggddlq",
                        "include_errors": "true"
                    }
                )
                
                print(f"Amazon trigger response: {response.status_code}")
                response.raise_for_status()
                
                # Step 2: Get the snapshot ID
                trigger_result = response.json()
                snapshot_id = trigger_result.get("snapshot_id")
                
                if not snapshot_id:
                    print("No snapshot_id received from Amazon trigger")
                    return []
                
                print(f"Received snapshot_id: {snapshot_id}")
                
                # Step 3: Poll for results
                reviews_data = await self._poll_amazon_results(snapshot_id)
                
                # Step 4: Convert to standard format
                standardized_reviews = []
                for review in reviews_data[:100]:  # Limit to 100 reviews
                    if review.get("review_text"):
                        standardized_reviews.append({
                            "review_text": review.get("review_text", ""),
                            "title": review.get("review_header", ""),
                            "rating": review.get("rating", 0),
                            "review_date": review.get("review_posted_date", ""),
                            "helpful_votes": review.get("helpful_count", 0),
                            "product_name": product["name"],
                            "author_name": review.get("author_name", ""),
                            "verified_purchase": review.get("is_verified", False)
                        })
                
                print(f"Converted {len(standardized_reviews)} Amazon reviews to standard format")
                return standardized_reviews
                
        except Exception as e: 
            print(f"Error extracting Amazon reviews: {e}")
            return []
    
    # extracting walmart reviews
    async def _extract_walmart_reviews(self, product: Dict) -> List[Dict]:
        try:
            # Extract product ID and construct review URL
            product_id = self._extract_walmart_product_id(product["url"])
            if not product_id:
                print(f"Could not extract product ID from URL: {product['url']}")
                return []
            
            print(f"Extracting Walmart reviews for product ID: {product_id}")
            
            # Get first page to determine total pages
            first_page_url = f"https://www.walmart.com/reviews/product/{product_id}?entryPoint=viewAllReviewsBottom"
            first_page_html = await self.bright_data.get_product_page(first_page_url)
            total_pages = self._get_walmart_total_pages(first_page_html)
            print(f"Found {total_pages} total pages of reviews")
            max_pages = min(total_pages, 10)
            
            # Extract reviews from multiple pages concurrently
            page_tasks = []
            for page in range(1, max_pages + 1):
                page_url = f"https://www.walmart.com/reviews/product/{product_id}?entryPoint=viewAllReviewsBottom&page={page}"
                page_tasks.append(self._extract_walmart_page_reviews_bs(page_url, product["name"]))
            
            page_results = await asyncio.gather(*page_tasks, return_exceptions=True)
            
            # Flatten results
            all_reviews = []
            for page_num, page_reviews in enumerate(page_results, 1):
                if isinstance(page_reviews, Exception):
                    print(f"Error extracting page {page_num}: {page_reviews}")
                elif isinstance(page_reviews, list):
                    print(f"Page {page_num}: extracted {len(page_reviews)} reviews")
                    all_reviews.extend(page_reviews)
            
            print(f"Total Walmart reviews extracted: {len(all_reviews)}")
            return all_reviews[:100]  # Ensure max 100 reviews
            
        except Exception as e: 
            print(f"Error extracting Walmart reviews: {e}")
            return []
    
    async def _extract_walmart_page_reviews_bs(self, page_url: str, product_name: str) -> List[Dict]:
        try:
            html = await self.bright_data.get_product_page(page_url)
            soup = BeautifulSoup(html, "html.parser")
            
            reviews = []
            
            # Find all review containers - use more flexible selectors
            review_containers = soup.find_all("div", class_=lambda x: x and "overflow-visible" in x and "b--none" in x and "dark-gray" in x)
            
            # Alternative approach - look for containers that have the review structure
            if not review_containers:
                # Look for divs that contain the review date pattern
                review_containers = soup.find_all("div", class_="overflow-visible")
                review_containers = [container for container in review_containers if 
                                container.find("div", class_="f7 gray flex flex-auto flex-none-l tr tl-l justify-end justify-start-l")]
            
            print(f"Found {len(review_containers)} review containers on page")
            
            for container in review_containers:
                try:
                    review_data = self._parse_walmart_review_container(container, product_name)
                    if review_data:
                        reviews.append(review_data)
                except Exception as e:
                    print(f"Error parsing individual review: {e}")
                    continue
            
            return reviews
            
        except Exception as e:
            print(f"Error extracting page reviews: {e}")
            return []

    def _parse_walmart_review_container(self, container, product_name: str) -> Optional[Dict]:
        try:
            # Extract date - look for the date pattern more flexibly
            date_elem = container.find("div", class_=lambda x: x and "f7" in x and "gray" in x and "flex" in x and "justify-end" in x)
            if not date_elem:
                date_elem = container.find("div", class_="f7 gray flex flex-auto flex-none-l tr tl-l justify-end justify-start-l")
            review_date = date_elem.get_text(strip=True) if date_elem else ""
            
            # Extract reviewer name - look for span with f7 b mv0 classes
            name_elem = container.find("span", class_=lambda x: x and "f7" in x and "b" in x and "mv0" in x)
            if not name_elem:
                name_elem = container.find("span", class_="f7 b mv0")
            reviewer_name = name_elem.get_text(strip=True) if name_elem else ""
            
            # Extract rating (count the filled stars) - look for star container
            star_container = container.find("div", class_=lambda x: x and "w_ExHd" in x and "w_y6ym" in x)
            rating = 0
            if star_container:
                # Count filled stars (w_1jp4 class indicates filled star)
                filled_stars = star_container.find_all("svg", class_=lambda x: x and "w_1jp4" in x)
                rating = len(filled_stars)
            
            # Extract review title - look for h3 with specific classes
            title_elem = container.find("h3", class_=lambda x: x and "w_kV33" in x and "w_Sl3f" in x and "w_mvVb" in x)
            if not title_elem:
                title_elem = container.find("h3", class_="w_kV33 w_Sl3f w_mvVb f5 b")
            review_title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Extract review text - look for span with tl-m db-m classes
            text_container = container.find("span", class_=lambda x: x and "tl-m" in x and "db-m" in x)
            review_text = ""
            if text_container:
                # Remove any <b> tags and get clean text
                for b_tag in text_container.find_all("b"):
                    b_tag.decompose()
                review_text = text_container.get_text(strip=True)
            
            # Extract helpful votes - look for upvote button
            helpful_votes = 0
            upvote_buttons = container.find_all("button", {"aria-label": lambda x: x and "Upvote" in x})
            for upvote_button in upvote_buttons:
                vote_span = upvote_button.find("span", class_=lambda x: x and "ml1" in x and "f7" in x and "dark-gray" in x)
                if vote_span:
                    vote_text = vote_span.get_text(strip=True)
                    vote_match = re.search(r'\((\d+)\)', vote_text)
                    if vote_match:
                        helpful_votes = int(vote_match.group(1))
                        break
            
            # Extract verified purchase status
            verified_purchase = False
            verified_elems = container.find_all("span", class_=lambda x: x and "b" in x and "f7" in x and "dark-gray" in x)
            for elem in verified_elems:
                if "Verified Purchase" in elem.get_text():
                    verified_purchase = True
                    break
            
            # Only return review if we have essential data
            if review_text and rating > 0:
                return {
                    "review_text": review_text,
                    "title": review_title,
                    "rating": rating,
                    "review_date": review_date,
                    "helpful_votes": helpful_votes,
                    "product_name": product_name,
                    "reviewer_name": reviewer_name,
                    "verified_purchase": verified_purchase
                }
            
            # Debug: print what we found even if incomplete
            print(f"Incomplete review data - Text: {bool(review_text)}, Rating: {rating}, Name: {reviewer_name}")
            return None
            
        except Exception as e:
            print(f"Error parsing review container: {e}")
            return None
        
    def _extract_walmart_product_id(self, url: str) -> Optional[str]:
        """Extract product ID from Walmart URL - improved version"""
        # Handle both product page URLs and review URLs
        patterns = [
            r'/ip/[^/]+/(\d+)',  # Standard product page
            r'/reviews/product/(\d+)',  # Review page
            r'walmart\.com/ip/.*?/(\d+)'  # Flexible pattern
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        print(f"Could not extract product ID from URL: {url}")
        return None
    
    # checking reviews cache
    async def _check_review_cache(self, selected_products: Dict[str, Dict]) -> Optional[Dict[str, List[Dict]]]:
        """Check if reviews are cached for the exact product combination"""
        try:
            # Generate a more specific cache key
            cache_key = self._generate_cache_key(selected_products)
            print(f"🔍 Checking cache for key: {cache_key}")
            
            # Search for exact cache match in Pinecone
            cache_embedding = await self.pinecone._generate_embedding(cache_key)
            index = self.pinecone.pc.Index(self.settings.PINECONE_REVIEWS_INDEX)
            
            # Remove session_id dependency - search only by cache properties
            results = index.query(
                vector=cache_embedding,
                top_k=5,  # Get more results to check
                include_metadata=True,
                filter={
                    "is_cache": True,
                    "expires_at": {"$gt": datetime.now().timestamp()}
                }
            )
            
            print(f"🔍 Found {len(results.matches)} potential cache entries")
            
            # Check each result for exact cache key match
            for match in results.matches:
                stored_cache_key = match.metadata.get("cache_key", "")
                similarity_score = match.score
                
                print(f"🔍 Comparing cache keys:")
                print(f"   Stored: {stored_cache_key[:100]}...")
                print(f"   Looking for: {cache_key[:100]}...")
                print(f"   Similarity: {similarity_score}")
                
                # Check for exact match
                if stored_cache_key == cache_key:
                    cached_data = match.metadata.get("cached_reviews")
                    if cached_data:
                        print(f"✅ Exact cache key match! Score: {similarity_score}")
                        return json.loads(cached_data)
                elif similarity_score > 0.98:  # Very high similarity as fallback
                    cached_data = match.metadata.get("cached_reviews")
                    if cached_data:
                        print(f"✅ High similarity cache match! Score: {similarity_score}")
                        return json.loads(cached_data)
            
            print("❌ No matching cache found")
            return None
            
        except Exception as e:
            print(f"❌ Error checking review cache: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    # generating cache key
    def _generate_cache_key(self, selected_products: Dict[str, Dict]) -> str:
        """Generate a unique cache key for the product combination"""
        # Create a more detailed cache key
        key_parts = []
        for store in sorted(selected_products.keys()):
            product = selected_products[store]
            # Include both URL and product name for uniqueness
            key_parts.append(f"{store}:{product['url']}:{product['name']}")
        
        cache_key = "|".join(key_parts)
        print(f"🔑 Generated cache key: {cache_key}")
        return cache_key

    # caching review
    async def _cache_reviews(self, session_id: str, selected_products: Dict[str, Dict], reviews: Dict[str, List[Dict]]):
        """Cache reviews with detailed metadata"""
        try:
            cache_key = self._generate_cache_key(selected_products)
            cache_id = str(uuid4())
            
            print(f"💾 Caching reviews with key: {cache_key}")
            
            # Clean the reviews data before JSON serialization
            cleaned_reviews = {}
            for store, store_reviews in reviews.items():
                cleaned_reviews[store] = []
                for review in store_reviews[:50]:  # Limit to 50 reviews per store for caching
                    cleaned_review = {
                        "review_text": review.get("review_text", "")[:500],  # Truncate long reviews
                        "title": review.get("title", "")[:100],  # Truncate long titles
                        "rating": review.get("rating", 0),
                        "review_date": review.get("review_date", ""),
                        "helpful_votes": review.get("helpful_votes", 0),
                        "product_name": review.get("product_name", "")[:100],  # Truncate product name
                        "reviewer_name": review.get("reviewer_name", "")[:50],  # Truncate reviewer name
                        "verified_purchase": review.get("verified_purchase", False)
                    }
                    cleaned_reviews[store].append(cleaned_review)
            
            # Generate embedding for the cache key
            cache_embedding = await self.pinecone._generate_embedding(cache_key)
            index = self.pinecone.pc.Index(self.settings.PINECONE_REVIEWS_INDEX)
            
            # Store with detailed metadata
            metadata = {
                "cache_key": cache_key,
                "is_cache": True,
                "cached_reviews": json.dumps(cleaned_reviews),
                "timestamp": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=self.settings.CACHE_EXPIRY_DAYS)).timestamp(),
                "product_count": len(selected_products),
                "review_count": sum(len(store_reviews) for store_reviews in cleaned_reviews.values()),
                # Add product details for debugging
                "products_info": json.dumps({
                    store: {
                        "name": product["name"][:100],
                        "url": product["url"][:200]
                    }
                    for store, product in selected_products.items()
                })
            }
            
            index.upsert(vectors=[{
                "id": cache_id,
                "values": cache_embedding,
                "metadata": metadata
            }])
            
            print(f"✅ Successfully cached {sum(len(r) for r in cleaned_reviews.values())} reviews")
            
        except Exception as e:
            print(f"❌ Error caching review results: {e}")
            import traceback
            traceback.print_exc()   

    def _get_walmart_total_pages(self, html: str) -> int:
        """Parse pagination to get total pages"""
        soup = BeautifulSoup(html, "html.parser")
        
        # Look for the last page number in pagination
        pagination = soup.find("nav", {"aria-label": "pagination"})
        if not pagination:
            return 1
        
        # Find all page links
        page_links = pagination.find_all("a", {"data-automation-id": "page-number"})
        if not page_links:
            return 1
        
        # Get the highest page number
        max_page = 1
        for link in page_links:
            try:
                page_num = int(link.get_text(strip=True))
                max_page = max(max_page, page_num)
            except (ValueError, TypeError):
                continue
        
        return max_page
    
    async def _poll_amazon_results(self, snapshot_id: str, max_wait: int = 300) -> List[Dict]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for attempt in range(max_wait // 5):
                    print(f"Polling Amazon snapshot {snapshot_id}, attempt {attempt + 1}")
                    
                    response = await client.get(
                        f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}",
                        headers={"Authorization": f"Bearer {self.settings.BRIGHT_DATA_API_KEY}"},
                        params={"format": "json"}
                    )
                    
                    print(f"Snapshot status response: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            reviews_data = response.json()
                            
                            if isinstance(reviews_data, list) and len(reviews_data) > 0:
                                print(f"Successfully retrieved {len(reviews_data)} Amazon reviews")
                                return reviews_data
                            else:
                                print("Snapshot not ready yet, continuing to poll...")
                                
                        except json.JSONDecodeError as e:
                            print(f"JSON decode error: {e}")
                            print(f"Response text sample: {response.text[:200]}...")
                            
                    elif response.status_code == 404:
                        print("Snapshot not found or not ready yet")
                    elif response.status_code == 202:
                        print("Snapshot still processing...")
                    else:
                        print(f"Unexpected status code: {response.status_code}")
                        print(f"Response: {response.text}")
                    
                    await asyncio.sleep(10)  # Wait 10 seconds before next poll
                
                print(f"Amazon scraping timed out after {max_wait} seconds")
                return []
                
        except Exception as e:
            print(f"Error polling Amazon results: {e}")
            return []
        
    def _clean_amazon_url(self, url: str) -> str:
        # Extract the base product URL up to the ASIN
        match = re.search(r'(https://www\.amazon\.com/[^/]+/dp/[A-Z0-9]{10})', url)
        if match:
            return match.group(1)
        
        # Fallback: remove common tracking parameters
        base_url = url.split('?')[0].split('#')[0]
        return base_url
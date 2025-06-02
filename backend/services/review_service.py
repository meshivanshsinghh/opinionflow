from services.brightdata import BrightDataClient
from services.pinecone_service import PineconeService
from core.config import get_settings
from services.gemini import GeminiModel
import json 
import httpx
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import hashlib
import re
import asyncio 

class ReviewExtractionService:
    def __init__(self):
        self.bright_data = BrightDataClient()
        self.pinecone = PineconeService()
        self.settings = get_settings()
        self.gemini = GeminiModel()
        
        
    # extracting reviews for product
    async def extract_reviews_for_products(
        self, 
        selected_products: Dict[str, Dict],
    ) -> Dict[str, List[Dict]]:
        
        comparison_id = self._generate_comparison_id(selected_products)
        
        
        # checking if reviews already exists
        if await self.pinecone.check_comparison_exists(comparison_id):
            all_reviews = await self.pinecone.search_reviews_by_comparison(
                comparison_id=comparison_id,
                question="product reviews",
                top_k=1000
            )
            
            cached_reviews = {}
            for store in selected_products.keys():
                cached_reviews[store] = [r for r in all_reviews if r.get("store") == store][:100]
            
            return cached_reviews

        fresh_reviews = await self._extract_fresh_reviews(selected_products)
        try:
            await self._store_reviews_with_comparison_id(fresh_reviews, comparison_id, selected_products)
            
            total_reviews = sum(len(store_reviews) for store_reviews in fresh_reviews.values())
            await self.pinecone.cache_comparison_flag(comparison_id, total_reviews)
                        
        except Exception as e:
            print("Returning fresh reviews without caching due to storage failure")
        return fresh_reviews
        
    # generating comparison id
    def _generate_comparison_id(self, selected_products: Dict[str, Dict]) -> str:
        product_keys = []
        
        for store in sorted(selected_products.keys()):
            product = selected_products[store]
            product_id = product.get("id", "")
            product_keys.append(f"{store.strip()}_{product_id.strip()}")
        
        comparison_key = "|".join(product_keys)
        comparison_hash = hashlib.md5(comparison_key.encode()).hexdigest()[:16]
        
        return f"COMP_{comparison_hash}"
    
                
    # extracting fresh reviews
    async def _extract_fresh_reviews(self, selected_products: Dict[str, Dict]) -> Dict[str, List[Dict]]:
        tasks = []
        
        for store, product in selected_products.items(): 
            if store == "amazon":
                tasks.append(self._extract_amazon_reviews(product))
            elif store == "walmart":
                tasks.append(self._extract_walmart_reviews(product))
                
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # organizing results
        all_reviews = {}
        for(store, product), reviews in zip(selected_products.items(), results):
            if isinstance(reviews, Exception):
                print(f"Error extracting reviews for {store}: {reviews}")
                all_reviews[store] = []
            else:
                all_reviews[store] = reviews[:100]
                print(f"Successfully extractted {len(reviews)} reviews for {store}")
                
        return all_reviews
    
    
    async def _store_reviews_with_comparison_id(
        self, 
        reviews: Dict[str, List[Dict]],
        comparison_id: str, 
        selected_products: Dict[str, Dict]
    ):
        try:
            store_tasks = []
            
            for store, store_reviews in reviews.items():
                if store in selected_products and store_reviews:
                    product = selected_products[store]
                    store_tasks.append(
                        self._store_store_reviews(store_reviews, comparison_id, product["id"], store)
                    )
            
            results = await asyncio.gather(*store_tasks, return_exceptions=True)

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    store_name = list(reviews.keys())[i]
                    print(f"ERROR: Failed to store reviews for {store_name}: {result}")
                    raise result
            
        except Exception as e: 
            raise
    
    async def _store_store_reviews(self, store_reviews: List[Dict], comparison_id: str, product_id: str, store: str):
        try:
            batch_size = 50 
            batch_tasks = []
            
            for i in range(0, len(store_reviews), batch_size):
                batch_reviews = store_reviews[i:i + batch_size]
                batch_tasks.append(
                    self.pinecone.store_comparison_reviews(
                        reviews=batch_reviews, 
                        comparison_id=comparison_id, 
                        product_id=product_id,
                        store=store,
                    )
                )
            
            results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
            # Add error checking
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    raise result        
            
        except Exception as e:
            raise
        
        
    # ========== EXTRACTING AMAZON AND WALMART REVIEWS ============
    async def _extract_amazon_reviews(self, product: Dict) -> List[Dict]:
        try:
            clean_url = self._clean_amazon_url(product["url"])
            
            async with httpx.AsyncClient(timeout=120.0) as client: 
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
                trigger_result = response.json()
                snapshot_id = trigger_result.get("snapshot_id")
                
                if not snapshot_id:
                    print("No snaphsot_id received")
                    return []
                
                reviews_data = await self._poll_amazon_results(snapshot_id)
                
                standardized_reviews = []
                for review in reviews_data[:100]:
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
                        
                return standardized_reviews
        except Exception as e: 
            print(f"Error extracting amazon reviews: {e}")
            return []
        
        
        
    async def _extract_walmart_reviews(self, product: Dict) -> List[Dict]:
        try:
            product_id = self._extract_walmart_product_id(product["url"])
            if not product_id:
                return []
            
            first_page_url = f"https://www.walmart.com/reviews/product/{product_id}?entryPoint=viewAllReviewsBottom"
            first_page_html = await self.bright_data.get_product_page(first_page_url)
            total_pages = self._get_walmart_total_pages(first_page_html)
            max_pages = min(total_pages, 5)
            
            semaphore = asyncio.Semaphore(3)
            
            async def extract_page_with_semaphore(page):
                async with semaphore:
                    page_url = f"https://www.walmart.com/reviews/product/{product_id}?entryPoint=viewAllReviewsBottom&page={page}"
                    return await self._extract_walmart_page_reviews_bs(page_url, product["name"])
            
        
            page_tasks = [extract_page_with_semaphore(page) for page in range(1, max_pages + 1)]
            page_results = await asyncio.gather(*page_tasks, return_exceptions=True)

            all_reviews = []
            for page_num, page_reviews in enumerate(page_results, 1):
                if isinstance(page_reviews, Exception):
                    print(f"Error exxtracting page {page_num}")
                elif isinstance(page_reviews, list):
                    all_reviews.extend(page_reviews)
                    
            return all_reviews[:100]
                    
        except Exception as e: 
            print(f"Error extracting walmart reviews: {e}")
            return []
        
    # extracting page content
    async def _extract_walmart_page_reviews_bs(self, page_url: str, product_name: str) -> List[Dict]:
        try:
            html = await self.bright_data.get_product_page(page_url)
            soup = BeautifulSoup(html, "html.parser")
            reviews = []
            review_containers = soup.find_all("div", class_=lambda x: x and "overflow-visible" in x and "b--none" in x and "dark-gray" in x)
            
            if not review_containers:
                review_containers = soup.find_all("div", class_="overflow-visible")
                review_containers = [container for container in review_containers if 
                                container.find("div", class_="f7 gray flex flex-auto flex-none-l tr tl-l justify-end justify-start-l")]

            for container in review_containers:
                try:
                    review_data = self._parse_walmart_review_container(container, product_name)
                    if review_data:
                        reviews.append(review_data)
                except Exception as e:
                    continue
            
            return reviews
        
        except Exception as e:
            print(f"Error extracting page reviews: {e}")
            return []
        
    # cleaning and extracting walmart product id
    def _extract_walmart_product_id(self, url: str) -> Optional[str]:
        patterns = [
            r'/ip/[^/]+/(\d+)',
            r'/reviews/product/(\d+)',
            r'walmart\.com/ip/.*?/(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    # getting walmart total pages
    def _get_walmart_total_pages(self, html: str) -> int:
        soup = BeautifulSoup(html, "html.parser")
        
        pagination = soup.find("nav", {"aria-label": "pagination"})
        if not pagination:
            return 1
        
        page_links = pagination.find_all("a", {"data-automation-id": "page-number"})
        if not page_links:
            return 1
        
        max_page = 1
        for link in page_links:
            try:
                page_num = int(link.get_text(strip=True))
                max_page = max(max_page, page_num)
            except (ValueError, TypeError):
                continue
        
        return max_page
    
    # extrating walmart content scraping
    def _parse_walmart_review_container(self, container, product_name: str) -> Optional[Dict]:
        try:
            # extracting date
            date_elem = container.find("div", class_=lambda x: x and "f7" in x and "gray" in x and "flex" in x and "justify-end" in x)
            if not date_elem:
                date_elem = container.find("div", class_="f7 gray flex flex-auto flex-none-l tr tl-l justify-end justify-start-l")
            review_date = date_elem.get_text(strip=True) if date_elem else ""
            
            # extracting reviewer name
            name_elem = container.find("span", class_=lambda x: x and "f7" in x and "b" in x and "mv0" in x)
            if not name_elem:
                name_elem = container.find("span", class_="f7 b mv0")
            reviewer_name = name_elem.get_text(strip=True) if name_elem else ""
            
            # extracting rating
            star_container = container.find("div", class_=lambda x: x and "w_ExHd" in x and "w_y6ym" in x)
            rating = 0
            if star_container:
                filled_stars = star_container.find_all("svg", class_=lambda x: x and "w_1jp4" in x)
                rating = len(filled_stars)
            
            # extracting review title
            title_elem = container.find("h3", class_=lambda x: x and "w_kV33" in x and "w_Sl3f" in x and "w_mvVb" in x)
            if not title_elem:
                title_elem = container.find("h3", class_="w_kV33 w_Sl3f w_mvVb f5 b")
            review_title = title_elem.get_text(strip=True) if title_elem else ""
            
            # extracting review text
            text_container = container.find("span", class_=lambda x: x and "tl-m" in x and "db-m" in x)
            review_text = ""
            if text_container:
                for b_tag in text_container.find_all("b"):
                    b_tag.decompose()
                review_text = text_container.get_text(strip=True)
            
            # extracting helpful votes
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
            
            # extracting verified purchase status
            verified_purchase = False
            verified_elems = container.find_all("span", class_=lambda x: x and "b" in x and "f7" in x and "dark-gray" in x)
            for elem in verified_elems:
                if "Verified Purchase" in elem.get_text():
                    verified_purchase = True
                    break
            
            if review_text and rating > 0:
                return {
                    "review_text": review_text,
                    "title": review_title,
                    "rating": rating,
                    "review_date": review_date,
                    "helpful_votes": helpful_votes,
                    "product_name": product_name,
                    "author_name": reviewer_name,
                    "verified_purchase": verified_purchase
                }
            
            return None
            
        except Exception as e:
            print(f"Error parsing review container: {e}")
            return None
        
    # checking the status of snapshot and adding a poll mechanism
    async def _poll_amazon_results(self, snapshot_id: str, max_wait: int = 120) -> List[Dict]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                intervals = [2, 2, 3, 5, 5, 10, 10, 15, 15, 20]
                
                for i, interval in enumerate(intervals):
                    if sum(intervals[:i+1]) >= max_wait:
                        break
                
                    print(f"Polling Amazon snapshot {snapshot_id}, attempt {i + 1}")
                    
                    response = await client.get(
                        f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}",
                        headers={"Authorization": f"Bearer {self.settings.BRIGHT_DATA_API_KEY}"},
                        params={"format": "json"}
                    )
                    
                    if response.status_code == 200:
                        try:
                            reviews_data = response.json()
                            if isinstance(reviews_data, list) and len(reviews_data) > 0:
                                return reviews_data
                        except json.JSONDecodeError as e:
                            print(f"JSON decode error: {e}")
                
                    await asyncio.sleep(interval)
                
                return []
                
        except Exception as e:
            print(f"Error polling Amazon results: {e}")
            return []
        
    # cleaning amazon url
    def _clean_amazon_url(self, url: str) -> str:
        match = re.search(r'(https://www\.amazon\.com/[^/]+/dp/[A-Z0-9]{10})', url)
        if match:
            return match.group(1)
        
        base_url = url.split('?')[0].split('#')[0]
        return base_url
        
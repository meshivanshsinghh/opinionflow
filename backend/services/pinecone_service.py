from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
from uuid import uuid4
from pinecone import Pinecone, ServerlessSpec
from core.config import get_settings
from utils.retry import with_retry
import numpy as np
from huggingface_hub import InferenceClient

class PineconeService: 
    def __init__(self):
        self.settings = get_settings()
        self.pc = Pinecone(api_key=self.settings.PINECONE_API_KEY)
        self.embedding_dimension = 384
        self._indexes_initialized = False
        
        try:
            self.hf_client = InferenceClient(api_key=self.settings.HUGGINGFACE_API_KEY)
        except Exception as e:
            print(f'Error initializing HuggingFace client: {e}')
            self.hf_client = None
        
    async def _ensure_indexes_exist(self):
        if self._indexes_initialized:
            return
        
        existing_indexes = self.pc.list_indexes().names()
        
        # discovery cache index
        if self.settings.PINECONE_DISCOVERY_INDEX not in existing_indexes:
            self.pc.create_index(
                name=self.settings.PINECONE_DISCOVERY_INDEX,
                dimension=self.embedding_dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=self.settings.PINECONE_ENVIRONMENT
                )
            )
            
        # reviews index 
        if self.settings.PINECONE_REVIEWS_INDEX not in existing_indexes:
            self.pc.create_index(
                name=self.settings.PINECONE_REVIEWS_INDEX,
                dimension=self.embedding_dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=self.settings.PINECONE_ENVIRONMENT
                )
            )
        
        self._indexes_initialized = True
     
    async def _generate_embedding(self, text: str) -> List[float]:
        try:
            if self.hf_client:
                # Use HuggingFace InferenceClient for feature extraction
                result = self.hf_client.feature_extraction(
                    text, 
                    model="sentence-transformers/all-MiniLM-L6-v2"
                )
                
                # Convert result to list if it's numpy array or tensor
                if hasattr(result, 'tolist'):
                    embedding = result.tolist()
                else:
                    embedding = list(result)
                
                # Handle 2D array (batch dimension)
                if isinstance(embedding[0], list):
                    embedding = embedding[0]
                
                # Ensure correct dimension
                if len(embedding) > self.embedding_dimension:
                    embedding = embedding[:self.embedding_dimension]
                elif len(embedding) < self.embedding_dimension:
                    padding = [0.0] * (self.embedding_dimension - len(embedding))
                    embedding.extend(padding)
                
                return embedding
            else:
                print('error doing embedding')
                return self._simple_hash_embedding(text)
                    
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return self._simple_hash_embedding(text)
             
    def _simple_hash_embedding(self, text: str) -> List[float]:
        import hashlib
        
        # Create a simple but consistent embedding
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to float vector
        embedding = []
        for i in range(0, len(hash_bytes), 4):
            chunk = hash_bytes[i:i+4]
            if len(chunk) == 4:
                val = int.from_bytes(chunk, 'big') / (2**32)
                embedding.append(val)
        
        # Pad or truncate to desired dimension
        while len(embedding) < self.embedding_dimension:
            embedding.extend(embedding[:min(len(embedding), self.embedding_dimension - len(embedding))])
        
        return embedding[:self.embedding_dimension]
    
    def _is_expired(self, expires_at) -> bool: 
        if isinstance(expires_at, (int, float)):
            # Handle numeric timestamp
            return datetime.now().timestamp() > expires_at
        else:
            # Handle ISO string (fallback)
            expiry_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            return datetime.now(expiry_time.tzinfo) > expiry_time
    
    
    @with_retry(max_retries=3)
    async def search_discovery_cache_exact(self, query: str) -> Optional[Dict[str, Any]]:
        await self._ensure_indexes_exist()
        try:
            # Normalize the query for exact matching
            normalized_query = self._normalize_search_query(query)            
            index = self.pc.Index(self.settings.PINECONE_DISCOVERY_INDEX)
            current_timestamp = datetime.now().timestamp()
            
            # Use dummy vector with exact metadata filter
            results = index.query(
                vector=[0.0] * self.embedding_dimension,
                top_k=1,
                include_metadata=True,
                filter={
                    "normalized_query": normalized_query,
                    "expires_at": {"$gt": current_timestamp}
                }
            )
            
            if results.matches:
                match = results.matches[0]
                return {
                    "discovered_products": json.loads(match.metadata["discovered_products"]),
                    "cached_at": match.metadata["timestamp"],
                    "similarity_score": 1.0,
                }
                
            return None
            
        except Exception as e: 
            print(f"Error searching discovery cache: {e}")
            return None
    
    @with_retry(max_retries=3)
    async def cache_discovery_results_exact(self, query: str, products: Dict[str, List[Dict]]) -> str:
        await self._ensure_indexes_exist()
        try:
            normalized_query = self._normalize_search_query(query)
            cache_id = str(uuid4())
            
            current_time = datetime.now()
            expires_at_timestamp = (current_time + timedelta(days=self.settings.CACHE_EXPIRY_DAYS)).timestamp()
        
            index = self.pc.Index(self.settings.PINECONE_DISCOVERY_INDEX)
            
            dummy_embedding = [1.0] + [0.0] * (self.embedding_dimension - 1)
            
            index.upsert(vectors=[{
                "id": cache_id,
                "values": dummy_embedding,
                "metadata": {
                    "search_query": query, 
                    "normalized_query": normalized_query,
                    "timestamp": current_time.isoformat(),
                    "expires_at": expires_at_timestamp,
                    "discovered_products": json.dumps(products),
                    "product_count": sum(len(prods) for prods in products.values()),
                    "is_exact_cache": True
                }
            }])
            
            return cache_id
            
        except Exception as e:
            print(f"Error caching discovery results: {e}")
            raise
    
    @with_retry(max_retries=3)
    async def search_comparison_cache(self, comparison_id: str) -> Optional[Dict]:
        await self._ensure_indexes_exist()
        try:
            index = self.pc.Index(self.settings.PINECONE_REVIEWS_INDEX)
            
            # Query with exact comparison_id filter
            results = index.query(
                vector=[1.0] + [0.0] * (self.embedding_dimension - 1),
                top_k=1,
                include_metadata=True,
                filter={
                    "comparison_id": comparison_id,
                    "is_comparison_cache": True,
                    "expires_at": {"$gt": datetime.now().timestamp()}
                }
            )
            
            if results.matches:
                cached_data = results.matches[0].metadata.get("cached_reviews")
                if cached_data:
                    return json.loads(cached_data)

            return None
            
        except Exception as e:
            print(f"Error searching comparison cache: {e}")
            return None

    @with_retry(max_retries=3)
    async def cache_comparison_results(self, comparison_id: str, reviews: Dict[str, List[Dict]]) -> str:
        await self._ensure_indexes_exist()
        try:
            cache_id = str(uuid4())
            index = self.pc.Index(self.settings.PINECONE_REVIEWS_INDEX)
            
            
            
            # truncate review data to fit within size limits
            truncated_reviews = {}
            for store, store_reviews in reviews.items():
                truncated_reviews[store] = []
                for review in store_reviews:
                    truncated_review = {
                         "review_text": review.get("review_text", "")[:500],  # Truncate to 500 chars
                        "title": review.get("title", "")[:100],
                        "rating": review.get("rating", 0),
                        "review_date": review.get("review_date", ""),
                        "helpful_votes": review.get("helpful_votes", 0),
                        "product_name": review.get("product_name", "")[:100],
                        "author_name": review.get("author_name", "")[:50],
                        "verified_purchase": review.get("verified_purchase", False)
                    }
                    
                    truncated_reviews[store].append(truncated_review)

            dummy_embedding = [1.0] + [0.0] * (self.embedding_dimension - 1)
            
            # review_ids = []
            # for store_reviews in reviews.values():
            #     for review in store_reviews:
            #         if "id" in review: 
            #             review_ids.append(review["id"])
                        

            metadata = {
                "comparison_id": comparison_id,
                "is_comparison_cache": True,
                "cached_reviews": json.dumps(truncated_reviews),
                "timestamp": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=self.settings.CACHE_EXPIRY_DAYS)).timestamp(),
                "review_count": sum(len(store_reviews) for store_reviews in reviews.values())
            }
            
            index.upsert(vectors=[{
                "id": cache_id,
                "values": dummy_embedding,
                "metadata": metadata
            }])
            
            return cache_id
            
        except Exception as e:
            print(f"Error caching comparison results: {e}")
            raise

    @with_retry(max_retries=3)
    async def store_comparison_reviews(self, reviews: List[Dict], comparison_id: str, product_id: str, store: str) -> List[str]:
        await self._ensure_indexes_exist()
        try:
            index = self.pc.Index(self.settings.PINECONE_REVIEWS_INDEX)
            vectors = []
            review_ids = []
            
            for review in reviews:
                if not review.get("review_text"):
                    continue
                    
                review_id = str(uuid4())
                review_ids.append(review_id)
                
                # generating embedding for review content
                review_content = f"Title: {review.get('title', '')} Review: {review.get('review_text', '')}"
                embedding = await self._generate_embedding(review_content)
                
                # Clean metadata - truncate to prevent size issues
                metadata = {
                    "id": review_id,
                    "comparison_id": comparison_id,
                    "product_id": product_id,
                    "product_name": (review.get("product_name") or "")[:200],
                    "store": store,
                    "review_text": (review.get("review_text") or "")[:2000],
                    "title": (review.get("title") or "")[:200],
                    "rating": review.get("rating") or 0,
                    "author_name": review.get("author_name", "")[:100],
                    "verified_purchase": review.get("verified_purchase", False),
                    "timestamp": datetime.now().isoformat(),
                    "is_comparison_review": True
                }
                
                vectors.append({
                    "id": review_id,
                    "values": embedding,
                    "metadata": metadata
                })
            
            # Batch upsert (100 vectors at a time)
            for i in range(0, len(vectors), 100):
                batch = vectors[i:i + 100]
                index.upsert(vectors=batch)
            
            return review_ids
            
        except Exception as e:
            print(f"Error storing comparison reviews: {e}")
            raise

    @with_retry(max_retries=3)
    async def search_reviews_by_comparison(self, comparison_id: str, question: str, top_k: int = 1000) -> List[Dict]:
        await self._ensure_indexes_exist()
        try:
            
            question_embedding = await self._generate_embedding(question)
            index = self.pc.Index(self.settings.PINECONE_REVIEWS_INDEX)
            
            results = index.query(
                vector=question_embedding,
                top_k=top_k,
                include_metadata=True,
                filter={"comparison_id": comparison_id, "is_comparison_review": True}
            )
                        
            reviews = []
            for match in results.matches:
                review = {
                    "review_text": match.metadata.get("review_text", ""),
                    "title": match.metadata.get("title", ""),
                    "rating": match.metadata.get("rating", 0),
                    "store": match.metadata.get("store", ""),
                    "product_name": match.metadata.get("product_name", ""),
                    "similarity_score": match.score
                }
                reviews.append(review)
            
            return reviews
            
        except Exception as e:
            print(f"Error searching reviews by comparison: {e}")
            return []

    # ========== LEGACY SESSION-BASED METHODS (Keep for backward compatibility) ==========
    # @with_retry(max_retries=3)
    # async def store_reviews(self, reviews: List[Dict], session_id: str, product_id: str, store: str) -> List[str]:
    #     await self._ensure_indexes_exist()
    #     try:
    #         index = self.pc.Index(self.settings.PINECONE_REVIEWS_INDEX)
    #         vectors = []
    #         review_ids = []
            
    #         for review in reviews:
    #             if not review.get("review_text"):
    #                 continue
                    
    #             review_id = str(uuid4())
    #             review_ids.append(review_id)
                
    #             # Create review text for embedding
    #             review_content = f"Title: {review.get('title', '')} Review: {review.get('review_text', '')}"
    #             embedding = await self._generate_embedding(review_content)  # Add await
                
    #             # Clean metadata - ensure no null values
    #             metadata = {
    #                 "session_id": session_id,
    #                 "product_id": product_id,
    #                 "product_name": review.get("product_name") or "",
    #                 "store": store,
    #                 "review_text": review.get("review_text") or "",
    #                 "title": review.get("title") or "",
    #                 "rating": review.get("rating") or 0,
    #                 "review_date": review.get("review_date") or "",
    #                 "helpful_votes": review.get("helpful_votes") or 0,
    #                 "timestamp": datetime.now().isoformat()
    #             }
                
    #             vectors.append({
    #                 "id": review_id,
    #                 "values": embedding,
    #                 "metadata": metadata
    #             })
            
    #         # Batch upsert (100 vectors at a time)
    #         for i in range(0, len(vectors), 100):
    #             batch = vectors[i:i + 100]
    #             index.upsert(vectors=batch)
            
    #         return review_ids
            
    #     except Exception as e:
    #         print(f"Error storing reviews: {e}")
    #         raise
    
    # @with_retry(max_retries=3)
    # async def search_reviews_by_session(self, session_id: str, question: str, top_k: int = 20) -> List[Dict]:
    #     await self._ensure_indexes_exist()
    #     try:
    #         question_embedding = await self._generate_embedding(question)  # Add await
    #         index = self.pc.Index(self.settings.PINECONE_REVIEWS_INDEX)
            
    #         results = index.query(
    #             vector=question_embedding,
    #             top_k=top_k,
    #             include_metadata=True,
    #             filter={"session_id": session_id}
    #         )
            
    #         return [
    #             {
    #                 "review_text": match.metadata["review_text"],
    #                 "title": match.metadata["title"],
    #                 "rating": match.metadata["rating"],
    #                 "store": match.metadata["store"],
    #                 "product_name": match.metadata["product_name"],
    #                 "similarity_score": match.score
    #             }
    #             for match in results.matches
    #         ]
            
    #     except Exception as e:
    #         print(f"Error searching reviews: {e}")
    #         return []
    
    async def cleanup_expired_cache(self):
        await self._ensure_indexes_exist()
        try:
            index = self.pc.Index(self.settings.PINECONE_DISCOVERY_INDEX)
            
            # Query for expired entries
            current_time = datetime.now().isoformat()
            results = index.query(
                vector=[0] * self.embedding_dimension,
                top_k=10000,
                include_metadata=True,
                filter={"expires_at": {"$lt": current_time}}
            )
            
            if results.matches:
                expired_ids = [match.id for match in results.matches]
                index.delete(ids=expired_ids)
                print(f"Cleaned up {len(expired_ids)} expired cache entries")
                
        except Exception as e:
            print(f"Error cleaning up expired cache: {e}")
    
    def _normalize_search_query(self, query: str) -> str:
        # Convert to lowercase, remove extra spaces, sort words
        words = query.lower().strip().split()
        
        # removing common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'for', 'with'}
        filtered_words = [word for word in words if word not in stop_words]
        
        # sorting words for consistent ordering
        normalized = ' '.join(sorted(filtered_words))
        return normalized
    
    
    # cache comparison flag
    @with_retry(max_retries = 3)
    async def cache_comparison_flag(self, comparison_id: str, review_count: int) -> str:
        await self._ensure_indexes_exist()
        try:
            cache_id = str(uuid4())
            index = self.pc.Index(self.settings.PINECONE_REVIEWS_INDEX)
            
            dummy_embedding = [1.0] + [0.0] * (self.embedding_dimension - 1)
            
            metadata = {
                "comparison_id": comparison_id,
                "is_comparison_flag": True,  # Changed from cache to flag
                "review_count": review_count,
                "timestamp": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=self.settings.CACHE_EXPIRY_DAYS)).timestamp(),
            }
            
            index.upsert(vectors=[{
                "id": cache_id,
                "values": dummy_embedding,
                "metadata": metadata
            }])
            
            return cache_id
            
        except Exception as e:
            print(f"Error caching comparison flag: {e}")
            raise
        
    @with_retry(max_retries=3)
    async def check_comparison_exists(self, comparison_id: str) -> bool:
        await self._ensure_indexes_exist()
        try:
            index = self.pc.Index(self.settings.PINECONE_REVIEWS_INDEX)
            
            results = index.query(
                vector=[1.0] + [0.0] * (self.embedding_dimension - 1),
                top_k=1,
                include_metadata=True,
                filter={
                    "comparison_id": comparison_id,
                    "is_comparison_flag": True,
                    "expires_at": {"$gt": datetime.now().timestamp()}
                }
            )
            
            return len(results.matches) > 0
            
        except Exception as e:
            print(f"Error checking comparison exists: {e}")
            return False
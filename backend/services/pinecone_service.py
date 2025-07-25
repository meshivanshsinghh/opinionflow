from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
from uuid import uuid4
from pinecone import Pinecone, ServerlessSpec
from core.config import get_settings
from utils.retry import with_retry
from huggingface_hub import InferenceClient
import hashlib
import asyncio

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
                result = self.hf_client.feature_extraction(
                    text, 
                    model="sentence-transformers/all-MiniLM-L6-v2"
                )
                
                if hasattr(result, 'tolist'):
                    embedding = result.tolist()
                else:
                    embedding = list(result)
                
                #handling 2d array
                if isinstance(embedding[0], list):
                    embedding = embedding[0]
                
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
        
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        embedding = []
        for i in range(0, len(hash_bytes), 4):
            chunk = hash_bytes[i:i+4]
            if len(chunk) == 4:
                val = int.from_bytes(chunk, 'big') / (2**32)
                embedding.append(val)

        while len(embedding) < self.embedding_dimension:
            embedding.extend(embedding[:min(len(embedding), self.embedding_dimension - len(embedding))])
        
        return embedding[:self.embedding_dimension]
    
    def _is_expired(self, expires_at) -> bool: 
        if isinstance(expires_at, (int, float)):
            return datetime.now().timestamp() > expires_at
        else:
            expiry_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            return datetime.now(expiry_time.tzinfo) > expiry_time
    
    
    @with_retry(max_retries=3)
    async def search_discovery_cache_exact(self, query: str) -> Optional[Dict[str, Any]]:
        await self._ensure_indexes_exist()
        try:
            normalized_query = self._normalize_search_query(query)            
            index = self.pc.Index(self.settings.PINECONE_DISCOVERY_INDEX)
            current_timestamp = datetime.now().timestamp()
            
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
            
            truncated_reviews = {}
            for store, store_reviews in reviews.items():
                truncated_reviews[store] = []
                for review in store_reviews:
                    truncated_review = {
                         "review_text": review.get("review_text", "")[:500],
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
            
            batch_size = 50
            
            async def process_review_batch(review_batch):
                batch_vectors = []
                batch_ids = []

                embedding_tasks = []
                for review in review_batch:
                    if not review.get("review_text"):
                        continue
                    review_content = f"Title: {review.get('title', '')} Review: {review.get('review_text', '')}"
                    embedding_tasks.append(self._generate_embedding(review_content))
                
                embeddings = await asyncio.gather(*embedding_tasks, return_exceptions=True)
                
                for i, (review, embedding) in enumerate(zip(review_batch, embeddings)):
                    if isinstance(embedding, Exception):
                        continue
                    if not review.get("review_text"):
                        continue
                        
                    review_id = str(uuid4())
                    batch_ids.append(review_id)
                    
                    metadata = {
                        "id": review_id,
                        "comparison_id": comparison_id,
                        "product_id": product_id,
                        "product_name": (review.get("product_name") or "")[:200],
                        "store": store,
                        "review_text": (review.get("review_text") or "")[:1500],
                        "title": (review.get("title") or "")[:150],
                        "rating": review.get("rating") or 0,
                        "author_name": review.get("author_name", "")[:80],
                        "verified_purchase": review.get("verified_purchase", False),
                        "timestamp": datetime.now().isoformat(),
                        "is_comparison_review": True
                    }
                    
                    batch_vectors.append({
                        "id": review_id,
                        "values": embedding,
                        "metadata": metadata
                    })
                
                return batch_vectors, batch_ids
        
            batch_tasks = []
            for i in range(0, len(reviews), batch_size):
                batch = reviews[i:i + batch_size]
                batch_tasks.append(process_review_batch(batch))
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            failed_batches = 0
            for result in batch_results:
                if isinstance(result, Exception):
                    failed_batches += 1
                    continue
                batch_vectors, batch_ids = result
                vectors.extend(batch_vectors)
                review_ids.extend(batch_ids)

            if failed_batches > 0:
                print(f"WARNING: {failed_batches} batches failed during processing")
            
            if not vectors:
                raise Exception(f"No vectors to store for {store} - all batches failed")

            # Store vectors in smaller batches
            upsert_batch_size = 100
            failed_upserts = 0
            for i in range(0, len(vectors), upsert_batch_size):
                batch = vectors[i:i + upsert_batch_size]
                try:
                    index.upsert(vectors=batch)
                except Exception as e:
                    failed_upserts += 1
                    
            if failed_upserts > 0:
                raise Exception(f"{failed_upserts} upsert batches failed for {store}")
            
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
    
    async def cleanup_expired_cache(self):
        await self._ensure_indexes_exist()
        try:
            index = self.pc.Index(self.settings.PINECONE_DISCOVERY_INDEX)
            
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
        words = query.lower().strip().split()
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
                "is_comparison_flag": True,
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
        
    @with_retry(max_retries=3)
    async def search_discovery_cache_by_key(self, cache_key: str) -> Optional[Dict[str, Any]]:
        await self._ensure_indexes_exist()
        try:
            index = self.pc.Index(self.settings.PINECONE_DISCOVERY_INDEX)
            current_timestamp = datetime.now().timestamp()
            
            try:
                result = index.fetch(ids=[cache_key])
                if cache_key in result.vectors:
                    metadata = result.vectors[cache_key].metadata
                    if metadata.get("expires_at", 0) > current_timestamp:
                        return {
                            "discovered_products": json.loads(metadata["discovered_products"]),
                            "cached_at": metadata["timestamp"],
                            "similarity_score": 1.0,
                        }
            except Exception:
                pass
            
            return None
            
        except Exception as e: 
            print(f"Error searching discovery cache: {e}")
            return None
        
    @with_retry(max_retries=3)
    async def cache_discovery_results_by_key(self, cache_key: str, query: str, products: Dict[str, List[Dict]]) -> str:
        await self._ensure_indexes_exist()
        try:
            current_time = datetime.now()
            expires_at_timestamp = (current_time + timedelta(days=self.settings.CACHE_EXPIRY_DAYS)).timestamp()
        
            index = self.pc.Index(self.settings.PINECONE_DISCOVERY_INDEX)
            query_embedding = await self._generate_embedding(query)
            
            index.upsert(vectors=[{
                "id": cache_key,
                "values": query_embedding,
                "metadata": {
                    "search_query": query,
                    "cache_key": cache_key,
                    "timestamp": current_time.isoformat(),
                    "expires_at": expires_at_timestamp,
                    "discovered_products": json.dumps(products),
                    "product_count": sum(len(prods) for prods in products.values()),
                }
            }])
            
            return cache_key
            
        except Exception as e:
            print(f"Error caching discovery results: {e}")
            raise
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import uuid
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from core.config import get_settings
from utils.retry import with_retry

class PineconeService: 
    def __init__(self):
        self.settings = get_settings()
        self.pc = Pinecone(api_key=self.settings.PINECONE_API_KEY)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dimension = 384
        self._indexes_initialized = False
        
        # initializing indexes
        # asyncio.create_task(self._ensure_indexes_exist())
        
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
            
    # generating embedding
    def _generate_embedding(self, text:str) -> List[float]:
        return self.embedding_model.encode(text).tolist()
    
    def _is_expired(self, expires_at) -> bool: 
        if isinstance(expires_at, (int, float)):
            # Handle numeric timestamp
            return datetime.now().timestamp() > expires_at
        else:
            # Handle ISO string (fallback)
            expiry_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            return datetime.now(expiry_time.tzinfo) > expiry_time
    
    @with_retry(max_retries=3)
    async def search_discovery_cache(self, query: str) -> Optional[Dict[str, Any]]:
        await self._ensure_indexes_exist()
        try:
            query_embedding = self._generate_embedding(query)
            index = self.pc.Index(self.settings.PINECONE_DISCOVERY_INDEX)
            
            current_timestamp = datetime.now().timestamp()
            
            results = index.query(
                vector=query_embedding,
                top_k = 1,
                include_metadata=True,
                 filter={"expires_at": {"$gt": current_timestamp}}
            )
            
            if results.matches and results.matches[0].score >= self.settings.DISCOVERY_SIMILARITY_THRESHOLD:
                match = results.matches[0]
                if not self._is_expired(match.metadata["expires_at"]):
                    return {
                        "discovered_products": json.loads(match.metadata["discovered_products"]),
                        "cached_at": match.metadata["timestamp"],
                        "similarity_score": match.score
                    }

            return None
            
        except Exception as e: 
            print(f"Error searching discovery cache: {e}")
            return None
    
    @with_retry(max_retries=3)
    async def cache_discovery_results(self, query: str, products: Dict[str, List[Dict]]) -> str:
        await self._ensure_indexes_exist()
        try:
            query_embedding = self._generate_embedding(query)
            cache_id = str(uuid.uuid4())
            
            current_time = datetime.now()
            expires_at_timestamp = (current_time + timedelta(days=self.settings.CACHE_EXPIRY_DAYS)).timestamp()
        
            
            index = self.pc.Index(self.settings.PINECONE_DISCOVERY_INDEX)
            
            index.upsert(vectors=[{
                "id": cache_id,
                "values": query_embedding,
                "metadata": {
                    "search_query": query,
                    "timestamp": current_time.isoformat(),  # Keep as string for display
                    "expires_at": expires_at_timestamp,     # Store as number for filtering
                    "discovered_products": json.dumps(products),
                    "product_count": sum(len(prods) for prods in products.values())
                }
            }])
            
            return cache_id
            
        except Exception as e:
            print(f"Error caching discovery results: {e}")
            raise
        
     
    @with_retry(max_retries=3)
    async def store_reviews(self, reviews: List[Dict], session_id: str, product_id: str, store: str) -> List[str]:
        await self._ensure_indexes_exist()
        try:
            index = self.pc.Index(self.settings.PINECONE_REVIEWS_INDEX)
            vectors = []
            review_ids = []
            
            for review in reviews:
                if not review.get("review_text"):
                    continue
                    
                review_id = str(uuid.uuid4())
                review_ids.append(review_id)
                
                # Create review text for embedding
                review_content = f"Title: {review.get('title', '')} Review: {review.get('review_text', '')}"
                embedding = self._generate_embedding(review_content)
                
                # Clean metadata - ensure no null values
                metadata = {
                    "session_id": session_id,
                    "product_id": product_id,
                    "product_name": review.get("product_name") or "",  # Convert None to empty string
                    "store": store,
                    "review_text": review.get("review_text") or "",
                    "title": review.get("title") or "",  # Convert None to empty string
                    "rating": review.get("rating") or 0,
                    "review_date": review.get("review_date") or "",
                    "helpful_votes": review.get("helpful_votes") or 0,
                    "timestamp": datetime.now().isoformat()
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
            print(f"Error storing reviews: {e}")
            raise
    
    @with_retry(max_retries=3)
    async def search_reviews_by_session(self, session_id: str, question: str, top_k: int = 20) -> List[Dict]:
        await self._ensure_indexes_exist()
        try:
            question_embedding = self._generate_embedding(question)
            index = self.pc.Index(self.settings.PINECONE_REVIEWS_INDEX)
            
            results = index.query(
                vector=question_embedding,
                top_k=top_k,
                include_metadata=True,
                filter={"session_id": session_id}
            )
            
            return [
                {
                    "review_text": match.metadata["review_text"],
                    "title": match.metadata["title"],
                    "rating": match.metadata["rating"],
                    "store": match.metadata["store"],
                    "product_name": match.metadata["product_name"],
                    "similarity_score": match.score
                }
                for match in results.matches
            ]
            
        except Exception as e:
            print(f"Error searching reviews: {e}")
            return []
    
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
            
    @with_retry(max_retries=3)
    async def search_review_cache(self, cache_key: str) -> Optional[Dict[str, List[Dict]]]:
        await self._ensure_indexes_exist()
        try:
            cache_embedding = self._generate_embedding(cache_key)
            index = self.pc.Index(self.settings.PINECONE_REVIEWS_INDEX)
            
            results = index.query(
                vector=cache_embedding,
                top_k=1,
                include_metadata=True,
                filter={"cache_key": cache_key, "is_cache": True}
            )
            
            if results.matches and results.matches[0].score > 0.95:
                cached_data = results.matches[0].metadata.get("cached_reviews")
                if cached_data:
                    return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            print(f"Error searching review cache: {e}")
            return None

    @with_retry(max_retries=3)
    async def cache_review_results(self, cache_key: str, reviews: Dict[str, List[Dict]]) -> str:
        await self._ensure_indexes_exist()
        try:
            cache_id = str(uuid.uuid4())
            cache_embedding = self._generate_embedding(cache_key)
            index = self.pc.Index(self.settings.PINECONE_REVIEWS_INDEX)
            
            # Clean the reviews data before JSON serialization
            cleaned_reviews = {}
            for store, store_reviews in reviews.items():
                cleaned_reviews[store] = [
                    {
                        "review_text": review.get("review_text") or "",
                        "title": review.get("title") or "",
                        "rating": review.get("rating") or 0,
                        "review_date": review.get("review_date") or "",
                        "helpful_votes": review.get("helpful_votes") or 0,
                        "product_name": review.get("product_name") or ""
                    }
                    for review in store_reviews
                ]
            
            index.upsert(vectors=[{
                "id": cache_id,
                "values": cache_embedding,
                "metadata": {
                    "cache_key": cache_key,
                    "is_cache": True,
                    "cached_reviews": json.dumps(cleaned_reviews),
                    "timestamp": datetime.now().isoformat(),
                    "expires_at": (datetime.now() + timedelta(days=self.settings.CACHE_EXPIRY_DAYS)).timestamp()
                }
            }])
            
            return cache_id
            
        except Exception as e:
            print(f"Error caching review results: {e}")
            raise
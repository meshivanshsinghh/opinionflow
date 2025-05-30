import asyncio
from typing import Dict, List, Optional, Any
import json
import hashlib
from datetime import datetime
from services.pinecone_service import PineconeService
from services.gemini import GeminiModel
from core.config import get_settings

class AnalysisService:
    def __init__(self):
        self.pinecone = PineconeService()
        self.gemini = GeminiModel()
        self.settings = get_settings()
    
    async def analyze_reviews(self, selected_products: Dict[str, Dict]) -> Dict[str, Any]:
        try:
            comparison_id = self._generate_comparison_id(selected_products)
            all_reviews = await self._get_comparison_reviews(comparison_id)
            
            if not all_reviews:
                return {"error": "No reviews found for analysis"}
            
            # Perform parallel analysis
            tasks = [
                self._analyze_sentiment(all_reviews),
                self._extract_pros_cons(all_reviews),
                self._analyze_rating_distribution(all_reviews),
                self._extract_common_themes(all_reviews),
                self._generate_overall_summary(all_reviews, selected_products)
            ]
            
            sentiment, pros_cons, rating_dist, themes, summary = await asyncio.gather(*tasks)
            
            return {
                "comparison_id": comparison_id,
                "products": selected_products,
                "total_reviews": len(all_reviews),
                "sentiment_analysis": sentiment,
                "pros_cons": pros_cons,
                "rating_distribution": rating_dist,
                "common_themes": themes,
                "overall_summary": summary,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error in analysis: {e}")
            return {"error": str(e)}
    
    async def answer_question(self, question: str, selected_products: Dict[str, Dict]) -> Dict[str, Any]:
        try:
             
            comparison_id = self._generate_comparison_id(selected_products)
 
            relevant_reviews = await self.pinecone.search_reviews_by_comparison(
                comparison_id=comparison_id,
                question=question,
                top_k=15
            )
            
            if not relevant_reviews:
                return {
                    "answer": "I don't have enough review data to answer that question.",
                    "sources": [],
                    "confidence": 0.0
                }
            
            # generating answer using gemini
            answer_data = await self._generate_rag_answer(question, relevant_reviews)
            
            return {
                "comparison_id": comparison_id,
                "question": question,
                "answer": answer_data["answer"],
                "sources": answer_data["sources"],
                "confidence": answer_data["confidence"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error answering question: {e}")
            return {"error": str(e)}
    
    def _generate_comparison_id(self, selected_products: Dict[str, Dict]) -> str:
        product_keys = []
        
        for store in sorted(selected_products.keys()):
            product = selected_products[store]
            product_id = product.get("id", "")
            product_keys.append(f"{store}_{product_id}")
        
        comparison_key = "|".join(product_keys)
        comparison_hash = hashlib.md5(comparison_key.encode()).hexdigest()[:16]
        
        return f"COMP_{comparison_hash}"
    
    async def _get_comparison_reviews(self, comparison_id: str) -> List[Dict]:
        try:
            # getting cached reviews first
            # cached_reviews = await self.pinecone.search_comparison_cache(comparison_id)
            # if cached_reviews: 
            #     all_reviews = []
            #     for store, store_reviews in cached_reviews.items():
            #         for review in store_reviews:
            #             review["store"] = store
            #             all_reviews.append(review)
            #     return all_reviews
            
            # Just search individual review vectors directly
            reviews = await self.pinecone.search_reviews_by_comparison(
                comparison_id=comparison_id,
                question="product review analysis",
                top_k=1000
            )
            return reviews
        except Exception as e:
            print(f"Error getting comparison reviews: {e}")
            return []
    
    async def _analyze_sentiment(self, reviews: List[Dict]) -> Dict[str, Any]:
        try:
            store_reviews = {}
            for review in reviews:
                store = review.get("store", "unknown")
                if store not in store_reviews:
                    store_reviews[store] = []
                store_reviews[store].append(review)
            
            store_sentiment = {}
            for store, store_revs in store_reviews.items():
                ratings = [r.get("rating", 0) for r in store_revs]
                avg_rating = sum(ratings) / len(ratings) if ratings else 0
                
                positive = len([r for r in ratings if r >= 4])
                neutral = len([r for r in ratings if r == 3])
                negative = len([r for r in ratings if r <= 2])
                total = len(ratings)
                
                store_sentiment[store] = {
                    "average_rating": round(avg_rating, 2),
                    "total_reviews": total,
                    "positive_percentage": round((positive / total) * 100, 1) if total > 0 else 0,
                    "neutral_percentage": round((neutral / total) * 100, 1) if total > 0 else 0,
                    "negative_percentage": round((negative / total) * 100, 1) if total > 0 else 0,
                    "sentiment_label": self._get_sentiment_label(avg_rating)
                }
            
            return store_sentiment
            
        except Exception as e:
            print(f"Error in sentiment analysis: {e}")
            return {}
    
    async def _extract_pros_cons(self, reviews: List[Dict]) -> Dict[str, List[str]]:
        try:
            sample_reviews = reviews[:50] if len(reviews) > 50 else reviews
            
            review_texts = []
            for review in sample_reviews:
                text = f"Rating: {review.get('rating', 0)}/5 - {review.get('review_text', '')}"
                review_texts.append(text)
            
            prompt = f"""
                Analyze these product reviews and extract the top pros and cons mentioned by customers.
                
                Reviews:
                {chr(10).join(review_texts[:30])}
                
                Return a JSON object with:
                {{
                    "pros": ["list of top 5 positive aspects mentioned"],
                    "cons": ["list of top 5 negative aspects mentioned"]
                }}
                
                Focus on the most frequently mentioned points across all reviews.
                
            """
            
            response = await self.gemini.generate_content(prompt)
            result = json.loads(response.text)
            
            return {
                "pros": result.get("pros", [])[:5],
                "cons": result.get("cons", [])[:5]
            }
            
        except Exception as e:
            print(f"Error extracting pros/cons: {e}")
            return {"pros": [], "cons": []}
    
    async def _analyze_rating_distribution(self, reviews: List[Dict]) -> Dict[str, Any]:
        try:
            store_distributions = {}
            
            for review in reviews:
                store = review.get("store", "unknown")
                rating = review.get("rating", 0)
                
                if store not in store_distributions:
                    store_distributions[store] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                
                if 1 <= rating <= 5:
                    store_distributions[store][rating] += 1
            
            # converting to percentages
            for store, dist in store_distributions.items():
                total = sum(dist.values())
                if total > 0:
                    for rating in dist:
                        dist[rating] = round((dist[rating] / total) * 100, 1)
            
            return store_distributions
            
        except Exception as e:
            print(f"Error in rating distribution: {e}")
            return {}
    
    async def _extract_common_themes(self, reviews: List[Dict]) -> List[Dict[str, Any]]:
        try:
            sample_reviews = reviews[:50] if len(reviews) > 50 else reviews
            
            review_texts = [r.get("review_text", "") for r in sample_reviews]
            combined_text = " ".join(review_texts)[:8000]
            
            prompt = f"""
                Analyze these product reviews and identify the top 5 most common themes or topics discussed.
                
                Reviews text: {combined_text}
                
                Return a JSON array of objects:
                [
                    {{"theme": "Theme name", "frequency": "High/Medium/Low", "description": "Brief description"}},
                    ...
                ]
                
                Focus on aspects like: quality, price, shipping, customer service, product features, etc.
            """
            
            response = await self.gemini.generate_content(prompt)
            result = json.loads(response.text)
            
            return result[:5] if isinstance(result, list) else []
            
        except Exception as e:
            print(f"Error extracting themes: {e}")
            return []
    
    async def _generate_overall_summary(self, reviews: List[Dict], products: Dict[str, Dict]) -> str:
        try:
            total_reviews = len(reviews)
            avg_rating = sum(r.get("rating", 0) for r in reviews) / total_reviews if total_reviews > 0 else 0
            
            store_stats = {}
            for review in reviews:
                store = review.get("store", "unknown")
                if store not in store_stats:
                    store_stats[store] = {"count": 0, "total_rating": 0}
                store_stats[store]["count"] += 1
                store_stats[store]["total_rating"] += review.get("rating", 0)
            
            for store, stats in store_stats.items():
                stats["avg_rating"] = stats["total_rating"] / stats["count"] if stats["count"] > 0 else 0
            
            prompt = f"""
                Generate a concise summary of this product review analysis:
                
                Products analyzed:
                {json.dumps(products, indent=2)}
                
                Review statistics:
                - Total reviews: {total_reviews}
                - Overall average rating: {avg_rating:.2f}/5
                - Store breakdown: {json.dumps(store_stats, indent=2)}
                
                Write a 2-3 sentence summary highlighting the key insights about these products across different stores.
            """
            
            response = await self.gemini.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "Analysis completed successfully."
    
    async def _generate_rag_answer(self, question: str, relevant_reviews: List[Dict]) -> Dict[str, Any]:
        try:
             
            context_reviews = []
            for i, review in enumerate(relevant_reviews[:10]):
                context_reviews.append({
                    "id": i + 1,
                    "store": review.get("store", ""),
                    "rating": review.get("rating", 0),
                    "text": review.get("review_text", "")[:500],
                    "title": review.get("title", ""),
                    "similarity": round(review.get("similarity_score", 0), 3)
                })
            
            prompt = f"""
                Answer the user's question based on the provided product reviews. Use specific information from the reviews and cite your sources.

                Question: {question}

                Relevant Reviews:
                {json.dumps(context_reviews, indent=2)}

                Instructions:
                1. Answer the question directly and comprehensively
                2. Use specific information from the reviews
                3. Mention which stores/reviews support your points
                4. If comparing stores, be objective
                5. If you can't answer confidently, say so

                Return ONLY a valid JSON object in this exact format:
                {{
                    "answer": "Your detailed answer here",
                    "sources": [1, 2, 3],
                    "confidence": 0.85
                }}
            """
            response = await self.gemini.generate_content(prompt)
            
            # Add proper JSON parsing with error handling
            try:
                result = json.loads(response.text)
            except json.JSONDecodeError as json_error:
                # Try to extract answer from raw text as fallback
                return {
                    "answer": response.text if response.text else "I couldn't generate a proper answer.",
                    "sources": [],
                    "confidence": 0.3
                }
                        
            
            cited_sources = []
            for source_id in result.get("sources", []):
                if 1 <= source_id <= len(context_reviews):
                    review = context_reviews[source_id - 1]
                    cited_sources.append({
                        "store": review["store"],
                        "rating": review["rating"],
                        "text_snippet": review["text"][:200] + "..." if len(review["text"]) > 200 else review["text"],
                        "similarity": review["similarity"]
                    })
            
            return {
                "answer": result.get("answer", "I couldn't generate a proper answer."),
                "sources": cited_sources,
                "confidence": result.get("confidence", 0.5)
            }
            
        except Exception as e:
            return {
                "answer": "I encountered an error while processing your question.",
                "sources": [],
                "confidence": 0.0
            }
    
    def _get_sentiment_label(self, avg_rating: float) -> str:
        """Convert average rating to sentiment label"""
        if avg_rating >= 4.0:
            return "Very Positive"
        elif avg_rating >= 3.5:
            return "Positive"
        elif avg_rating >= 2.5:
            return "Mixed"
        elif avg_rating >= 2.0:
            return "Negative"
        else:
            return "Very Negative"
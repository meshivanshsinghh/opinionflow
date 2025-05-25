from fastapi import APIRouter, Depends, HTTPException
from backend.services.review_service import ReviewExtractionService
from backend.dependencies import get_review_service
from pydantic import BaseModel
from typing import Dict, List

router = APIRouter(tags=["reviews"])

class ReviewExtractionRequest(BaseModel):
    session_id: str
    selected_products: Dict[str, Dict]

class ReviewExtractionResponse(BaseModel):
    session_id: str
    reviews: Dict[str, List[Dict]]
    total_reviews: int
    extraction_time_seconds: float

@router.post("/extract", response_model=ReviewExtractionResponse)
async def extract_reviews(
    request: ReviewExtractionRequest,
    review_service: ReviewExtractionService = Depends(get_review_service)
):
    """Extract reviews for selected products"""
    import time
    start_time = time.time()
    
    try:
        reviews = await review_service.extract_reviews_for_products(
            session_id=request.session_id,
            selected_products=request.selected_products
        )
        
        extraction_time = time.time() - start_time
        
        return ReviewExtractionResponse(
            session_id=request.session_id,
            reviews=reviews,
            total_reviews=sum(len(store_reviews) for store_reviews in reviews.values()),
            extraction_time_seconds=round(extraction_time, 2)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
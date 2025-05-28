from fastapi import APIRouter, Depends, HTTPException
from services.review_service import ReviewExtractionService
from dependencies import get_review_service
from pydantic import BaseModel
from typing import Dict, List
import time


router = APIRouter(tags=["reviews"])

class ReviewExtractionRequest(BaseModel):
    selected_products: Dict[str, Dict]

class ReviewExtractionResponse(BaseModel):
    reviews: Dict[str, List[Dict]]
    total_reviews: int
    extraction_time_seconds: float

@router.post("/extract", response_model=ReviewExtractionResponse)
async def extract_reviews(
    request: ReviewExtractionRequest,
    review_service: ReviewExtractionService = Depends(get_review_service)
):
    
    start_time = time.time()
    
    try:
        reviews = await review_service.extract_reviews_for_products(
            selected_products=request.selected_products
        )
        
        extraction_time = time.time() - start_time
        
        return ReviewExtractionResponse(
            reviews=reviews,
            total_reviews=sum(len(store_reviews) for store_reviews in reviews.values()),
            extraction_time_seconds=round(extraction_time, 2)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
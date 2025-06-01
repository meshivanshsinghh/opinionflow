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
    

async def extract_reviews_handler(
    request: ReviewExtractionRequest,
    review_service: ReviewExtractionService = Depends(get_review_service)
):
    start_time = time.time()
    
    try:
        print(f"Extracting reviews for products: {list(request.selected_products.keys())}")
        
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
        print(f"Error in review extraction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Handle both routes to prevent redirect issues
@router.post("/extract", response_model=ReviewExtractionResponse)
async def extract_reviews(
    request: ReviewExtractionRequest,
    review_service: ReviewExtractionService = Depends(get_review_service)
):
    return await extract_reviews_handler(request, review_service)

@router.post("/extract/", response_model=ReviewExtractionResponse)
async def extract_reviews_with_slash(
    request: ReviewExtractionRequest,
    review_service: ReviewExtractionService = Depends(get_review_service)
):
    return await extract_reviews_handler(request, review_service)
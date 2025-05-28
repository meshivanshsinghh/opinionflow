from fastapi import APIRouter, Depends, HTTPException
from services.analysis_service import AnalysisService
from dependencies import get_analysis_service
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter(tags=["analysis"])

class AnalysisRequest(BaseModel):
    selected_products: Dict[str, Dict]

class QuestionRequest(BaseModel):
    question: str
    selected_products: Dict[str, Dict]

@router.post("/analyze")
async def analyze_reviews(
    request: AnalysisRequest,
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    try:
        results = await analysis_service.analyze_reviews(
            selected_products=request.selected_products
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/question")
async def answer_question(
    request: QuestionRequest,
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    try:
        results = await analysis_service.answer_question(
            question=request.question,
            selected_products=request.selected_products
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
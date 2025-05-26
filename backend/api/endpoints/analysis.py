from fastapi import APIRouter, Depends, HTTPException
from backend.services.analysis_service import AnalysisService
from backend.dependencies import get_analysis_service
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter(tags=["analysis"])

class AnalysisRequest(BaseModel):
    session_id: str
    selected_products: Dict[str, Dict]

class QuestionRequest(BaseModel):
    session_id: str
    question: str

@router.post("/analyze")
async def analyze_reviews(
    request: AnalysisRequest,
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """Analyze reviews for selected products"""
    try:
        results = await analysis_service.analyze_reviews(
            session_id=request.session_id,
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
    """Answer questions using RAG"""
    try:
        results = await analysis_service.answer_question(
            session_id=request.session_id,
            question=request.question
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
import os
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any, Optional
import uvicorn

app = FastAPI(title="OpinionFlow API")


class ProductRequest(BaseModel):
    product: str
    max_reviews: int = 150


class ReviewResponse(BaseModel):
    id: str
    source: str
    rating: float
    text: str


class SentimentSummary(BaseModel):
    overall: str
    pros: List[str]
    cons: List[str]


class AspectSentiment(BaseModel):
    aspect: str
    sentiment: float
    count: int


# analysis response
class AnalysisResponse(BaseModel):
    product: str
    summary: SentimentSummary
    aspect: List[AspectSentiment]
    reviews: List[ReviewResponse]
    store_counts: Dict[str, int]


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_product(request: ProductRequest):
    """
    Analyzing product reviews acorss multiple e-commerce stores.
    It returns sentiment summary, aspect-based analysis, and review snippets. 
    """

    if not request.product.strip():
        raise HTTPException(
            status_code=400, detail="Product query cannot be empty")

    return AnalysisResponse(
        product=request.product,
        summary=SentimentSummary(
            overall="TODO",
            pros=["TODO"],
            cons=["TODO"]
        ),
        aspect=[
            AspectSentiment(aspect="quality", sentiment=0.8, count=1)
        ],
        reviews=[ReviewResponse(id="1", source="test", text="Placeholder")],
        store_counts={"amazon": 0, "walmart": 0, "target": 0}
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

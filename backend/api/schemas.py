from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Optional
from datetime import datetime


class Product(BaseModel):
    id: Optional[str] = None
    name: str
    url: HttpUrl
    source: str
    price: Optional[float] = None
    review_count: int = 0
    last_scraped: Optional[datetime] = None
    specifications: Optional[Dict[str, str]] = None
    rating: float = 0.0
    image_url: Optional[str] = None

    class Config:
        from_attributes = True


class ProductQuery(BaseModel):
    query: str
    stores: Optional[List[str]] = ["amazon", "walmart", "target"]


class DiscoverUrlResponse(BaseModel):
    products: Dict[str, List[str]]

class DiscoverResponse(BaseModel):
    products: Dict[str, List[Product]]


class SelectedResponse(BaseModel):
    selected: Dict[str, str]

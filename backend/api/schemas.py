from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Optional
from datetime import datetime


class Product(BaseModel):
    id: Optional[int] = None
    name: str
    url: HttpUrl
    source: str
    price: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    last_scraped: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProductQuery(BaseModel):
    query: str
    stores: Optional[List[str]] = ["amazon", "walmart", "target"]


class DiscoverResponse(BaseModel):
    products: Dict[str, List[Product]]

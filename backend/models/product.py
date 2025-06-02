from pydantic import BaseModel, HttpUrl, Field
from typing import Dict, Optional
from datetime import datetime
from uuid import uuid4

class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    source: str
    url: HttpUrl
    name: str
    price: Optional[float]
    specifications: Dict[str, str] = {}
    rating: float = 0.0
    review_count: int = 0
    image_url: Optional[str] = None
    is_selected: bool = False
    last_scraped: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

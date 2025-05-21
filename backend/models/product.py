from pydantic import BaseModel, HttpUrl, field_validator, Field
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
    rating: Optional[float]
    review_count: Optional[int]
    image_url: Optional[str] = None
    is_selected: bool = False
    last_scraped: Optional[datetime] = None

    @field_validator('price')
    def price_must_be_positive(cls, v):
        if v < 0:
            raise ValueError('Price must be positive')
        return v

    @field_validator('rating')
    def rating_must_be_in_range(cls, v):
        if v is not None and not (0 <= v <= 5):
            raise ValueError('Rating mustbe between 0 and 5')
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

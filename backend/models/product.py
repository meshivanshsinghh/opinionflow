from pydantic import BaseModel, HttpUrl, field_validator
from typing import Dict, Optional
from datetime import datetime


class ProductSpecification(BaseModel):
    label: str
    value: str
    category: Optional[str] = None

    @field_validator('label')
    def label_not_empty(cls, v):
        if not v.strip():
            return ValueError('Label cannot be empty')
        return v.strip()


class Product(BaseModel):
    store: str
    url: HttpUrl
    title: str
    price: float
    image_url: Optional[HttpUrl]
    description: Optional[str]
    specifications: Dict[str, ProductSpecification]
    rating: Optional[float]
    review_count: Optional[int]
    is_selected: bool = False
    last_updated: datetime = datetime.now()

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

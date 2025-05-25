from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, List
from .product import Product


class SearchHistory(BaseModel):
    query: str
    timestamp: datetime
    selected_products: Dict[str, Product]
    notes: Optional[str] = None

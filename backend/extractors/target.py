from .base import BaseProductExtractor
from backend.models.product import Product

class TargetExtractor(BaseProductExtractor):
    async def extract_product_info(self, url: str) -> Product:
        return {
            "id": None,
            "name": "Dummy Target Product",
            "url": url,
            "source": "target",
            "price": 99.99,
            "review_count": 100,
            "last_scraped": None,
            "specifications_raw": "Dummy Target specs",
            "specifications": {},
            "rating": 4.5,
            "image_url": "https://dummyimage.com/target.jpg",
        }

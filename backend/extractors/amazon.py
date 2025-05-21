from backend.extractors.base import BaseProductExtractor
from backend.models.product import Product

class AmazonExtractor(BaseProductExtractor):
    async def extract_product_info(self, url: str) -> Product:
        return {
            "id": None,
            "name": "Dummy Amazon Product",
            "url": url,
            "source": "amazon",
            "price": 99.99,
            "review_count": 100,
            "last_scraped": None,
            "specifications_raw": "Dummy Amazon specs",
            "specifications": {},
            "rating": 4.5,
            "image_url": "https://dummyimage.com/amazon.jpg",
        }


from backend.extractors.base import BaseProductExtractor
from backend.api.schemas import Product

class AmazonExtractor(BaseProductExtractor):
    async def extract_product_info(self, url: str) -> Product:
        return Product(
            name="Dummy Product",
            url=url,
            source="amazon",   
            price=None,
            rating=None,
            review_count=None,
            last_scraped=None,
            specifications={}
        )


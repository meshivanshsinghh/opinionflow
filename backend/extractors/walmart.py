from bs4 import BeautifulSoup
from backend.extractors.base import BaseProductExtractor
from backend.models.product import Product, ProductSpecification


class WalmartExtractor(BaseProductExtractor):
    async def extract_product_info(self, url: str) -> Product:
        html = await self._fetch_page(url)
        soup = BeautifulSoup(html, "html.parser")

        specs = {}
        for spec_elem in soup.select('.specifications-list li'):
            label = spec_elem.select_one('.spec-label').text.strip()
            value = spec_elem.select_one('.spec-value').text.strip()

            specs[label] = ProductSpecification(
                label=label,
                value=value,
                category=self._categorize_spec(label)
            )

        return Product(
            store="walmart",
            url=url,
            title=soup.select_one('h1.prod-title').text.strip(),
            price=self._extract_price(soup),
            image_url=self._extract_image(soup),
            specifications=specs,
        )

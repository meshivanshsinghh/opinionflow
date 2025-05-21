
from backend.extractors.base import BaseProductExtractor
from backend.models.product import Product, ProductSpecification
import re
from datetime import datetime 
from playwright.async_api import async_playwright

class WalmartExtractor(BaseProductExtractor):
    def __init__(self, bright_data_client):
        self.auth = bright_data_client.auth
    
    async def extract_product_info(self, url: str) -> Product: 
        endpoint_url = f"wss://{self.auth}@brd.superproxy.io:9222"

        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.connect_over_cdp(endpoint_url)

                try:
                    page = await browser.new_page()
                    print(f"navigating to: {url}")
                    await page.goto(url, timeout=60000)
                    await page.wait_for_load_state('domcontentloaded')
                    await page.wait_for_timeout(2000)

                    # extraction logic
                    title = await self._extract_title(page)
                    price = await self._extract_price(page)
                    rating, review_count = await self._extract_rating_and_reviews(page)
                    specifications = await self._extract_specifications(page)

                    return Product(
                        name=title or "Unknown Title",
                        url=url,
                        source="walmart",
                        price=price,
                        rating=rating,
                        review_count=review_count,
                        specifications=specifications,
                        last_scraped=datetime.now()
                    )

                finally: 
                    await browser.close()

        except Exception as e:
            print(f"Error during walmart extraction: {str(e)}")
            raise
    

    # extracting title
    async def _extract_title(self, page):
        try:
            el = await page.query_selector('h1#main-title')
            if el: 
                text = await el.text_content()
                return text.strip() if text else None
        except Exception: 
            pass

        return None
            
    # extracting price
    async def _extract_price(self, page):
        try:
            el = await page.query_selector('span[itemprop="price"]')
            if el: 
                text = await el.text_content()
                match = re.search(r"\$([\d,]+(?:\.\d{2})?)", text)
                if match:
                    return float(match.group(1).replace(',', ''))
        except Exception: 
            pass 
        return None

    # extracting rating and reviews
    async def _extract_rating_and_reviews(self, page):
        try:
            block = await page.query_selector('div[data-testid="reviews-and-ratings"]')
            if block: 
                text = await block.inner_text()
                rating_match = re.search(r'(\d+(\.\d+)?)\s*stars?', text)
                count_match = re.search(r'out of\s+(\d+)', text)

                if not count_match: 
                    count_link = await block.query_selector('a[data-testid="item-review-section-link"]')
                    if count_link:
                        count_text = await count_link.text_content()
                        count_match = re.search(r'(\d+)', count_text)
                
                rating = float(rating_match.group(1)) if rating_match else None
                review_count = int(count_match.group(1)) if count_match else None
                return rating, review_count
        except Exception: 
            pass

        return None, None
    
    async def _extract_specifications(self, page):
        specs = {}
        try:
            # clicking on specification dropdown if present 
            spec_header = await page.query_selector('h2:has-text("Specifications")')
            if spec_header: 
                # clicking on specifications button
                button = await spec_header.evaluate_handle('el => el.parentElement.querySelector("button")')
                if button: 
                    aria_expanded = await button.get_attribute('aria-expanded')
                    if aria_expanded == "false": 
                        await button.click()
                        await page.wait_for_timeout(1000)
            more_details_btn = await page.query_selector('button[aria-label="More details"]')
            # checking if more details button is present
            if more_details_btn: 
                await more_details_btn.click()
                # Wait for the correct modal (with heading "More details")
                try:
                    await page.wait_for_selector('div[role="dialog"] h2:has-text("More details")', timeout=5000)
                    modal = await page.query_selector('div[role="dialog"]:has(h2:has-text("More details"))')
                    if modal: 
                        specs.update(await self._extract_spec_pairs(modal))
                    # Close the modal
                    close_btn = await modal.query_selector('button[aria-label="Close dialog"]')
                    if close_btn:
                        await close_btn.click()
                except Exception as e:
                    print(f"Error: More details modal not found or timed out: {e}")
            else: 
                panel = await page.query_selector('div[data-testid="ui-collapse-panel"]')
                if panel: 
                    specs.update(await self._extract_spec_pairs(panel))
        except Exception as e: 
            print(f"Error extracting specifications: {e}")
        return specs 

    async def _extract_spec_pairs(self, container):
        specs = {}
        try:
            items = await container.query_selector_all('div.pb2, div:not([class])')
            for item in items:
                label_el = await item.query_selector('h3')
                value_el = await item.query_selector('div.mv0 span, div.mv0, div span')
                if label_el and value_el:
                    label = await label_el.text_content()
                    value = await value_el.text_content()
                    if label and value:
                        specs[label.strip()] = ProductSpecification(
                            label=label.strip(),
                            value=value.strip()
                        )
        except Exception as e:
            print(f"Error extracting spec pairs: {e}")
        return specs
    

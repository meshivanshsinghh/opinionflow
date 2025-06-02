
from extractors.base import BaseProductExtractor
from models.product import Product
import re
from datetime import datetime
from bs4 import BeautifulSoup

class WalmartExtractor(BaseProductExtractor):
    def __init__(self, bright_data_client):
        self.bright_data = bright_data_client
    
    async def extract_product_info(self, url: str) -> Product: 
        try:
            html = await self.bright_data.get_product_page(url)
            soup = BeautifulSoup(html, "html.parser")

            # Title
            title_el = soup.find("h1", id="main-title")
            name = title_el.get_text(strip=True) if title_el else None

            # Price
            price = None
            price_el = soup.find("span", itemprop="price")
            if price_el:
                price_text = price_el.get_text(strip=True)
                match = re.search(r"\$?([\d,.]+)", price_text)
                if match:
                    try:
                        price = float(match.group(1).replace(",", ""))
                    except Exception:
                        price = None

            # rating and review count
            rating, review_count = None, None
            reviews_block = soup.find("div", {"data-testid": "reviews-and-ratings"})
            if reviews_block:
                text = reviews_block.get_text(" ", strip=True)
                rating_match = re.search(r"([0-5](?:\.\d)?)\s*stars?", text)
                if not rating_match:
                    rating_match = re.search(r"\((\d(?:\.\d)?)\)", text)
                if not rating_match:
                    rating_match = re.search(r"\b([0-5](?:\.\d)?)\b", text)
                if rating_match:
                    try:
                        rating = float(rating_match.group(1))
                    except Exception:
                        rating = None
                count_match = re.search(r"out of\s+(\d+)", text)
                if not count_match:
                     count_match = re.search(r"(\d+)\s+(?:ratings|reviews)", text)
                if count_match:
                    review_count = int(count_match.group(1))

            # image url
            image_url = None
            img_el = soup.find("img", {"data-testid": "hero-image"})
            if img_el:
                image_url = img_el.get("src")
            if not image_url:
                thumb_div = soup.find("div", {"data-testid": "media-thumbnail"})
                if thumb_div:
                    img_tag = thumb_div.find("img")
                    if img_tag:
                        image_url = img_tag.get("src")

            about_section = soup.find("h2", string=re.compile("About this item", re.I))
            spec_text = ""
            if about_section:
                parent = about_section.find_parent("section")
                if parent:
                    ul = parent.find("ul")
                    if ul:
                        spec_text = "\n".join(li.get_text(strip=True) for li in ul.find_all("li"))
            
            if rating is None:
                rating = 0.0
            if review_count is None:
                review_count = 0
            
            return {
                "id": None,
                "name": name,
                "url": url,
                "source": "walmart",
                "price": price,
                "review_count": review_count,
                "last_scraped": datetime.now(),
                "specifications_raw": spec_text,
                "specifications": {},
                "rating": rating,
                "image_url": image_url,
            }
        
        except Exception as e:
            print(f"Error during walmart extraction: {str(e)}")
            raise
    

     
            
    

  
  

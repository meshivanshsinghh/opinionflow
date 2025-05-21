
from backend.extractors.base import BaseProductExtractor
from backend.models.product import Product
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

            # Rating & Review Count
            rating, review_count = None, None
            reviews_block = soup.find("div", {"data-testid": "reviews-and-ratings"})
            if reviews_block:
                text = reviews_block.get_text(" ", strip=True)
                # Try to match "4.3 stars" or "4 stars"
                rating_match = re.search(r"([0-5](?:\.\d)?)\s*stars?", text)
                # If not found, try to match "(4.3)" or "(4)"
                if not rating_match:
                    rating_match = re.search(r"\((\d(?:\.\d)?)\)", text)
                # If still not found, try to match just a number at the start
                if not rating_match:
                    rating_match = re.search(r"\b([0-5](?:\.\d)?)\b", text)
                if rating_match:
                    try:
                        rating = float(rating_match.group(1))
                    except Exception:
                        rating = None
                # Review count
                count_match = re.search(r"out of\s+(\d+)", text)
                if not count_match:
                    # Try to match "438 ratings" or "438 reviews"
                    count_match = re.search(r"(\d+)\s+(?:ratings|reviews)", text)
                if count_match:
                    review_count = int(count_match.group(1))

            # Image URL
            image_url = None
            img_el = soup.find("img", {"data-testid": "hero-image"})
            if img_el:
                image_url = img_el.get("src")

            # About this item (raw spec text)
            about_section = soup.find("h2", string=re.compile("About this item", re.I))
            spec_text = ""
            if about_section:
                parent = about_section.find_parent("section")
                if parent:
                    ul = parent.find("ul")
                    if ul:
                        spec_text = "\n".join(li.get_text(strip=True) for li in ul.find_all("li"))
            
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
    

     
            
    

  
  

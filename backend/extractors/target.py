# from extractors.base import BaseProductExtractor
# from datetime import datetime
# from bs4 import BeautifulSoup
# import re

# class TargetExtractor(BaseProductExtractor):
#     def __init__(self, bright_data_client):
#         self.bright_data = bright_data_client

#     async def extract_product_info(self, url: str) -> dict:
#         try:
#             html = await self.bright_data.get_product_page(url)
#             soup = BeautifulSoup(html, "html.parser")

#             # Title
#             title_el = soup.find("h1", attrs={"data-test": "product-title"})
#             name = title_el.get_text(strip=True) if title_el else None

#             # Price
#             price = None
#             price_el = soup.find("span", attrs={"data-test": "product-price"})
#             if price_el:
#                 price_text = price_el.get_text(strip=True)
#                 match = re.search(r"\$?([\d,.]+)", price_text)
#                 if match:
#                     try:
#                         price = float(match.group(1).replace(",", ""))
#                     except Exception:
#                         price = None

#             # Rating & Review Count
#             rating, review_count = None, None
#             rating_container = soup.find("div", attrs={"data-test": "ratingFeedbackContainer"})
#             if rating_container:
#                 sr_only = rating_container.find("span", class_=re.compile("ScreenReaderOnly"))
#                 if sr_only:
#                     text = sr_only.get_text(strip=True)
#                     match = re.search(r"([0-5](?:\.\d)?)\s*out of 5 stars with ([\d,]+) reviews", text)
#                     if match:
#                         try:
#                             rating = float(match.group(1))
#                         except Exception:
#                             rating = None
#                         try:
#                             review_count = int(match.group(2).replace(",", ""))
#                         except Exception:
#                             review_count = None

#             # Image URL
#             image_url = None
#             img_el = soup.find("img", src=re.compile(r"target\.scene7\.com"))
#             if img_el:
#                 image_url = img_el.get("src")

#             # Specifications: Highlights list
#             spec_text = ""
#             highlights_div = soup.find("div", attrs={"data-test": "@web/ProductDetailPageHighlights"})
#             if highlights_div:
#                 ul = highlights_div.find("ul")
#                 if ul:
#                     for li in ul.find_all("li"):
#                         value = li.get_text(strip=True)
#                         if value:
#                             spec_text += f"{value}\n"

#             # Description (optional, can append to spec_text)
#             desc_div = soup.find("div", attrs={"data-test": "item-details-description"})
#             if desc_div:
#                 desc = desc_div.get_text(strip=True)
#                 if desc:
#                     spec_text += f"Description: {desc}\n"

#             if rating is None:
#                 rating = 0.0
#             if review_count is None:
#                 review_count = 0
            
#             return {
#                 "id": None,
#                 "name": name,
#                 "url": url,
#                 "source": "target",
#                 "price": price,
#                 "review_count": review_count,
#                 "last_scraped": datetime.now(),
#                 "specifications_raw": spec_text,
#                 "specifications": {},
#                 "rating": rating,
#                 "image_url": image_url,
#             }

#         except Exception as e:
#             print(f"Error during target extraction: {str(e)}")
#             raise
from extractors.base import BaseProductExtractor
from datetime import datetime
from bs4 import BeautifulSoup
import re

class AmazonExtractor(BaseProductExtractor):
    def __init__(self, bright_data_client):
        self.bright_data = bright_data_client

    async def extract_product_info(self, url: str) -> dict:
        try:
            html = await self.bright_data.get_product_page(url)
            soup = BeautifulSoup(html, "html.parser")

            title_el = soup.find("span", id="productTitle")
            name = title_el.get_text(strip=True) if title_el else None

            price = None

            offscreen_spans = soup.find_all("span", class_="a-offscreen")
            for span in offscreen_spans:
                price_text = span.get_text(strip=True)
                match = re.search(r"\$([\d,.]+)", price_text)
                if match:
                    try:
                        price = float(match.group(1).replace(",", ""))
                        break
                    except Exception:
                        continue

            if price is None:
                price_to_pay = soup.find("span", class_="priceToPay")
                if price_to_pay:
                    whole = price_to_pay.find("span", class_="a-price-whole")
                    fraction = price_to_pay.find("span", class_="a-price-fraction")
                    if whole and fraction:
                        try:
                            price = float(whole.get_text(strip=True).replace(",", "") + "." + fraction.get_text(strip=True))
                        except Exception:
                            price = None

            if price is None:
                text = soup.get_text(" ", strip=True)
                match = re.search(r"\$([\d,]+\.\d{2})", text)
                if match:
                    try:
                        price = float(match.group(1).replace(",", ""))
                    except Exception:
                        price = None

            rating, review_count = None, None
            rating = None

            histogram = soup.find("i", attrs={"data-hook": "average-star-rating"})
            if histogram:
                alt = histogram.find("span", class_="a-icon-alt")
                if alt:
                    match = re.search(r"([0-5](?:\.\d)?)\s*out of 5", alt.get_text(strip=True))
                    if match:
                        rating = float(match.group(1))

            if rating is None:
                alt = soup.find("span", class_="a-icon-alt")
                if alt:
                    match = re.search(r"([0-5](?:\.\d)?)\s*out of 5", alt.get_text(strip=True))
                    if match:
                        rating = float(match.group(1))

            if rating is None:
                rating_text = soup.find("span", attrs={"data-hook": "rating-out-of-text"})
                if rating_text:
                    match = re.search(r"([0-5](?:\.\d)?)\s*out of 5", rating_text.get_text(strip=True))
                    if match:
                        rating = float(match.group(1))

            if rating is None:
                for span in soup.find_all("span"):
                    text = span.get_text(strip=True)
                    match = re.search(r"([0-5](?:\.\d)?)\s*out of 5", text)
                    if match:
                        rating = float(match.group(1))
                        break
            review_count_el = soup.find("span", id="acrCustomerReviewText")
            if review_count_el:
                text = review_count_el.get_text(strip=True)
                match = re.search(r"([\d,]+)", text)
                if match:
                    review_count = int(match.group(1).replace(",", ""))
            else:
                review_count_el = soup.find("span", attrs={"aria-label": re.compile(r"Reviews", re.I)})
                if review_count_el and review_count_el.has_attr("aria-label"):
                    match = re.search(r"([\d,]+)", review_count_el["aria-label"])
                    if match:
                        review_count = int(match.group(1).replace(",", ""))

            image_url = None
            img_el = soup.find("img", id="landingImage")
            if img_el:
                image_url = img_el.get("src")

            spec_text = ""
            prod_details_div = soup.find("div", id="prodDetails")
            if prod_details_div:
                details_tables = prod_details_div.find_all("table")
                for table in details_tables:
                    for row in table.find_all("tr"):
                        th = row.find("th")
                        td = row.find("td")
                        if th and td:
                            label = th.get_text(strip=True)
                            value = td.get_text(strip=True)
                            spec_text += f"{label}: {value}\n"

            if rating is None:
                rating = 0.0
            if review_count is None:
                review_count = 0
            
            return {
                "id": None,
                "name": name,
                "url": url,
                "source": "amazon",
                "price": price,
                "review_count": review_count,
                "last_scraped": datetime.now(),
                "specifications_raw": spec_text,
                "specifications": {},
                "rating": rating,
                "image_url": image_url,
            }

        except Exception as e:
            print(f"Error during amazon extraction: {str(e)}")
            raise
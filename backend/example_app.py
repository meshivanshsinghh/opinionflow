import requests
import os
from dotenv import load_dotenv
import google.generativeai as genai
import json
from sentence_transformers import SentenceTransformer
import uuid
from pinecone import Pinecone, Index

# loading api key from environment
load_dotenv()
BRIGHT_DATA_API_KEY = os.getenv("BRIGHT_DATA_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# gemini model
model = genai.GenerativeModel(
    model_name='gemini-2.0-flash',
    generation_config={'response_mime_type': 'application/json'}
)

# sentence transformers
sentence_model = SentenceTransformer('all-MiniLM-L6-v2')

# pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index("walmart-analysis")


def generate_embeddings(reviews):
    texts = []
    valid_indices = []

    for idx, review in enumerate(reviews):
        text_parts = []
        if review.get("title"):
            text_parts.append(f'Review Title: {review['title']}')
        if review.get("description"):
            text_parts.append(
                f'Review Description: {review['description']}')

        if text_parts:
            texts.append(". ".join(text_parts))
            valid_indices.append(idx)

    # generating embeddings
    embeddings = sentence_model.encode(texts, show_progress_bar=True,
                                       batch_size=32, convert_to_numpy=True).tolist()

    # attaching embedding back to original review objects
    for emb_idx, review_idx in enumerate(valid_indices):
        reviews[review_idx]["embedding"] = embeddings[emb_idx]

    return reviews


def fetch_page(url: str) -> str:
    try:
        response = requests.post('https://api.brightdata.com/request',
                                 headers={
                                     'Authorization': f'Bearer {BRIGHT_DATA_API_KEY}',
                                     'Content-Type': 'application/json'
                                 }, json={
                                     'zone': 'walmart_web_unlocker',
                                     'url': url,
                                     'format': 'raw',
                                     'data_format': 'markdown',
                                 }, timeout=60)
        print(response)
        if response.status_code == 200 and len(response.text) > 1000:
            return response.text

    except Exception as e:
        print(f'Request failed: {str(e)}')

    return None


def extract_reviews(markdown: str) -> list[dict]:
    prompt = f"""
        Extract all customer reviews from this Walmart product page content.
        Return a JSON array of review objects with the following structure:
        {{
            "reviews" : [
                {{
                    "date": "YYYY-MM-DD or original date format if available",
                    "title": "Review title/headline",
                    "description": "Review text content",
                    "rating": <integer from 1-5>
                }}
            ]
        }}

        Rules:
        - Include all reviews found on the page
        - Use null for any missing fields
        - Convert ratings to integers (1-5)
        - Extract the full review text, not just snippets
        - Preserve original review text without summarizing

        Here's the page content:
        {markdown}

    """
    response = model.generate_content(prompt)

    # Add error handling for JSON decoding
    try:
        result = json.loads(response.text)
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        # Print start of response for debugging
        print(f"Response text sample: {response.text[:200]}...")

        # Try to fix common escape character issues
        fixed_text = response.text.replace(
            '\\', '\\\\')  # Double all backslashes

        try:
            result = json.loads(fixed_text)
            print("Fixed JSON using backslash replacement")
        except json.JSONDecodeError:
            # If still fails, use a safer fallback
            print("Fallback: Returning empty reviews list")
            return []

    # normalizing clean results
    return [
        {
            "date": review.get("date"),
            "title": review.get("title"),
            "description": review.get("description", ""),
            "rating": review.get("rating"),
        } for review in result.get("reviews", [])
    ]

# storing as vector in pinecone


def store_to_pinecone(reviews):
    vectors = []
    for review in reviews:
        if "embedding" not in review:
            continue

        if review.get("title") is None:
            review["title"] = ""
        if review.get("description") is None:
            review["description"] = ""
        if review.get("date") is None:
            review["date"] = ""

        vectors.append({
            "id": str(uuid.uuid4()),
            "values": review["embedding"],
            "metadata": {
                "title": review.get("title"),
                "description": review.get("description"),
                "rating": review.get("rating")
            },
        }
        )

    # batch upload to pinecone (100 vectors per request)
    for i in range(0, len(vectors), 100):
        batch = vectors[i: i + 100]
        index.upsert(vectors=batch)


def main():
    all_reviews = []
    all_page_content = []
    current_page = 1

    # Step 1: Scrape reviews from multiple pages
    while True:
        walmart_url = f'https://www.walmart.com/reviews/product/2392908121?page={current_page}'
        page_content = fetch_page(walmart_url)

        if not page_content:
            print(
                f'Stopping at page {current_page}: fetch failed or no content')
            break

        print(f'fetched page {current_page}')
        all_page_content.append(page_content)

        # checking for next page
        if f'page={current_page + 1}' not in page_content:
            print('No next page found. Ending pagination')
            break

        current_page += 1

        # TODO Remove in production
        if current_page > 15:
            break

    # Step 2: Processing all pages with Gemini
    for page_content in all_page_content:
        page_reviews = extract_reviews(page_content)
        all_reviews.extend(page_reviews)

    # Step 3: Generating embeddings for all reviews
    reviews_with_embeddings = generate_embeddings(all_reviews)

    # Step 4: Uploading to pinecone
    store_to_pinecone(reviews_with_embeddings)

    # Step 5: Saving the final dataset
    with open('walmart_reviews_dataset.json', 'w') as f:
        json.dump(reviews_with_embeddings, f, indent=2)


if __name__ == "__main__":
    main()

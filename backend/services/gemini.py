import google.generativeai as genai
import json 
from core.config import get_settings

class GeminiModel: 
    
    def __init__(self, model_name="gemini-2.0-flash"):
        settings = get_settings()
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={'response_mime_type': 'application/json'}
        )
    
    async def batch_extract_specifications(self, products: list[dict]) -> list[dict]:
        prompt = (
            "For each product below, extract concise, tag-like specifications as a JSON object of label: value pairs."
            "Keep tags short, relevant, and to the point for product cards. "
            "Example: {'Brand': 'Apple', 'Color': 'Green', 'Material': 'Sisal Rope'}\n\n"
            "Products:\n"
        )
        for idx, prod in enumerate(products):
            prompt += f"Product {idx+1}:\nName: {prod['name']}\nSpecs:\n{prod['specifications_raw']}\n\n"
            
        prompt += "Return a JSON array, each element is a dict of label: value pairs for each product in order."
        
        response = self.model.generate_content(prompt)
        try:
            result = json.loads(response.text)
            return result
        except Exception as e:
            print("Gemini JSON parse error:", e)
            return [{} for _ in products]

    async def generate_content(self, prompt: str) -> any:
        """Generate content using Gemini model"""
        try:
            response = self.model.generate_content(prompt)
            return response
        except Exception as e:
            print(f"Gemini generation error: {e}")
            raise
import google.generativeai as genai
import json 
import asyncio
from core.config import get_settings

class GeminiModel: 
    
    def __init__(self, model_name="gemini-2.0-flash"):
        settings = get_settings()
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        self.generation_config = {
            'response_mime_type': 'application/json',
            'candidate_count': 1,
            'max_output_tokens': 4096,
            'temperature': 0.1,
        }
        
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=self.generation_config
        )
    
    async def batch_extract_specifications(self, products: list[dict]) -> list[dict]:
        if len(products) > 10:
            print(f"Large batch ({len(products)} products), this should be chunked")
        
        # Optimize prompt to be more concise
        prompt = (
            "Extract 3-5 key specifications for each product as JSON. "
            "Format: [{\"Brand\":\"X\",\"Type\":\"Y\",...}]. "
            "Be concise and consistent.\n\nProducts:\n"
        )
        
        for idx, prod in enumerate(products):
            specs_raw = (prod.get('specifications_raw', '') or '')[:500]
            product_name = (prod.get('name', '') or '')[:100]
            prompt += f"{idx+1}. Name: {product_name}\nSpecs: {specs_raw}\n\n"
            
        prompt += f"Return JSON array with exactly {len(products)} objects, one for each product in order:"
        
        try:
            async with asyncio.timeout(25):
                response = self.model.generate_content(prompt)
                result = json.loads(response.text)
                
                if len(result) == len(products):
                    return result
                else:
                    print(f"Gemini returned {len(result)} specs for {len(products)} products")
                    if len(result) < len(products):
                        result.extend([{}] * (len(products) - len(result)))
                    else:
                        result = result[:len(products)]
                    return result
                    
        except asyncio.TimeoutError:
            print("Gemini request timed out")
            return [{} for _ in products]
        except json.JSONDecodeError as e:
            print(f"Gemini JSON parse error: {e}")
            return [{} for _ in products]
        except Exception as e:
            print(f"Gemini error: {e}")
            return [{} for _ in products]

    async def generate_content(self, prompt: str) -> any:
        """Generate content using Gemini model with timeout"""
        try:
            async with asyncio.timeout(45):
                response = self.model.generate_content(prompt)
                return response
        except asyncio.TimeoutError:
            print("Gemini content generation timed out")
            raise
        except Exception as e:
            print(f"Gemini generation error: {e}")
            raise
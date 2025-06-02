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
                    if len(result) < len(products):
                        result.extend([{}] * (len(products) - len(result)))
                    else:
                        result = result[:len(products)]
                    return result
                    
        except asyncio.TimeoutError:
            return [{} for _ in products]
        except json.JSONDecodeError as e:
            return [{} for _ in products]
        except Exception as e:
            return [{} for _ in products]

    async def generate_content(self, prompt: str) -> any:
        try:            
            async with asyncio.timeout(25):
                response = self.model.generate_content(prompt)
                if not response or not hasattr(response, 'text'):
                    raise Exception("Invalid response from Gemini - no text attribute")
                if not response.text or response.text.strip() == "":
                    raise Exception("Empty response from Gemini")
                return response
                
        except asyncio.TimeoutError:
            raise Exception("Gemini API timeout after 20 seconds")
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
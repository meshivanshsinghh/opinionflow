from services.brightdata import BrightDataClient
from functools import lru_cache
from services.review_service import ReviewExtractionService
from services.analysis_service import AnalysisService

@lru_cache
def get_bd_client() -> BrightDataClient:
    return BrightDataClient()

@lru_cache
def get_proxy_url() -> str:
    client = get_bd_client()
    return client.proxy_url


def get_product_service():
    from services.product_service import ProductService
    return ProductService(bright_data_client=get_bd_client())

def get_review_service() -> ReviewExtractionService:
    return ReviewExtractionService()

def get_analysis_service():
    return AnalysisService()
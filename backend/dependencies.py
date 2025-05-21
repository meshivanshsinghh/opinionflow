from backend.services.brightdata import BrightDataClient
from functools import lru_cache

@lru_cache
def get_bd_client() -> BrightDataClient:
    return BrightDataClient()

@lru_cache
def get_proxy_url() -> str:
    client = get_bd_client()
    return client.proxy_url


def get_product_service():
    from backend.services.product_service import ProductService
    return ProductService(bright_data_client=get_bd_client())
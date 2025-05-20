from fastapi import Depends
from backend.services.product_service import ProductService
from backend.services.brightdata import BrightDataClient
from backend.core.config import get_settings


async def get_product_service(
    settings=Depends(get_settings)
) -> ProductService:
    bright_data_client = BrightDataClient()
    return ProductService(bright_data_client)


async def get_brightdata_client() -> BrightDataClient:
    return BrightDataClient()

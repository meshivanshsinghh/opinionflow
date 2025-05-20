from fastapi import APIRouter, Depends, HTTPException
from backend.core.exceptions import OpinionFlowException
from backend.services.product_service import ProductService
from backend.core.config import Settings, get_settings
from backend.models.product import Product
from typing import Dict, List
from backend.api.schemas import DiscoverResponse, ProductQuery, Product

router = APIRouter()


@router.post("/discover/", response_model=DiscoverResponse)
async def discover_products(
    query: str,
    settings: Settings = Depends(get_settings),
    product_service: ProductService = Depends()
):
    try:
        return await product_service.discover_products(
            query,
            max_per_store=settings.MAX_PRODUCTS_PER_STORE
        )
    except OpinionFlowException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "details": e.details}
        )


@router.post("/custom/", response_model=Product)
async def add_custom_product(
    url: str,
    product_service: ProductService = Depends()
):
    try:
        return await product_service.add_custom_product(url)
    except OpinionFlowException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "details": e.details}
        )


@router.post("/{store}/select/{product_id}", response_model=ProductQuery)
async def select_product(
    store: str,
    product_id: str,
    product_service: ProductService = Depends()
):
    """
    Select a product for a specific store.
    """
    try:
        product_service.select_product(store, product_id)
        return {"selected": product_service.get_selected_products()}
    except OpinionFlowException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "details": e.details}
        )

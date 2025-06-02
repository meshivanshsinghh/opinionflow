from fastapi import APIRouter, Depends, HTTPException, Body
from core.exceptions import OpinionFlowException
from services.product_service import ProductService
from core.config import Settings, get_settings
from models.product import Product
from dependencies import get_product_service
from api.schemas import DiscoverResponse, ProductQuery, Product, SelectedResponse
from typing import List 
import asyncio

router = APIRouter(tags=["products"])


@router.post("/discover", response_model=DiscoverResponse)
async def discover_products(
    payload: ProductQuery,
    settings: Settings = Depends(get_settings),
    product_service: ProductService = Depends(get_product_service)
):
    try:
        products = await product_service.discover_products_fast(
            payload.query,
            max_per_store=settings.MAX_PRODUCTS_PER_STORE
        )
        return {"products": products}
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=408,
            detail="Request timed out. Please try again with a more specific search query."
        )
    except OpinionFlowException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.details
        )
    except Exception as e:
        print(f"Unexpected error in discover_products_fast: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during product discovery"
        )


@router.post("/custom", response_model=Product)
async def add_custom_product(
    url: str = Body(..., embed=True),
    product_service: ProductService = Depends(get_product_service)
):
    try:
        return await product_service.add_custom_product(url)
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=408,
            detail="Product extraction timed out. Please try again."
        )
    except OpinionFlowException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.details
        )
    except Exception as e:
        print(f"Unexpected error in add_custom_product: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while adding the product"
        )


@router.post("/{store}/select/{product_id}", response_model=SelectedResponse)
async def select_product(
    store: str,
    product_id: str,
    product_service: ProductService = Depends(get_product_service)
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
            detail=e.details
        )
    except Exception as e:
        print(f"Unexpected error in select_product: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while selecting the product"
        )
        
@router.post("/enhance-specifications")
async def enhance_specifications(
    product_ids: List[str] = Body(..., embed=True),
    product_service: ProductService = Depends(get_product_service)
):
    try:
        enhanced_products = await product_service.get_specifications_for_products(product_ids)
        
        products_with_specs = sum(1 for specs in enhanced_products.values() if specs)
        
        return {
            "enhanced_products": enhanced_products,
            "total_products": len(product_ids),
            "products_with_specs": products_with_specs,
            "success": True
        }
    except Exception as e:
        print(f"Unexpected error in enhance_specifications: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while enhancing specifications"
        )
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import get_settings
from backend.api.endpoints import products
from backend.api.endpoints import reviews

def create_application() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="OpinionFlow API",
        description="Real-time product review analysis across multiple stores",
        version="1.0.0"
    )

    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(
        products.router,
        prefix=f"{settings.API_V1_STR}/products",
        tags=["products"]
    )

    app.include_router(
        reviews.router, 
        prefix=f"{settings.API_V1_STR}/reviews",
        tags=["reviews"]
    )
    
    # TODO: include history mechanism
    # app.include_router(
    #     history.router,
    #     prefix=f"{settings.API_V1_STR}/history",
    #     tags=["history"]
    # )

    return app


app = create_application()

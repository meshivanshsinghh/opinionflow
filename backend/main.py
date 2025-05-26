from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import get_settings
from api.endpoints import products
from api.endpoints import reviews
from api.endpoints import analysis
import os


def create_application() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="OpinionFlow API",
        description="Real-time product review analysis across multiple stores",
        version="1.0.0"
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:3001", 
            "https://opinionflow-ruby.vercel.app",  
            "https://opinionflowproject.netlify.app",
        ],
        allow_origin_regex=r"https://.*\.netlify\.app|https://.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Accept",
            "Accept-Language", 
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-CSRF-Token"
        ],
        expose_headers=["X-Total-Count", "X-Page-Count"],
        max_age=3600,  # Cache preflight requests for 1 hour
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
    
    app.include_router(
        analysis.router,
        prefix=f"{settings.API_V1_STR}/analysis",
        tags=["analysis"]
    )
    
    return app


app = create_application()

# Add this for debugging
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
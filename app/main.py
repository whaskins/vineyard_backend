from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
import os
import logging
import asyncio
from pathlib import Path
from datetime import datetime

from app.api.api_v1.api import api_router
from app.core.config import settings
from app.db.session import close_db_connection

# Configure logging
logging.basicConfig(level=logging.INFO if settings.DEBUG else logging.WARNING)
logger = logging.getLogger("app")

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=None,
    redoc_url=None,
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    # Log the CORS origins for debugging
    logger.info(f"Configuring CORS with origins: {settings.BACKEND_CORS_ORIGINS}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_origin_regex=r"https?://.*\.abqwebdev\.com(:[0-9]+)?",  # Allow all subdomains of abqwebdev.com with optional port
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
        expose_headers=["Content-Length"],
        max_age=600,  # Cache preflight requests for 10 minutes
    )

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount static files directory for serving uploaded images
static_dir = Path(__file__).parent / "static"
if not static_dir.exists():
    static_dir.mkdir(parents=True, exist_ok=True)

static_uploads_dir = static_dir / "uploads" / "images"
if not static_uploads_dir.exists():
    static_uploads_dir.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Custom API documentation
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{settings.APP_NAME} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    )

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{settings.APP_NAME} - ReDoc",
    )

# Custom OpenAPI schema for better documentation
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        version="1.0.0",
        description="Vineyard Inventory API for vine management, maintenance tracking, and issue reporting",
        routes=app.routes,
    )
    
    # Add API key security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Enter: **Bearer &lt;JWT&gt;**",
        }
    }
    
    # Apply security to all operations
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            operation["security"] = [{"Bearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Register startup event
@app.on_event("startup")
async def on_startup():
    """Initialize application resources on startup."""
    logger.info("Application starting up...")
    # Any startup initialization can go here

# Register shutdown event to close all database connections
@app.on_event("shutdown")
async def on_shutdown():
    """Perform cleanup tasks on application shutdown."""
    logger.info("Application shutting down...")
    # Use a timeout to ensure we don't block shutdown
    try:
        # Set a timeout for the shutdown process
        await asyncio.wait_for(close_db_connection(), timeout=3.0)
    except asyncio.TimeoutError:
        logger.warning("Timeout during database connection cleanup")
    except Exception as e:
        logger.error(f"Error during shutdown cleanup: {e}")
    
    logger.info("Shutdown cleanup completed")


@app.get("/", tags=["Status"])
async def root():
    """
    Root endpoint - returns API status and basic information
    """
    return {
        "status": "online",
        "api": settings.APP_NAME,
        "version": "1.0.0",
        "documentation": "/docs",
        "api_prefix": settings.API_V1_STR,
    }

@app.get("/health", tags=["Status"])
async def health():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }
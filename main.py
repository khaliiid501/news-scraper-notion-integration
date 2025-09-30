"""Main FastAPI application for the news scraper service."""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import create_tables
from app.api.routes import router
from app.scraper.news_scraper import scrape_all_sources
from app.db.crud import article_crud
from app.db.session import get_db

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    logger.info("Starting news scraper service")
    
    # Create database tables
    await create_tables()
    logger.info("Database tables created")
    
    # Perform initial scraping
    try:
        logger.info("Performing initial news scraping")
        articles = await scrape_all_sources()
        
        # Save articles to database
        if articles:
            async for db in get_db():
                created, skipped = await article_crud.bulk_create_articles(db, articles)
                logger.info("Initial scraping completed", 
                           created=created, 
                           skipped=skipped)
                break
    except Exception as e:
        logger.error("Failed to perform initial scraping", error=str(e))
    
    logger.info("News scraper service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down news scraper service")


# Create FastAPI application
app = FastAPI(
    title="News Scraper API",
    description="A production-ready news scraper service with PostgreSQL storage",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1", tags=["articles"])


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": str(asyncio.get_event_loop().time())
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler."""
    logger.error("Unhandled exception", error=str(exc), path=str(request.url))
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": str(asyncio.get_event_loop().time())
        }
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "News Scraper API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )

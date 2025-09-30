"""FastAPI routes for the news scraper API."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    ArticleCreate,
    ArticleFilters,
    ArticleListResponse,
    ArticleResponse,
    ArticleUpdate,
    HealthResponse,
)
from app.core.logging import get_logger
from app.db.crud import article_crud
from app.db.session import get_db

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(),
        version="1.0.0"
    )


@router.get("/articles", response_model=ArticleListResponse)
async def get_articles(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    source: str | None = Query(None, description="Filter by source"),
    category: str | None = Query(None, description="Filter by category"),
    author: str | None = Query(None, description="Filter by author"),
    search: str | None = Query(None, description="Search in title and content"),
    from_date: datetime | None = Query(None, description="Filter articles from this date"),
    to_date: datetime | None = Query(None, description="Filter articles until this date"),
    db: AsyncSession = Depends(get_db)
):
    """Get articles with optional filtering and pagination."""
    try:
        skip = (page - 1) * size

        filters = ArticleFilters(
            source=source,
            category=category,
            author=author,
            search=search,
            from_date=from_date,
            to_date=to_date
        )

        articles, total = await article_crud.get_articles(db, skip=skip, limit=size, filters=filters)

        pages = (total + size - 1) // size  # Ceiling division

        return ArticleListResponse(
            articles=[ArticleResponse.model_validate(article) for article in articles],
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    except Exception as e:
        logger.error("Failed to get articles", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific article by ID."""
    try:
        article = await article_crud.get_article_by_id(db, article_id)

        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        return ArticleResponse.model_validate(article)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get article", article_id=article_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/articles", response_model=ArticleResponse, status_code=201)
async def create_article(
    article_data: ArticleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new article."""
    try:
        # Check if article already exists
        existing_article = await article_crud.get_article_by_url(db, str(article_data.url))
        if existing_article:
            raise HTTPException(status_code=409, detail="Article with this URL already exists")

        article = await article_crud.create_article(db, article_data)

        if not article:
            raise HTTPException(status_code=400, detail="Failed to create article")

        return ArticleResponse.model_validate(article)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create article", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/articles/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: int,
    article_update: ArticleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing article."""
    try:
        article = await article_crud.update_article(db, article_id, article_update)

        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        return ArticleResponse.model_validate(article)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update article", article_id=article_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/articles/{article_id}", status_code=204)
async def delete_article(
    article_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete an article."""
    try:
        success = await article_crud.delete_article(db, article_id)

        if not success:
            raise HTTPException(status_code=404, detail="Article not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete article", article_id=article_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sources", response_model=list[str])
async def get_sources(db: AsyncSession = Depends(get_db)):
    """Get all unique article sources."""
    try:
        sources = await article_crud.get_sources(db)
        return sources

    except Exception as e:
        logger.error("Failed to get sources", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/categories", response_model=list[str])
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Get all unique article categories."""
    try:
        categories = await article_crud.get_categories(db)
        return categories

    except Exception as e:
        logger.error("Failed to get categories", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get database statistics."""
    try:
        stats = await article_crud.get_stats(db)
        return stats

    except Exception as e:
        logger.error("Failed to get stats", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

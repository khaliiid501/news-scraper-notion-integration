"""Pydantic schemas for API request/response models."""

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class ArticleBase(BaseModel):
    """Base article schema."""
    title: str = Field(..., max_length=500, description="Article title")
    url: HttpUrl = Field(..., description="Article URL")
    content: str | None = Field(None, description="Article content")
    summary: str | None = Field(None, description="Article summary")
    author: str | None = Field(None, max_length=200, description="Article author")
    source: str = Field(..., max_length=200, description="Article source")
    category: str | None = Field(None, max_length=100, description="Article category")
    published_at: datetime | None = Field(None, description="Publication timestamp")


class ArticleCreate(ArticleBase):
    """Schema for creating an article."""
    pass


class ArticleUpdate(BaseModel):
    """Schema for updating an article."""
    title: str | None = Field(None, max_length=500, description="Article title")
    content: str | None = Field(None, description="Article content")
    summary: str | None = Field(None, description="Article summary")
    author: str | None = Field(None, max_length=200, description="Article author")
    category: str | None = Field(None, max_length=100, description="Article category")


class ArticleResponse(ArticleBase):
    """Schema for article response."""
    id: int = Field(..., description="Article ID")
    scraped_at: datetime = Field(..., description="Scraping timestamp")

    class Config:
        from_attributes = True


class ArticleListResponse(BaseModel):
    """Schema for article list response."""
    articles: list[ArticleResponse] = Field(default_factory=list, description="List of articles")
    total: int = Field(0, description="Total number of articles")
    page: int = Field(1, description="Current page number")
    size: int = Field(10, description="Page size")
    pages: int = Field(0, description="Total number of pages")


class ArticleFilters(BaseModel):
    """Schema for article filtering parameters."""
    source: str | None = Field(None, description="Filter by source")
    category: str | None = Field(None, description="Filter by category")
    author: str | None = Field(None, description="Filter by author")
    search: str | None = Field(None, description="Search in title and content")
    from_date: datetime | None = Field(None, description="Filter articles from this date")
    to_date: datetime | None = Field(None, description="Filter articles until this date")


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str = Field("ok", description="Service status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    version: str = Field("1.0.0", description="API version")


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str = Field(..., description="Error message")
    detail: str | None = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")

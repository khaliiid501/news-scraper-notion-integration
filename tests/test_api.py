"""Tests for the API endpoints."""

import pytest
from httpx import AsyncClient
from datetime import datetime

from app.api.schemas import ArticleCreate


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_get_articles_empty(client: AsyncClient):
    """Test getting articles when database is empty."""
    response = await client.get("/api/v1/articles")
    assert response.status_code == 200
    
    data = response.json()
    assert data["articles"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["size"] == 10
    assert data["pages"] == 0


@pytest.mark.asyncio
async def test_create_article(client: AsyncClient):
    """Test creating a new article."""
    article_data = {
        "title": "Test Article",
        "url": "https://example.com/test-article",
        "content": "This is a test article content.",
        "summary": "Test summary",
        "author": "Test Author",
        "source": "Test Source",
        "category": "Technology",
        "published_at": "2024-01-01T12:00:00Z"
    }
    
    response = await client.post("/api/v1/articles", json=article_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["title"] == article_data["title"]
    assert data["url"] == article_data["url"]
    assert data["content"] == article_data["content"]
    assert data["author"] == article_data["author"]
    assert data["source"] == article_data["source"]
    assert data["category"] == article_data["category"]
    assert "id" in data
    assert "scraped_at" in data


@pytest.mark.asyncio
async def test_create_duplicate_article(client: AsyncClient):
    """Test creating a duplicate article."""
    article_data = {
        "title": "Test Article",
        "url": "https://example.com/duplicate-article",
        "content": "This is a test article content.",
        "source": "Test Source"
    }
    
    # Create first article
    response1 = await client.post("/api/v1/articles", json=article_data)
    assert response1.status_code == 201
    
    # Try to create duplicate
    response2 = await client.post("/api/v1/articles", json=article_data)
    assert response2.status_code == 409


@pytest.mark.asyncio
async def test_get_article_by_id(client: AsyncClient):
    """Test getting a specific article by ID."""
    # Create an article first
    article_data = {
        "title": "Test Article for Get",
        "url": "https://example.com/test-get-article",
        "content": "This is a test article content.",
        "source": "Test Source"
    }
    
    create_response = await client.post("/api/v1/articles", json=article_data)
    assert create_response.status_code == 201
    created_article = create_response.json()
    
    # Get the article by ID
    response = await client.get(f"/api/v1/articles/{created_article['id']}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == created_article["id"]
    assert data["title"] == article_data["title"]


@pytest.mark.asyncio
async def test_get_nonexistent_article(client: AsyncClient):
    """Test getting a nonexistent article."""
    response = await client.get("/api/v1/articles/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_article(client: AsyncClient):
    """Test updating an existing article."""
    # Create an article first
    article_data = {
        "title": "Original Title",
        "url": "https://example.com/test-update-article",
        "content": "Original content.",
        "source": "Test Source"
    }
    
    create_response = await client.post("/api/v1/articles", json=article_data)
    assert create_response.status_code == 201
    created_article = create_response.json()
    
    # Update the article
    update_data = {
        "title": "Updated Title",
        "content": "Updated content."
    }
    
    response = await client.put(f"/api/v1/articles/{created_article['id']}", json=update_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["content"] == update_data["content"]
    assert data["url"] == article_data["url"]  # Unchanged


@pytest.mark.asyncio
async def test_delete_article(client: AsyncClient):
    """Test deleting an article."""
    # Create an article first
    article_data = {
        "title": "Article to Delete",
        "url": "https://example.com/test-delete-article",
        "source": "Test Source"
    }
    
    create_response = await client.post("/api/v1/articles", json=article_data)
    assert create_response.status_code == 201
    created_article = create_response.json()
    
    # Delete the article
    response = await client.delete(f"/api/v1/articles/{created_article['id']}")
    assert response.status_code == 204
    
    # Verify it's deleted
    get_response = await client.get(f"/api/v1/articles/{created_article['id']}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_get_articles_with_pagination(client: AsyncClient):
    """Test getting articles with pagination."""
    # Create multiple articles
    for i in range(15):
        article_data = {
            "title": f"Test Article {i}",
            "url": f"https://example.com/test-article-{i}",
            "source": "Test Source"
        }
        response = await client.post("/api/v1/articles", json=article_data)
        assert response.status_code == 201
    
    # Test first page
    response = await client.get("/api/v1/articles?page=1&size=10")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["articles"]) == 10
    assert data["total"] == 15
    assert data["page"] == 1
    assert data["size"] == 10
    assert data["pages"] == 2
    
    # Test second page
    response = await client.get("/api/v1/articles?page=2&size=10")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["articles"]) == 5
    assert data["total"] == 15
    assert data["page"] == 2


@pytest.mark.asyncio
async def test_get_sources(client: AsyncClient):
    """Test getting unique sources."""
    # Create articles with different sources
    sources = ["BBC", "CNN", "Reuters"]
    for source in sources:
        article_data = {
            "title": f"Article from {source}",
            "url": f"https://example.com/article-{source.lower()}",
            "source": source
        }
        response = await client.post("/api/v1/articles", json=article_data)
        assert response.status_code == 201
    
    # Get sources
    response = await client.get("/api/v1/sources")
    assert response.status_code == 200
    
    data = response.json()
    assert set(data) == set(sources)


@pytest.mark.asyncio
async def test_get_categories(client: AsyncClient):
    """Test getting unique categories."""
    # Create articles with different categories
    categories = ["Technology", "Politics", "Sports"]
    for category in categories:
        article_data = {
            "title": f"Article about {category}",
            "url": f"https://example.com/article-{category.lower()}",
            "source": "Test Source",
            "category": category
        }
        response = await client.post("/api/v1/articles", json=article_data)
        assert response.status_code == 201
    
    # Get categories
    response = await client.get("/api/v1/categories")
    assert response.status_code == 200
    
    data = response.json()
    assert set(data) == set(categories)


@pytest.mark.asyncio
async def test_get_stats(client: AsyncClient):
    """Test getting database statistics."""
    # Create some articles
    sources = ["BBC", "CNN"]
    for i, source in enumerate(sources):
        for j in range(3):
            article_data = {
                "title": f"Article {j} from {source}",
                "url": f"https://example.com/article-{source.lower()}-{j}",
                "source": source
            }
            response = await client.post("/api/v1/articles", json=article_data)
            assert response.status_code == 201
    
    # Get stats
    response = await client.get("/api/v1/stats")
    assert response.status_code == 200
    
    data = response.json()
    assert data["total_articles"] == 6
    assert "articles_by_source" in data
    assert data["articles_by_source"]["BBC"] == 3
    assert data["articles_by_source"]["CNN"] == 3
    assert "recent_articles" in data
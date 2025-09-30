"""Tests for the news scraper functionality."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.scraper.news_scraper import NewsScraper, RSSScraperError
from app.api.schemas import ArticleCreate


@pytest.mark.asyncio
async def test_news_scraper_context_manager():
    """Test NewsScraper as async context manager."""
    async with NewsScraper() as scraper:
        assert scraper.session is not None
        assert scraper.timeout == 30
        assert scraper.max_retries == 3


@pytest.mark.asyncio
async def test_scrape_rss_feed_success():
    """Test successful RSS feed scraping."""
    # Mock RSS feed data
    mock_feed_data = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>Test News</title>
            <item>
                <title>Test Article</title>
                <link>https://example.com/article1</link>
                <description>Test article description</description>
                <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
                <author>Test Author</author>
                <category>Technology</category>
            </item>
        </channel>
    </rss>"""
    
    # Mock HTTP response
    mock_response = Mock()
    mock_response.content = mock_feed_data.encode()
    mock_response.raise_for_status = Mock()
    
    async with NewsScraper() as scraper:
        # Mock the HTTP client
        scraper.session.get = AsyncMock(return_value=mock_response)
        
        # Test scraping
        articles = await scraper.scrape_rss_feed("https://example.com/feed.xml")
        
        assert len(articles) == 1
        article = articles[0]
        assert isinstance(article, ArticleCreate)
        assert article.title == "Test Article"
        assert str(article.url) == "https://example.com/article1"
        assert article.source == "Example.com"


@pytest.mark.asyncio
async def test_scrape_rss_feed_http_error():
    """Test RSS feed scraping with HTTP error."""
    async with NewsScraper() as scraper:
        # Mock HTTP error
        import httpx
        scraper.session.get = AsyncMock(side_effect=httpx.HTTPError("Connection failed"))
        
        # Test scraping
        with pytest.raises(RSSScraperError):
            await scraper.scrape_rss_feed("https://example.com/feed.xml")


@pytest.mark.asyncio
async def test_extract_source_name():
    """Test source name extraction."""
    scraper = NewsScraper()
    
    # Test with feed metadata
    mock_feed = Mock()
    mock_feed.feed = Mock()
    mock_feed.feed.title = "BBC News"
    
    source_name = scraper._extract_source_name("https://feeds.bbci.co.uk/news/rss.xml", mock_feed)
    assert source_name == "BBC News"
    
    # Test with URL fallback
    mock_feed_no_title = Mock()
    mock_feed_no_title.feed = Mock()
    mock_feed_no_title.feed.title = None
    
    source_name = scraper._extract_source_name("https://www.cnn.com/feed.xml", mock_feed_no_title)
    assert source_name == "Cnn.com"


@pytest.mark.asyncio
async def test_extract_content_from_entry():
    """Test content extraction from RSS entry."""
    scraper = NewsScraper()
    
    # Test with content field
    mock_entry = Mock()
    mock_entry.content = [Mock()]
    mock_entry.content[0].value = "<p>Test content with <strong>HTML</strong></p>"
    
    content = scraper._extract_content_from_entry(mock_entry)
    assert content == "Test content with HTML"
    
    # Test with summary field
    mock_entry_summary = Mock()
    mock_entry_summary.summary = "Test summary content"
    del mock_entry_summary.content  # Remove content attribute
    
    content = scraper._extract_content_from_entry(mock_entry_summary)
    assert content == "Test summary content"


@pytest.mark.asyncio
async def test_extract_published_date():
    """Test publication date extraction."""
    scraper = NewsScraper()
    
    # Test with published_parsed
    mock_entry = Mock()
    # January 1, 2024, 12:00:00 UTC
    mock_entry.published_parsed = (2024, 1, 1, 12, 0, 0, 0, 1, 0)
    
    published_date = scraper._extract_published_date(mock_entry)
    assert isinstance(published_date, datetime)
    assert published_date.year == 2024
    assert published_date.month == 1
    assert published_date.day == 1


@pytest.mark.asyncio 
async def test_extract_category_from_entry():
    """Test category extraction from RSS entry."""
    scraper = NewsScraper()
    
    # Test with tags
    mock_entry = Mock()
    mock_entry.tags = [Mock()]
    mock_entry.tags[0].term = "Technology"
    
    category = scraper._extract_category_from_entry(mock_entry)
    assert category == "Technology"
    
    # Test with category field
    mock_entry_category = Mock()
    del mock_entry_category.tags  # Remove tags attribute
    mock_entry_category.category = "Science"
    
    category = scraper._extract_category_from_entry(mock_entry_category)
    assert category == "Science"


@pytest.mark.asyncio
async def test_scrape_article_content():
    """Test scraping full article content from URL."""
    html_content = """
    <html>
        <body>
            <nav>Navigation</nav>
            <article>
                <h1>Article Title</h1>
                <p>This is the main article content.</p>
                <p>Second paragraph of content.</p>
            </article>
            <footer>Footer content</footer>
        </body>
    </html>
    """
    
    # Mock HTTP response
    mock_response = Mock()
    mock_response.content = html_content.encode()
    mock_response.raise_for_status = Mock()
    
    async with NewsScraper() as scraper:
        scraper.session.get = AsyncMock(return_value=mock_response)
        
        content = await scraper._scrape_article_content("https://example.com/article")
        
        assert "This is the main article content." in content
        assert "Second paragraph of content." in content
        assert "Navigation" not in content  # Should be removed
        assert "Footer content" not in content  # Should be removed


@pytest.mark.asyncio
async def test_scrape_all_sources():
    """Test scraping all configured sources."""
    from app.scraper.news_scraper import scrape_all_sources
    
    # Mock settings
    with patch('app.scraper.news_scraper.settings') as mock_settings:
        mock_settings.news_sources = [
            "https://example1.com/feed.xml",
            "https://example2.com/feed.xml"
        ]
        
        # Mock the scraper methods
        with patch('app.scraper.news_scraper.NewsScraper') as mock_scraper_class:
            mock_scraper = AsyncMock()
            mock_scraper.__aenter__ = AsyncMock(return_value=mock_scraper)
            mock_scraper.__aexit__ = AsyncMock(return_value=None)
            
            # Mock successful scraping
            mock_article1 = ArticleCreate(
                title="Article 1",
                url="https://example1.com/article1",
                source="Example1"
            )
            mock_article2 = ArticleCreate(
                title="Article 2", 
                url="https://example2.com/article2",
                source="Example2"
            )
            
            mock_scraper.scrape_rss_feed = AsyncMock(side_effect=[
                [mock_article1],
                [mock_article2]
            ])
            
            mock_scraper_class.return_value = mock_scraper
            
            # Test scraping
            articles = await scrape_all_sources()
            
            assert len(articles) == 2
            assert articles[0].title == "Article 1"
            assert articles[1].title == "Article 2"
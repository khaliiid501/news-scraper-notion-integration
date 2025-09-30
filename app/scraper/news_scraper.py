"""News scraping functionality."""

import asyncio
import re
from datetime import datetime
from urllib.parse import urlparse

import feedparser
import httpx
from bs4 import BeautifulSoup

from app.api.schemas import ArticleCreate
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class NewsScraperError(Exception):
    """Base exception for news scraper errors."""
    pass


class RSSScraperError(NewsScraperError):
    """Exception for RSS scraping errors."""
    pass


class HTMLScraperError(NewsScraperError):
    """Exception for HTML scraping errors."""
    pass


class NewsScraper:
    """News scraper for RSS feeds and HTML content."""

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session: httpx.AsyncClient | None = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = httpx.AsyncClient(
            timeout=self.timeout,
            headers={
                "User-Agent": "NewsScraperBot/1.0 (+https://github.com/khaliiid501/news-scraper-notion-integration)"
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.aclose()

    async def scrape_rss_feed(self, feed_url: str) -> list[ArticleCreate]:
        """Scrape articles from an RSS feed."""
        try:
            logger.info("Scraping RSS feed", feed_url=feed_url)

            # Fetch RSS content
            if not self.session:
                raise RSSScraperError("HTTP session not initialized")

            response = await self.session.get(feed_url)
            response.raise_for_status()

            # Parse RSS feed
            feed = feedparser.parse(response.content)

            if feed.bozo and hasattr(feed, 'bozo_exception'):
                logger.warning("RSS feed parsing warning",
                             feed_url=feed_url,
                             warning=str(feed.bozo_exception))

            articles = []
            source_name = self._extract_source_name(feed_url, feed)

            for entry in feed.entries[:settings.max_articles_per_source]:
                try:
                    article = await self._parse_rss_entry(entry, source_name, feed_url)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.error("Failed to parse RSS entry",
                               feed_url=feed_url,
                               entry_title=getattr(entry, 'title', 'Unknown'),
                               error=str(e))

            logger.info("RSS scraping completed",
                       feed_url=feed_url,
                       articles_found=len(articles))
            return articles

        except httpx.HTTPError as e:
            logger.error("HTTP error while fetching RSS feed",
                        feed_url=feed_url,
                        error=str(e))
            raise RSSScraperError(f"Failed to fetch RSS feed: {e}")
        except Exception as e:
            logger.error("Unexpected error while scraping RSS feed",
                        feed_url=feed_url,
                        error=str(e))
            raise RSSScraperError(f"Unexpected error: {e}")

    async def _parse_rss_entry(
        self, entry, source_name: str, feed_url: str
    ) -> ArticleCreate | None:
        """Parse a single RSS entry into an ArticleCreate object."""
        # Extract basic information
        title = getattr(entry, 'title', '').strip()
        link = getattr(entry, 'link', '').strip()

        if not title or not link:
            return None

        # Extract content/summary
        content = self._extract_content_from_entry(entry)
        summary = self._extract_summary_from_entry(entry, content)

        # Extract author
        author = self._extract_author_from_entry(entry)

        # Extract publication date
        published_at = self._extract_published_date(entry)

        # Extract category
        category = self._extract_category_from_entry(entry)

        # Try to enhance content by scraping the article page
        try:
            enhanced_content = await self._scrape_article_content(link)
            if enhanced_content and len(enhanced_content) > len(content or ''):
                content = enhanced_content
        except Exception as e:
            logger.debug("Failed to enhance article content",
                        url=link,
                        error=str(e))

        return ArticleCreate(
            title=title,
            url=link,
            content=content,
            summary=summary,
            author=author,
            source=source_name,
            category=category,
            published_at=published_at
        )

    async def _scrape_article_content(self, url: str) -> str | None:
        """Scrape full article content from the article URL."""
        try:
            if not self.session:
                return None

            response = await self.session.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()

            # Try to find article content using common selectors
            content_selectors = [
                'article',
                '.article-content',
                '.article-body',
                '.post-content',
                '.entry-content',
                '.content',
                '[role="main"]',
                'main'
            ]

            content = None
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = ' '.join(elem.get_text(strip=True) for elem in elements)
                    break

            # Fallback to body content if no specific selectors found
            if not content:
                body = soup.find('body')
                if body:
                    content = body.get_text(strip=True)

            # Clean up the content
            if content:
                content = re.sub(r'\s+', ' ', content).strip()
                # Limit content length
                if len(content) > 10000:
                    content = content[:10000] + '...'

            return content

        except Exception as e:
            logger.debug("Failed to scrape article content", url=url, error=str(e))
            return None

    def _extract_source_name(self, feed_url: str, feed) -> str:
        """Extract source name from feed metadata or URL."""
        # Try to get from feed metadata
        if hasattr(feed, 'feed'):
            if hasattr(feed.feed, 'title') and feed.feed.title:
                return feed.feed.title.strip()

        # Fallback to domain name
        parsed_url = urlparse(feed_url)
        domain = parsed_url.netloc.lower()

        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]

        return domain.capitalize()

    def _extract_content_from_entry(self, entry) -> str | None:
        """Extract content from RSS entry."""
        # Try different content fields
        content_fields = ['content', 'summary', 'description']

        for field in content_fields:
            if hasattr(entry, field):
                content_data = getattr(entry, field)
                if isinstance(content_data, list) and content_data:
                    content_data = content_data[0]

                if hasattr(content_data, 'value'):
                    content = content_data.value
                elif isinstance(content_data, str):
                    content = content_data
                else:
                    continue

                if content:
                    # Clean HTML tags
                    soup = BeautifulSoup(content, 'html.parser')
                    text = soup.get_text(strip=True)
                    return re.sub(r'\s+', ' ', text).strip()

        return None

    def _extract_summary_from_entry(self, entry, content: str | None) -> str | None:
        """Extract summary from RSS entry."""
        # Try summary field first
        if hasattr(entry, 'summary') and entry.summary:
            soup = BeautifulSoup(entry.summary, 'html.parser')
            summary = soup.get_text(strip=True)
            summary = re.sub(r'\s+', ' ', summary).strip()
            if summary:
                return summary

        # Fallback to truncated content
        if content and len(content) > 200:
            return content[:200] + '...'

        return content

    def _extract_author_from_entry(self, entry) -> str | None:
        """Extract author from RSS entry."""
        author_fields = ['author', 'dc_creator', 'creator']

        for field in author_fields:
            if hasattr(entry, field):
                author = getattr(entry, field)
                if isinstance(author, str) and author.strip():
                    return author.strip()

        return None

    def _extract_published_date(self, entry) -> datetime | None:
        """Extract publication date from RSS entry."""
        date_fields = ['published_parsed', 'updated_parsed']

        for field in date_fields:
            if hasattr(entry, field):
                date_tuple = getattr(entry, field)
                if date_tuple:
                    try:
                        import time
                        timestamp = time.mktime(date_tuple)
                        return datetime.fromtimestamp(timestamp)
                    except (ValueError, OverflowError):
                        continue

        return None

    def _extract_category_from_entry(self, entry) -> str | None:
        """Extract category from RSS entry."""
        if hasattr(entry, 'tags') and entry.tags:
            # Get the first tag as category
            return entry.tags[0].term if entry.tags[0].term else None

        if hasattr(entry, 'category') and entry.category:
            return entry.category

        return None


async def scrape_all_sources() -> list[ArticleCreate]:
    """Scrape all configured news sources."""
    all_articles = []

    async with NewsScraper() as scraper:
        tasks = []
        for source_url in settings.news_sources:
            task = scraper.scrape_rss_feed(source_url)
            tasks.append(task)

        # Run all scraping tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("Failed to scrape source",
                           source_url=settings.news_sources[i],
                           error=str(result))
            else:
                all_articles.extend(result)

    logger.info("Completed scraping all sources",
               total_articles=len(all_articles),
               sources_count=len(settings.news_sources))

    return all_articles

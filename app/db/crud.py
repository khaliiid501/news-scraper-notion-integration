"""Database operations for articles."""

from datetime import datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import ArticleCreate, ArticleFilters, ArticleUpdate
from app.core.logging import get_logger
from app.models.article import Article

logger = get_logger(__name__)


class ArticleCRUD:
    """CRUD operations for articles."""

    @staticmethod
    async def create_article(db: AsyncSession, article_data: ArticleCreate) -> Article | None:
        """Create a new article."""
        try:
            article = Article(
                title=article_data.title,
                url=str(article_data.url),
                content=article_data.content,
                summary=article_data.summary,
                author=article_data.author,
                source=article_data.source,
                category=article_data.category,
                published_at=article_data.published_at
            )

            db.add(article)
            await db.commit()
            await db.refresh(article)

            logger.debug("Article created", article_id=article.id, title=article.title)
            return article

        except IntegrityError:
            await db.rollback()
            logger.debug("Article already exists", url=str(article_data.url))
            return None
        except Exception as e:
            await db.rollback()
            logger.error("Failed to create article", error=str(e), url=str(article_data.url))
            raise

    @staticmethod
    async def get_article_by_id(db: AsyncSession, article_id: int) -> Article | None:
        """Get an article by ID."""
        result = await db.execute(select(Article).where(Article.id == article_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_article_by_url(db: AsyncSession, url: str) -> Article | None:
        """Get an article by URL."""
        result = await db.execute(select(Article).where(Article.url == url))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_articles(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 10,
        filters: ArticleFilters | None = None
    ) -> tuple[list[Article], int]:
        """Get articles with optional filtering and pagination."""

        # Build base query
        query = select(Article)
        count_query = select(func.count(Article.id))

        # Apply filters
        if filters:
            conditions = []

            if filters.source:
                conditions.append(Article.source.ilike(f"%{filters.source}%"))

            if filters.category:
                conditions.append(Article.category.ilike(f"%{filters.category}%"))

            if filters.author:
                conditions.append(Article.author.ilike(f"%{filters.author}%"))

            if filters.search:
                search_term = f"%{filters.search}%"
                conditions.append(
                    or_(
                        Article.title.ilike(search_term),
                        Article.content.ilike(search_term),
                        Article.summary.ilike(search_term)
                    )
                )

            if filters.from_date:
                conditions.append(Article.published_at >= filters.from_date)

            if filters.to_date:
                conditions.append(Article.published_at <= filters.to_date)

            if conditions:
                filter_condition = and_(*conditions)
                query = query.where(filter_condition)
                count_query = count_query.where(filter_condition)

        # Add ordering
        query = query.order_by(Article.published_at.desc().nulls_last(), Article.scraped_at.desc())

        # Add pagination
        query = query.offset(skip).limit(limit)

        # Execute queries
        articles_result = await db.execute(query)
        count_result = await db.execute(count_query)

        articles = articles_result.scalars().all()
        total = count_result.scalar() or 0

        return list(articles), total

    @staticmethod
    async def update_article(
        db: AsyncSession,
        article_id: int,
        article_update: ArticleUpdate
    ) -> Article | None:
        """Update an existing article."""
        try:
            result = await db.execute(select(Article).where(Article.id == article_id))
            article = result.scalar_one_or_none()

            if not article:
                return None

            # Update fields
            update_data = article_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(article, field, value)

            await db.commit()
            await db.refresh(article)

            logger.debug("Article updated", article_id=article.id)
            return article

        except Exception as e:
            await db.rollback()
            logger.error("Failed to update article", article_id=article_id, error=str(e))
            raise

    @staticmethod
    async def delete_article(db: AsyncSession, article_id: int) -> bool:
        """Delete an article by ID."""
        try:
            result = await db.execute(select(Article).where(Article.id == article_id))
            article = result.scalar_one_or_none()

            if not article:
                return False

            await db.delete(article)
            await db.commit()

            logger.debug("Article deleted", article_id=article_id)
            return True

        except Exception as e:
            await db.rollback()
            logger.error("Failed to delete article", article_id=article_id, error=str(e))
            raise

    @staticmethod
    async def get_sources(db: AsyncSession) -> list[str]:
        """Get all unique sources."""
        result = await db.execute(
            select(Article.source)
            .distinct()
            .where(Article.source.is_not(None))
            .order_by(Article.source)
        )
        return [source for source in result.scalars().all() if source]

    @staticmethod
    async def get_categories(db: AsyncSession) -> list[str]:
        """Get all unique categories."""
        result = await db.execute(
            select(Article.category)
            .distinct()
            .where(Article.category.is_not(None))
            .order_by(Article.category)
        )
        return [category for category in result.scalars().all() if category]

    @staticmethod
    async def get_stats(db: AsyncSession) -> dict:
        """Get database statistics."""
        # Total articles
        total_result = await db.execute(select(func.count(Article.id)))
        total_articles = total_result.scalar() or 0

        # Articles by source
        sources_result = await db.execute(
            select(Article.source, func.count(Article.id))
            .group_by(Article.source)
            .order_by(func.count(Article.id).desc())
        )
        articles_by_source = dict(sources_result.all())

        # Recent articles (last 24 hours)
        from datetime import timedelta
        yesterday = datetime.now() - timedelta(days=1)
        recent_result = await db.execute(
            select(func.count(Article.id))
            .where(Article.scraped_at >= yesterday)
        )
        recent_articles = recent_result.scalar() or 0

        return {
            "total_articles": total_articles,
            "articles_by_source": articles_by_source,
            "recent_articles": recent_articles
        }

    @staticmethod
    async def bulk_create_articles(db: AsyncSession, articles_data: list[ArticleCreate]) -> tuple[int, int]:
        """Bulk create articles, returning (created_count, skipped_count)."""
        created_count = 0
        skipped_count = 0

        for article_data in articles_data:
            try:
                article = await ArticleCRUD.create_article(db, article_data)
                if article:
                    created_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                logger.error("Failed to create article in bulk operation",
                           url=str(article_data.url),
                           error=str(e))
                skipped_count += 1

        logger.info("Bulk article creation completed",
                   created=created_count,
                   skipped=skipped_count)

        return created_count, skipped_count


# Global instance
article_crud = ArticleCRUD()

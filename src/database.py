"""
Database management and operations
"""
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from loguru import logger

from .models import Base, NewsItem, CrawlLog


class Database:
    """Database manager for the news tracker"""

    def __init__(self, db_url: str = "sqlite:///data/xiaomi_news.db"):
        """
        Initialize database connection

        Args:
            db_url: SQLAlchemy database URL
        """
        self.engine = create_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self._create_tables()

    def _create_tables(self):
        """Create all tables if they don't exist"""
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created/verified")

    @contextmanager
    def get_session(self) -> Session:
        """Context manager for database sessions"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()

    def add_news_item(self, news_data: dict) -> Optional[NewsItem]:
        """
        Add a news item to the database

        Args:
            news_data: Dictionary containing news item data

        Returns:
            NewsItem if created, None if already exists
        """
        with self.get_session() as session:
            # Check if item already exists
            existing = session.query(NewsItem).filter_by(
                post_id=news_data['post_id']
            ).first()

            if existing:
                logger.debug(f"News item already exists: {news_data['post_id']}")
                return None

            # Create new item
            news_item = NewsItem(**news_data)
            session.add(news_item)
            session.flush()
            logger.info(f"Added new news item from {news_data['platform']}: {news_data['post_id']}")
            return news_item

    def get_unreported_items(self, limit: Optional[int] = None) -> List[NewsItem]:
        """
        Get all news items that haven't been reported yet

        Args:
            limit: Maximum number of items to return

        Returns:
            List of unreported NewsItem objects
        """
        with self.get_session() as session:
            query = session.query(NewsItem).filter_by(is_reported=False).order_by(
                NewsItem.published_at.desc()
            )
            if limit:
                query = query.limit(limit)
            return query.all()

    def mark_as_reported(self, item_ids: List[int]):
        """
        Mark news items as reported

        Args:
            item_ids: List of news item IDs to mark as reported
        """
        with self.get_session() as session:
            session.query(NewsItem).filter(NewsItem.id.in_(item_ids)).update(
                {NewsItem.is_reported: True},
                synchronize_session=False
            )
            logger.info(f"Marked {len(item_ids)} items as reported")

    def get_recent_items(self, hours: int = 24, platform: Optional[str] = None) -> List[NewsItem]:
        """
        Get recent news items

        Args:
            hours: Number of hours to look back
            platform: Optional platform filter

        Returns:
            List of recent NewsItem objects
        """
        with self.get_session() as session:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            query = session.query(NewsItem).filter(
                NewsItem.created_at >= cutoff_time
            )
            if platform:
                query = query.filter(NewsItem.platform == platform)

            return query.order_by(NewsItem.published_at.desc()).all()

    def add_crawl_log(self, log_data: dict) -> CrawlLog:
        """
        Add a crawl log entry

        Args:
            log_data: Dictionary containing crawl log data

        Returns:
            Created CrawlLog object
        """
        with self.get_session() as session:
            log_entry = CrawlLog(**log_data)
            session.add(log_entry)
            session.flush()
            return log_entry

    def get_statistics(self) -> dict:
        """
        Get statistics about the news items

        Returns:
            Dictionary with various statistics
        """
        with self.get_session() as session:
            total_items = session.query(NewsItem).count()
            unreported_items = session.query(NewsItem).filter_by(is_reported=False).count()

            # Get counts by platform
            platforms = {}
            for platform in ['xiaohongshu', 'weibo', 'twitter']:
                count = session.query(NewsItem).filter_by(platform=platform).count()
                platforms[platform] = count

            # Recent items (last 24 hours)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            recent_items = session.query(NewsItem).filter(
                NewsItem.created_at >= cutoff_time
            ).count()

            return {
                'total_items': total_items,
                'unreported_items': unreported_items,
                'platforms': platforms,
                'recent_24h': recent_items
            }

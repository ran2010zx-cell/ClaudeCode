"""
Data models for the Xiaomi news tracker
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class NewsItem(Base):
    """Model for storing news/social media posts"""
    __tablename__ = 'news_items'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Source information
    platform = Column(String(50), nullable=False)  # 'xiaohongshu', 'weibo', 'twitter'
    post_id = Column(String(200), unique=True, nullable=False)  # Unique ID from the platform

    # Content
    title = Column(String(500))
    content = Column(Text, nullable=False)
    author = Column(String(200))
    author_url = Column(String(500))

    # Metadata
    post_url = Column(String(1000))
    image_urls = Column(Text)  # JSON string of image URLs
    video_url = Column(String(1000))

    # Engagement metrics
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    views = Column(Integer, default=0)

    # Timestamps
    published_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Status
    is_reported = Column(Boolean, default=False)  # Whether this item has been reported

    def __repr__(self):
        return f"<NewsItem(platform='{self.platform}', post_id='{self.post_id}', author='{self.author}')>"

    def to_dict(self):
        """Convert to dictionary for easy serialization"""
        return {
            'id': self.id,
            'platform': self.platform,
            'post_id': self.post_id,
            'title': self.title,
            'content': self.content,
            'author': self.author,
            'author_url': self.author_url,
            'post_url': self.post_url,
            'image_urls': self.image_urls,
            'video_url': self.video_url,
            'likes': self.likes,
            'comments': self.comments,
            'shares': self.shares,
            'views': self.views,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_reported': self.is_reported
        }


class CrawlLog(Base):
    """Model for tracking crawl operations"""
    __tablename__ = 'crawl_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)  # 'success', 'failed', 'partial'
    items_found = Column(Integer, default=0)
    items_new = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    def __repr__(self):
        return f"<CrawlLog(platform='{self.platform}', status='{self.status}', items_new={self.items_new})>"

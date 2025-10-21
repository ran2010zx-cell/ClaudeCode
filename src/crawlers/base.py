"""
Base crawler class for all social media platforms
"""
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
import requests
from loguru import logger


class BaseCrawler(ABC):
    """Abstract base class for social media crawlers"""

    def __init__(self, keywords: List[str], config: dict):
        """
        Initialize the crawler

        Args:
            keywords: List of keywords to search for
            config: Configuration dictionary
        """
        self.keywords = keywords
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.get('user_agent', 'Mozilla/5.0')
        })

    @abstractmethod
    def get_platform_name(self) -> str:
        """Return the platform name"""
        pass

    @abstractmethod
    def search(self, keyword: str, limit: int = 50) -> List[Dict]:
        """
        Search for posts containing the keyword

        Args:
            keyword: Search keyword
            limit: Maximum number of results to return

        Returns:
            List of dictionaries containing post data
        """
        pass

    def crawl_all_keywords(self, limit_per_keyword: int = 50) -> List[Dict]:
        """
        Crawl all keywords and return combined results

        Args:
            limit_per_keyword: Maximum results per keyword

        Returns:
            List of all found posts
        """
        all_posts = []
        platform = self.get_platform_name()

        for keyword in self.keywords:
            try:
                logger.info(f"[{platform}] Searching for keyword: {keyword}")
                posts = self.search(keyword, limit_per_keyword)
                all_posts.extend(posts)
                logger.info(f"[{platform}] Found {len(posts)} posts for '{keyword}'")

                # Delay between requests to avoid rate limiting
                delay = self.config.get('request_delay', 2.0)
                time.sleep(delay)

            except Exception as e:
                logger.error(f"[{platform}] Error searching for '{keyword}': {e}")
                continue

        # Remove duplicates based on post_id
        unique_posts = self._remove_duplicates(all_posts)
        logger.info(f"[{platform}] Total unique posts found: {len(unique_posts)}")

        return unique_posts

    def _remove_duplicates(self, posts: List[Dict]) -> List[Dict]:
        """
        Remove duplicate posts based on post_id

        Args:
            posts: List of post dictionaries

        Returns:
            List of unique posts
        """
        seen = set()
        unique = []

        for post in posts:
            post_id = post.get('post_id')
            if post_id and post_id not in seen:
                seen.add(post_id)
                unique.append(post)

        return unique

    def normalize_post_data(self, raw_data: dict) -> dict:
        """
        Normalize raw post data to standard format

        Args:
            raw_data: Raw post data from the platform

        Returns:
            Normalized dictionary matching NewsItem model
        """
        return {
            'platform': self.get_platform_name(),
            'post_id': raw_data.get('post_id', ''),
            'title': raw_data.get('title', ''),
            'content': raw_data.get('content', ''),
            'author': raw_data.get('author', ''),
            'author_url': raw_data.get('author_url', ''),
            'post_url': raw_data.get('post_url', ''),
            'image_urls': raw_data.get('image_urls', ''),
            'video_url': raw_data.get('video_url', ''),
            'likes': raw_data.get('likes', 0),
            'comments': raw_data.get('comments', 0),
            'shares': raw_data.get('shares', 0),
            'views': raw_data.get('views', 0),
            'published_at': raw_data.get('published_at', datetime.utcnow()),
        }

    def make_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """
        Make HTTP request with error handling

        Args:
            url: URL to request
            method: HTTP method
            **kwargs: Additional arguments for requests

        Returns:
            Response object or None if failed
        """
        timeout = self.config.get('request_timeout', 30)

        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=timeout,
                **kwargs
            )
            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {url}: {e}")
            return None

    def close(self):
        """Close the session"""
        self.session.close()

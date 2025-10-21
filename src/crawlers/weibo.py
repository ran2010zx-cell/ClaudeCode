"""
Weibo crawler

Weibo provides an API but requires authentication. This implementation shows
how to work with both the API and web scraping approaches.

For API access:
1. Register an app at https://open.weibo.com/
2. Get App Key and App Secret
3. Obtain access token

For web scraping:
- Use mobile.weibo.cn (simpler HTML structure)
- Or use m.weibo.cn
"""
import json
import re
from typing import List, Dict
from datetime import datetime
from urllib.parse import quote
from bs4 import BeautifulSoup
from loguru import logger
from .base import BaseCrawler


class WeiboCrawler(BaseCrawler):
    """Crawler for Weibo platform"""

    def __init__(self, keywords: List[str], config: dict):
        super().__init__(keywords, config)

        # API credentials (if using API)
        self.app_key = config.get('weibo_app_key')
        self.app_secret = config.get('weibo_app_secret')
        self.access_token = config.get('weibo_access_token')

    def get_platform_name(self) -> str:
        return "weibo"

    def search(self, keyword: str, limit: int = 50) -> List[Dict]:
        """
        Search for Weibo posts

        Tries API first if credentials are available, falls back to web scraping

        Args:
            keyword: Search keyword
            limit: Maximum number of results

        Returns:
            List of post dictionaries
        """
        if self.access_token:
            logger.info(f"[Weibo] Using API to search for '{keyword}'")
            return self._search_with_api(keyword, limit)
        else:
            logger.info(f"[Weibo] Using web scraping to search for '{keyword}'")
            return self._search_with_scraping(keyword, limit)

    def _search_with_api(self, keyword: str, limit: int) -> List[Dict]:
        """
        Search using Weibo API

        API endpoint: https://api.weibo.com/2/search/topics.json

        Args:
            keyword: Search keyword
            limit: Maximum results

        Returns:
            List of post data
        """
        posts = []

        try:
            # Weibo API search endpoint
            url = "https://api.weibo.com/2/search/topics.json"

            params = {
                'access_token': self.access_token,
                'q': keyword,
                'count': min(limit, 50)  # API limit
            }

            response = self.make_request(url, params=params)

            if response and response.status_code == 200:
                data = response.json()

                # Parse API response
                if 'statuses' in data:
                    for item in data['statuses'][:limit]:
                        post = self._parse_api_post(item)
                        if post:
                            posts.append(post)

                logger.info(f"[Weibo] API returned {len(posts)} posts")

            else:
                logger.warning("[Weibo] API request failed, falling back to web scraping")
                return self._search_with_scraping(keyword, limit)

        except Exception as e:
            logger.error(f"[Weibo] API error: {e}")
            logger.info("[Weibo] Falling back to web scraping")
            return self._search_with_scraping(keyword, limit)

        return posts

    def _search_with_scraping(self, keyword: str, limit: int) -> List[Dict]:
        """
        Search using web scraping on mobile site

        Uses m.weibo.cn which has simpler structure

        Args:
            keyword: Search keyword
            limit: Maximum results

        Returns:
            List of post data
        """
        posts = []

        try:
            # Use mobile site for easier scraping
            encoded_keyword = quote(keyword)
            url = f"https://m.weibo.cn/search?containerid=100103type%3D1%26q%3D{encoded_keyword}"

            # Add mobile user agent
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
                'Referer': 'https://m.weibo.cn/'
            }

            response = self.session.get(url, headers=headers, timeout=self.config.get('request_timeout', 30))

            if response.status_code == 200:
                # Try to extract JSON data from page
                # Weibo mobile site often embeds data in JavaScript
                posts = self._extract_posts_from_mobile_page(response.text, limit)

                logger.info(f"[Weibo] Scraped {len(posts)} posts from web")

            else:
                logger.warning(f"[Weibo] Web scraping failed with status {response.status_code}")

        except Exception as e:
            logger.error(f"[Weibo] Web scraping error: {e}")

        return posts

    def _extract_posts_from_mobile_page(self, html: str, limit: int) -> List[Dict]:
        """
        Extract post data from mobile page HTML

        The mobile site often has JSON data embedded in scripts

        Args:
            html: HTML content
            limit: Maximum results

        Returns:
            List of posts
        """
        posts = []

        try:
            # Try to find JSON data in script tags
            # Pattern varies, this is a common one
            json_pattern = r'var \$render_data = \[(.*?)\]\[0\]'
            match = re.search(json_pattern, html, re.DOTALL)

            if match:
                json_str = match.group(1)
                data = json.loads(json_str)

                # Navigate to cards (structure may vary)
                if 'cards' in data:
                    for card in data['cards'][:limit]:
                        if 'mblog' in card:
                            post = self._parse_mblog(card['mblog'])
                            if post:
                                posts.append(post)

            else:
                # Fallback: try parsing HTML with BeautifulSoup
                posts = self._parse_html_fallback(html, limit)

        except Exception as e:
            logger.error(f"[Weibo] Error extracting posts from page: {e}")

        return posts

    def _parse_html_fallback(self, html: str, limit: int) -> List[Dict]:
        """
        Fallback HTML parsing method

        Args:
            html: HTML content
            limit: Maximum results

        Returns:
            List of posts
        """
        posts = []

        try:
            soup = BeautifulSoup(html, 'lxml')

            # This is a template - actual selectors depend on current Weibo HTML structure
            # You'll need to inspect the page and adjust these selectors
            post_elements = soup.find_all('div', class_='card-wrap', limit=limit)

            for element in post_elements:
                try:
                    post_data = {
                        'post_id': element.get('mid', ''),
                        'content': element.find('div', class_='weibo-text').get_text(strip=True) if element.find('div', class_='weibo-text') else '',
                        'author': element.find('div', class_='m-text-box').find('h3').get_text(strip=True) if element.find('div', class_='m-text-box') else '',
                        'post_url': f"https://m.weibo.cn/status/{element.get('mid', '')}",
                        'published_at': datetime.utcnow(),  # Need to parse actual timestamp
                    }

                    post = self.normalize_post_data(post_data)
                    posts.append(post)

                except Exception as e:
                    logger.debug(f"[Weibo] Error parsing post element: {e}")
                    continue

        except Exception as e:
            logger.error(f"[Weibo] HTML parsing error: {e}")

        return posts

    def _parse_api_post(self, item: dict) -> Dict:
        """
        Parse post data from API response

        Args:
            item: Post item from API

        Returns:
            Normalized post dictionary
        """
        try:
            post_data = {
                'post_id': str(item.get('id', '')),
                'content': item.get('text', ''),
                'author': item.get('user', {}).get('screen_name', ''),
                'author_url': f"https://weibo.com/u/{item.get('user', {}).get('id', '')}",
                'post_url': f"https://weibo.com/{item.get('user', {}).get('id', '')}/{item.get('bid', '')}",
                'image_urls': json.dumps([pic.get('url') for pic in item.get('pics', [])]),
                'likes': item.get('attitudes_count', 0),
                'comments': item.get('comments_count', 0),
                'shares': item.get('reposts_count', 0),
                'published_at': self._parse_weibo_time(item.get('created_at', '')),
            }

            return self.normalize_post_data(post_data)

        except Exception as e:
            logger.error(f"[Weibo] Error parsing API post: {e}")
            return {}

    def _parse_mblog(self, mblog: dict) -> Dict:
        """
        Parse mblog data from mobile JSON

        Args:
            mblog: Mblog dictionary

        Returns:
            Normalized post dictionary
        """
        try:
            post_data = {
                'post_id': str(mblog.get('id', '')),
                'content': mblog.get('text', ''),
                'author': mblog.get('user', {}).get('screen_name', ''),
                'author_url': f"https://weibo.com/u/{mblog.get('user', {}).get('id', '')}",
                'post_url': f"https://m.weibo.cn/status/{mblog.get('id', '')}",
                'image_urls': json.dumps([pic.get('url') for pic in mblog.get('pics', [])]) if 'pics' in mblog else '',
                'likes': mblog.get('attitudes_count', 0),
                'comments': mblog.get('comments_count', 0),
                'shares': mblog.get('reposts_count', 0),
                'published_at': self._parse_weibo_time(mblog.get('created_at', '')),
            }

            return self.normalize_post_data(post_data)

        except Exception as e:
            logger.error(f"[Weibo] Error parsing mblog: {e}")
            return {}

    def _parse_weibo_time(self, time_str: str) -> datetime:
        """
        Parse Weibo timestamp

        Weibo uses format like: "Fri Nov 24 12:34:56 +0800 2023"

        Args:
            time_str: Timestamp string

        Returns:
            datetime object
        """
        try:
            # Remove timezone info for simplicity
            time_str = re.sub(r'\+\d{4}\s', '', time_str)
            return datetime.strptime(time_str, '%a %b %d %H:%M:%S %Y')
        except Exception:
            return datetime.utcnow()

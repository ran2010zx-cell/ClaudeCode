"""
Twitter/X crawler

Twitter provides an API that requires authentication.

To use Twitter API:
1. Apply for developer account at https://developer.twitter.com/
2. Create an app and get API credentials
3. Use either:
   - API v2 with Bearer Token (recommended)
   - API v1.1 with OAuth tokens

Note: Twitter's free tier has limited access. Consider premium tiers for
higher rate limits.
"""
import json
from typing import List, Dict
from datetime import datetime
from loguru import logger

try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False
    logger.warning("tweepy not installed. Twitter crawler will not work. Install with: pip install tweepy")

from .base import BaseCrawler


class TwitterCrawler(BaseCrawler):
    """Crawler for Twitter/X platform"""

    def __init__(self, keywords: List[str], config: dict):
        super().__init__(keywords, config)

        # API credentials
        self.bearer_token = config.get('twitter_bearer_token')
        self.api_key = config.get('twitter_api_key')
        self.api_secret = config.get('twitter_api_secret')
        self.access_token = config.get('twitter_access_token')
        self.access_token_secret = config.get('twitter_access_token_secret')

        # Initialize API client
        self.client = None
        self.api = None
        self._init_api()

    def get_platform_name(self) -> str:
        return "twitter"

    def _init_api(self):
        """Initialize Twitter API client"""
        if not TWEEPY_AVAILABLE:
            logger.error("[Twitter] tweepy library not available")
            return

        try:
            # Try using Bearer Token for API v2 (simpler and recommended)
            if self.bearer_token:
                self.client = tweepy.Client(bearer_token=self.bearer_token)
                logger.info("[Twitter] Initialized with Bearer Token (API v2)")

            # Also initialize API v1.1 if credentials available
            elif self.api_key and self.api_secret:
                if self.access_token and self.access_token_secret:
                    # Full OAuth
                    auth = tweepy.OAuthHandler(self.api_key, self.api_secret)
                    auth.set_access_token(self.access_token, self.access_token_secret)
                    self.api = tweepy.API(auth)
                    logger.info("[Twitter] Initialized with OAuth 1.0a (API v1.1)")
                else:
                    # App-only auth
                    auth = tweepy.AppAuthHandler(self.api_key, self.api_secret)
                    self.api = tweepy.API(auth)
                    logger.info("[Twitter] Initialized with App Auth (API v1.1)")

            else:
                logger.warning("[Twitter] No API credentials provided")

        except Exception as e:
            logger.error(f"[Twitter] Error initializing API: {e}")

    def search(self, keyword: str, limit: int = 50) -> List[Dict]:
        """
        Search for tweets

        Args:
            keyword: Search keyword
            limit: Maximum number of results

        Returns:
            List of tweet dictionaries
        """
        if not TWEEPY_AVAILABLE:
            logger.error("[Twitter] Cannot search: tweepy not available")
            return []

        # Try API v2 first, then v1.1
        if self.client:
            return self._search_v2(keyword, limit)
        elif self.api:
            return self._search_v1(keyword, limit)
        else:
            logger.error("[Twitter] No API client available")
            return []

    def _search_v2(self, keyword: str, limit: int) -> List[Dict]:
        """
        Search using Twitter API v2

        Args:
            keyword: Search keyword
            limit: Maximum results

        Returns:
            List of tweet data
        """
        tweets = []

        try:
            # Build search query
            # You can enhance this with filters like -is:retweet, lang:en, etc.
            query = f"{keyword} -is:retweet"

            # Search recent tweets
            response = self.client.search_recent_tweets(
                query=query,
                max_results=min(limit, 100),  # API limit
                tweet_fields=['created_at', 'public_metrics', 'author_id', 'entities'],
                user_fields=['username', 'name'],
                expansions=['author_id']
            )

            if response.data:
                # Create user lookup
                users = {}
                if response.includes and 'users' in response.includes:
                    users = {user.id: user for user in response.includes['users']}

                for tweet in response.data:
                    author = users.get(tweet.author_id)
                    post = self._parse_tweet_v2(tweet, author)
                    if post:
                        tweets.append(post)

                logger.info(f"[Twitter] API v2 returned {len(tweets)} tweets")

        except tweepy.errors.TweepyException as e:
            logger.error(f"[Twitter] API v2 error: {e}")
        except Exception as e:
            logger.error(f"[Twitter] Unexpected error in v2 search: {e}")

        return tweets

    def _search_v1(self, keyword: str, limit: int) -> List[Dict]:
        """
        Search using Twitter API v1.1

        Args:
            keyword: Search keyword
            limit: Maximum results

        Returns:
            List of tweet data
        """
        tweets = []

        try:
            # Search tweets
            search_results = tweepy.Cursor(
                self.api.search_tweets,
                q=keyword,
                tweet_mode='extended',
                lang='zh',  # Chinese, change as needed
                result_type='recent'
            ).items(limit)

            for tweet in search_results:
                post = self._parse_tweet_v1(tweet)
                if post:
                    tweets.append(post)

            logger.info(f"[Twitter] API v1.1 returned {len(tweets)} tweets")

        except tweepy.errors.TweepyException as e:
            logger.error(f"[Twitter] API v1.1 error: {e}")
        except Exception as e:
            logger.error(f"[Twitter] Unexpected error in v1 search: {e}")

        return tweets

    def _parse_tweet_v2(self, tweet, author) -> Dict:
        """
        Parse tweet from API v2 response

        Args:
            tweet: Tweet object from API v2
            author: User object

        Returns:
            Normalized tweet dictionary
        """
        try:
            # Get metrics
            metrics = tweet.public_metrics if hasattr(tweet, 'public_metrics') else {}

            # Extract URLs and media
            image_urls = []
            video_url = ''

            if hasattr(tweet, 'entities') and tweet.entities:
                if 'media' in tweet.entities:
                    for media in tweet.entities['media']:
                        if media.get('type') == 'photo':
                            image_urls.append(media.get('url', ''))
                        elif media.get('type') == 'video':
                            video_url = media.get('url', '')

            post_data = {
                'post_id': str(tweet.id),
                'content': tweet.text,
                'author': author.name if author else 'Unknown',
                'author_url': f"https://twitter.com/{author.username}" if author else '',
                'post_url': f"https://twitter.com/user/status/{tweet.id}",
                'image_urls': json.dumps(image_urls),
                'video_url': video_url,
                'likes': metrics.get('like_count', 0),
                'comments': metrics.get('reply_count', 0),
                'shares': metrics.get('retweet_count', 0),
                'views': metrics.get('impression_count', 0),
                'published_at': tweet.created_at if hasattr(tweet, 'created_at') else datetime.utcnow(),
            }

            return self.normalize_post_data(post_data)

        except Exception as e:
            logger.error(f"[Twitter] Error parsing v2 tweet: {e}")
            return {}

    def _parse_tweet_v1(self, tweet) -> Dict:
        """
        Parse tweet from API v1.1 response

        Args:
            tweet: Status object from API v1.1

        Returns:
            Normalized tweet dictionary
        """
        try:
            # Get full text
            text = tweet.full_text if hasattr(tweet, 'full_text') else tweet.text

            # Extract media
            image_urls = []
            video_url = ''

            if hasattr(tweet, 'extended_entities') and 'media' in tweet.extended_entities:
                for media in tweet.extended_entities['media']:
                    if media['type'] == 'photo':
                        image_urls.append(media['media_url_https'])
                    elif media['type'] == 'video':
                        # Get highest quality video
                        variants = media.get('video_info', {}).get('variants', [])
                        video_variants = [v for v in variants if v.get('content_type') == 'video/mp4']
                        if video_variants:
                            video_url = max(video_variants, key=lambda x: x.get('bitrate', 0))['url']

            post_data = {
                'post_id': str(tweet.id),
                'content': text,
                'author': tweet.user.name,
                'author_url': f"https://twitter.com/{tweet.user.screen_name}",
                'post_url': f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}",
                'image_urls': json.dumps(image_urls),
                'video_url': video_url,
                'likes': tweet.favorite_count,
                'comments': tweet.reply_count if hasattr(tweet, 'reply_count') else 0,
                'shares': tweet.retweet_count,
                'views': 0,  # Not available in v1.1
                'published_at': tweet.created_at,
            }

            return self.normalize_post_data(post_data)

        except Exception as e:
            logger.error(f"[Twitter] Error parsing v1 tweet: {e}")
            return {}

    def get_rate_limit_status(self) -> dict:
        """
        Get current rate limit status

        Returns:
            Dictionary with rate limit information
        """
        try:
            if self.client:
                # API v2 doesn't have a direct rate limit endpoint in tweepy yet
                return {"status": "API v2 rate limits vary by endpoint"}
            elif self.api:
                limits = self.api.rate_limit_status()
                return limits
            else:
                return {"error": "No API client available"}

        except Exception as e:
            logger.error(f"[Twitter] Error getting rate limits: {e}")
            return {"error": str(e)}

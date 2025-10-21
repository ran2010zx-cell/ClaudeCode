"""
Task scheduler for periodic crawling
"""
import time
from datetime import datetime
from typing import List, Callable
import schedule
from loguru import logger

from .config import settings
from .database import Database
from .crawlers import XiaohongshuCrawler, WeiboCrawler, TwitterCrawler
from .reporter import Reporter


class NewsScheduler:
    """Scheduler for news tracking tasks"""

    def __init__(self, db: Database, reporter: Reporter):
        """
        Initialize scheduler

        Args:
            db: Database instance
            reporter: Reporter instance
        """
        self.db = db
        self.reporter = reporter
        self.keywords = settings.get_keywords_list()

        # Initialize crawlers
        config = self._get_crawler_config()
        self.crawlers = {
            'xiaohongshu': XiaohongshuCrawler(self.keywords, config),
            'weibo': WeiboCrawler(self.keywords, config),
            'twitter': TwitterCrawler(self.keywords, config),
        }

        logger.info(f"Scheduler initialized with keywords: {self.keywords}")

    def _get_crawler_config(self) -> dict:
        """
        Get configuration for crawlers

        Returns:
            Configuration dictionary
        """
        return {
            # General settings
            'user_agent': settings.user_agent,
            'request_timeout': settings.request_timeout,
            'request_delay': settings.request_delay,

            # Twitter credentials
            'twitter_bearer_token': settings.twitter_bearer_token,
            'twitter_api_key': settings.twitter_api_key,
            'twitter_api_secret': settings.twitter_api_secret,
            'twitter_access_token': settings.twitter_access_token,
            'twitter_access_token_secret': settings.twitter_access_token_secret,

            # Weibo credentials
            'weibo_app_key': settings.weibo_app_key,
            'weibo_app_secret': settings.weibo_app_secret,
            'weibo_access_token': settings.weibo_access_token,
        }

    def crawl_all_platforms(self):
        """
        Crawl all platforms and save new items

        This is the main task that runs periodically
        """
        logger.info("=" * 60)
        logger.info("Starting crawl cycle")
        logger.info("=" * 60)

        total_new_items = 0
        crawl_results = {}

        for platform_name, crawler in self.crawlers.items():
            result = self._crawl_platform(platform_name, crawler)
            crawl_results[platform_name] = result
            total_new_items += result['items_new']

        # Log crawl summary
        logger.info("=" * 60)
        logger.info(f"Crawl cycle completed. Total new items: {total_new_items}")
        for platform, result in crawl_results.items():
            logger.info(f"  {platform}: {result['items_new']} new / {result['items_found']} found")
        logger.info("=" * 60)

        # Send report if there are new items
        if total_new_items >= settings.report_min_items:
            logger.info(f"Sending report with {total_new_items} new items")
            self.reporter.send_report()
        else:
            logger.info(f"Not sending report (only {total_new_items} items, minimum is {settings.report_min_items})")

    def _crawl_platform(self, platform_name: str, crawler) -> dict:
        """
        Crawl a single platform

        Args:
            platform_name: Name of the platform
            crawler: Crawler instance

        Returns:
            Dictionary with crawl results
        """
        log_data = {
            'platform': platform_name,
            'started_at': datetime.utcnow(),
            'status': 'failed',
            'items_found': 0,
            'items_new': 0,
            'error_message': None
        }

        try:
            logger.info(f"[{platform_name}] Starting crawl")

            # Crawl all keywords
            posts = crawler.crawl_all_keywords(
                limit_per_keyword=settings.max_items_per_platform
            )

            log_data['items_found'] = len(posts)

            # Save to database
            items_saved = 0
            for post in posts:
                result = self.db.add_news_item(post)
                if result:  # New item
                    items_saved += 1

            log_data['items_new'] = items_saved
            log_data['status'] = 'success'

            logger.info(
                f"[{platform_name}] Crawl completed: "
                f"{items_saved} new items out of {len(posts)} found"
            )

        except Exception as e:
            logger.error(f"[{platform_name}] Crawl failed: {e}")
            log_data['error_message'] = str(e)
            log_data['status'] = 'failed'

        finally:
            log_data['completed_at'] = datetime.utcnow()
            self.db.add_crawl_log(log_data)

        return log_data

    def setup_schedule(self):
        """
        Set up the schedule for periodic crawling

        By default, runs every hour based on settings
        """
        interval = settings.crawl_interval_minutes

        logger.info(f"Setting up schedule: crawl every {interval} minutes")

        # Schedule the crawl task
        schedule.every(interval).minutes.do(self.crawl_all_platforms)

        # Also run immediately on startup
        logger.info("Running initial crawl")
        self.crawl_all_platforms()

    def run(self):
        """
        Run the scheduler loop

        This will block and run indefinitely
        """
        self.setup_schedule()

        logger.info("Scheduler started. Press Ctrl+C to stop.")

        try:
            while True:
                schedule.run_pending()
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up...")

        # Close crawler sessions
        for crawler in self.crawlers.values():
            try:
                crawler.close()
            except Exception as e:
                logger.error(f"Error closing crawler: {e}")

        logger.info("Cleanup completed")

    def run_once(self):
        """
        Run a single crawl cycle and exit

        Useful for testing or cron jobs
        """
        logger.info("Running single crawl cycle")
        self.crawl_all_platforms()
        self.cleanup()
        logger.info("Single crawl completed")

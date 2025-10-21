"""
Main entry point for Xiaomi News Tracker
"""
import sys
import argparse
from pathlib import Path
from loguru import logger

from .config import settings
from .database import Database
from .reporter import Reporter
from .scheduler import NewsScheduler


def setup_logging():
    """Configure logging"""
    # Remove default handler
    logger.remove()

    # Add console handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=settings.log_level
    )

    # Add file handler
    log_file = Path(settings.log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        settings.log_file,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
        level=settings.log_level
    )

    logger.info("Logging configured")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Xiaomi News Tracker - Social Media Monitoring System"
    )

    parser.add_argument(
        '--mode',
        choices=['run', 'once', 'test', 'stats', 'demo'],
        default='run',
        help='Run mode: run (continuous), once (single crawl), test (test report), stats (show statistics), demo (run with demo data)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    args = parser.parse_args()

    # Override log level if debug
    if args.debug:
        settings.log_level = "DEBUG"

    # Setup logging
    setup_logging()

    logger.info("=" * 60)
    logger.info("Xiaomi News Tracker Starting")
    logger.info("=" * 60)
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Keywords: {settings.get_keywords_list()}")
    logger.info(f"Crawl interval: {settings.crawl_interval_minutes} minutes")
    logger.info(f"Database: {settings.database_url}")

    # Initialize components
    db = Database(settings.database_url)
    reporter = Reporter(db)

    if args.mode == 'stats':
        # Show statistics
        show_statistics(db)

    elif args.mode == 'test':
        # Test report generation
        test_report(reporter)

    elif args.mode == 'demo':
        # Run with demo data
        run_demo(db, reporter)

    elif args.mode == 'once':
        # Run single crawl
        scheduler = NewsScheduler(db, reporter)
        scheduler.run_once()

    else:
        # Run continuous monitoring
        scheduler = NewsScheduler(db, reporter)
        scheduler.run()


def show_statistics(db: Database):
    """
    Show database statistics

    Args:
        db: Database instance
    """
    logger.info("Fetching statistics...")

    stats = db.get_statistics()

    print("\n" + "=" * 60)
    print("DATABASE STATISTICS")
    print("=" * 60)
    print(f"\nTotal items: {stats['total_items']}")
    print(f"Unreported items: {stats['unreported_items']}")
    print(f"Recent items (24h): {stats['recent_24h']}")
    print("\nBy platform:")
    for platform, count in stats['platforms'].items():
        print(f"  {platform}: {count}")
    print("=" * 60 + "\n")


def test_report(reporter: Reporter):
    """
    Test report generation

    Args:
        reporter: Reporter instance
    """
    logger.info("Generating test report...")
    reporter.generate_and_print_report()


def run_demo(db: Database, reporter: Reporter):
    """
    Run demo mode with generated data

    Args:
        db: Database instance
        reporter: Reporter instance
    """
    from .demo_data import DemoDataGenerator

    logger.info("=" * 60)
    logger.info("DEMO MODE - Generating sample data")
    logger.info("=" * 60)

    generator = DemoDataGenerator()

    # Generate demo posts
    logger.info("Generating demo posts...")
    posts = generator.generate_all_posts(count_per_platform=8)

    logger.info(f"Generated {len(posts)} demo posts")

    # Save to database
    saved_count = 0
    for post in posts:
        result = db.add_news_item(post)
        if result:
            saved_count += 1

    logger.info(f"Saved {saved_count} new posts to database")

    # Show statistics
    logger.info("\n")
    show_statistics(db)

    # Generate and display report
    logger.info("Generating demo report...")
    logger.info("=" * 60)

    items = db.get_unreported_items()
    if items:
        logger.info(f"Found {len(items)} unreported items")
        print("\n" + "=" * 70)
        print("DEMO REPORT PREVIEW")
        print("=" * 70)

        # Group by platform
        by_platform = {}
        for item in items:
            if item.platform not in by_platform:
                by_platform[item.platform] = []
            by_platform[item.platform].append(item)

        for platform, platform_items in by_platform.items():
            print(f"\n【{platform.upper()}】 - {len(platform_items)} 条新舆情")
            print("-" * 70)

            for i, item in enumerate(platform_items[:3], 1):  # Show first 3
                print(f"\n{i}. {item.title or '(无标题)'}")
                print(f"   作者: {item.author}")
                print(f"   时间: {item.published_at.strftime('%Y-%m-%d %H:%M')}")
                print(f"   内容: {item.content[:150]}...")
                print(f"   互动: 👍{item.likes} 💬{item.comments} 🔄{item.shares} 👀{item.views}")

            if len(platform_items) > 3:
                print(f"\n   ... 还有 {len(platform_items) - 3} 条")

        print("\n" + "=" * 70)
        print("提示: 完整报告可通过邮件发送 (需配置EMAIL_ENABLED=true)")
        print("=" * 70 + "\n")

        # Ask if user wants to send email report
        if settings.email_enabled:
            logger.info("Email is enabled. Generating full report...")
            reporter.send_report()
            logger.info("Demo report sent!")
        else:
            logger.info("Email not enabled. To enable, set EMAIL_ENABLED=true in .env")

    else:
        logger.info("No unreported items found")

    logger.info("\n" + "=" * 60)
    logger.info("Demo completed! Database saved at: data/xiaomi_news.db")
    logger.info("=" * 60)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nProgram interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)

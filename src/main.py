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
        choices=['run', 'once', 'test', 'stats'],
        default='run',
        help='Run mode: run (continuous), once (single crawl), test (test report), stats (show statistics)'
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


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nProgram interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)

#!/usr/bin/env python3
"""
Notion → 翻译 → Substack + Twitter 自动发布工具

工作流程:
1. 从 Notion 数据库获取待发布的文章
2. 使用 AI 翻译成英文
3. 发布到 Substack
4. 将文章拆分为推文线程发布到 Twitter
5. 最后一条推文链接到 Substack 文章
6. 更新 Notion 中的发布状态
"""

import sys
import argparse
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from notion_client import NotionClient, NotionArticle
from translator import Translator, TranslationResult
from substack import SubstackPublisher, SubstackPost, PublishResult
from twitter_publisher import TwitterPublisher, TwitterPublishResult


@dataclass
class PublishingResult:
    """完整发布结果"""
    success: bool
    article_title: str
    translated_title: str = ""
    substack_url: str = ""
    twitter_url: str = ""
    error: Optional[str] = None
    details: Dict[str, Any] = None


class AutoPublisher:
    """自动发布器 - 协调整个工作流程"""

    def __init__(self):
        self.notion = NotionClient()
        self.translator = Translator()
        self.substack = SubstackPublisher()
        self.twitter = TwitterPublisher()

        self._setup_logging()

    def _setup_logging(self):
        """设置日志"""
        log_file = settings.log_file
        log_level = settings.log_level

        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # 配置 loguru
        logger.remove()
        logger.add(
            sys.stderr,
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                   "<level>{message}</level>"
        )
        logger.add(
            log_file,
            rotation="10 MB",
            retention="1 week",
            level=log_level
        )

    def publish_article(
        self,
        article: NotionArticle,
        dry_run: bool = False,
        substack_method: str = "api"
    ) -> PublishingResult:
        """
        发布单篇文章的完整流程

        Args:
            article: Notion 文章
            dry_run: 是否只预览不发布
            substack_method: Substack 发布方式 (api/email/selenium)
        """
        logger.info(f"开始处理文章: {article.title}")

        try:
            # Step 1: 翻译
            logger.info("Step 1: 翻译文章...")
            translation = self.translator.translate_article(
                article.title,
                article.content
            )
            logger.info(f"翻译完成: {translation.title_translated}")

            if dry_run:
                return self._preview_result(article, translation)

            # Step 2: 发布到 Substack
            logger.info("Step 2: 发布到 Substack...")
            substack_post = SubstackPost(
                title=translation.title_translated,
                subtitle=f"Originally written in Chinese: {article.title}",
                content=translation.translated_text,
                is_draft=False
            )
            substack_result = self.substack.publish(
                substack_post,
                method=substack_method
            )

            if not substack_result.success:
                logger.error(f"Substack 发布失败: {substack_result.error}")
                return PublishingResult(
                    success=False,
                    article_title=article.title,
                    translated_title=translation.title_translated,
                    error=f"Substack 发布失败: {substack_result.error}"
                )

            logger.info(f"Substack 发布成功: {substack_result.post_url}")

            # Step 3: 发布到 Twitter
            logger.info("Step 3: 发布推文线程...")
            twitter_result = self.twitter.publish_article_as_thread(
                translation.title_translated,
                translation.translated_text,
                substack_result.post_url
            )

            if not twitter_result.success:
                logger.warning(f"Twitter 发布失败: {twitter_result.error}")
                # Twitter 失败不影响整体，继续更新 Notion

            # Step 4: 更新 Notion 状态
            logger.info("Step 4: 更新 Notion 状态...")
            self.notion.update_page_status(
                article.id,
                new_status="Published"
            )

            # 添加发布 URL
            self.notion.add_published_url(
                article.id,
                substack_result.post_url or "",
                twitter_result.thread_url or ""
            )

            return PublishingResult(
                success=True,
                article_title=article.title,
                translated_title=translation.title_translated,
                substack_url=substack_result.post_url or "",
                twitter_url=twitter_result.thread_url or "",
                details={
                    "substack": {
                        "method": substack_result.method,
                        "post_id": substack_result.post_id
                    },
                    "twitter": {
                        "tweet_count": len(twitter_result.tweet_ids),
                        "tweet_ids": twitter_result.tweet_ids
                    }
                }
            )

        except Exception as e:
            logger.exception(f"发布过程中出错: {e}")
            return PublishingResult(
                success=False,
                article_title=article.title,
                error=str(e)
            )

    def _preview_result(
        self,
        article: NotionArticle,
        translation: TranslationResult
    ) -> PublishingResult:
        """预览模式结果"""
        # 预览推文线程
        thread = self.twitter.preview_thread(
            translation.title_translated,
            translation.translated_text,
            "https://your-publication.substack.com/p/article-slug"
        )

        logger.info("\n" + "=" * 60)
        logger.info("预览模式 - 不会实际发布")
        logger.info("=" * 60)
        logger.info(f"\n原标题: {article.title}")
        logger.info(f"翻译标题: {translation.title_translated}")
        logger.info(f"\n翻译内容预览:\n{translation.translated_text[:500]}...")
        logger.info(f"\n推文线程 ({len(thread.tweets)} 条):")

        for tweet in thread.tweets:
            logger.info(f"\n--- Tweet {tweet.index}/{tweet.total} ---")
            logger.info(tweet.text)

        return PublishingResult(
            success=True,
            article_title=article.title,
            translated_title=translation.title_translated,
            details={
                "mode": "preview",
                "tweet_count": len(thread.tweets),
                "content_length": len(translation.translated_text)
            }
        )

    def publish_all_ready(
        self,
        dry_run: bool = False,
        substack_method: str = "api"
    ) -> list[PublishingResult]:
        """发布所有待发布的文章"""
        logger.info("获取待发布文章...")
        articles = self.notion.get_ready_to_publish_articles()

        if not articles:
            logger.info("没有待发布的文章")
            return []

        logger.info(f"找到 {len(articles)} 篇待发布文章")

        results = []
        for article in articles:
            result = self.publish_article(
                article,
                dry_run=dry_run,
                substack_method=substack_method
            )
            results.append(result)

            # 输出结果摘要
            if result.success:
                logger.info(f"✓ {result.article_title} 发布成功")
            else:
                logger.error(f"✗ {result.article_title} 发布失败: {result.error}")

        return results

    def publish_single(
        self,
        page_id: str,
        dry_run: bool = False,
        substack_method: str = "api"
    ) -> PublishingResult:
        """发布单篇指定文章"""
        logger.info(f"获取文章: {page_id}")
        article = self.notion.get_article(page_id)
        return self.publish_article(
            article,
            dry_run=dry_run,
            substack_method=substack_method
        )


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="Notion → Substack + Twitter 自动翻译发布工具"
    )

    parser.add_argument(
        "--mode",
        choices=["all", "single", "preview", "list"],
        default="all",
        help="运行模式: all(发布所有待发布), single(发布单篇), preview(预览), list(列出待发布)"
    )

    parser.add_argument(
        "--page-id",
        help="Notion 页面 ID (single 模式必需)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="试运行模式，不实际发布"
    )

    parser.add_argument(
        "--substack-method",
        choices=["api", "email", "selenium"],
        default="api",
        help="Substack 发布方式"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logger.level("DEBUG")

    publisher = AutoPublisher()

    if args.mode == "list":
        # 列出待发布文章
        articles = publisher.notion.get_ready_to_publish_articles()
        print(f"\n待发布文章 ({len(articles)} 篇):\n")
        for i, article in enumerate(articles, 1):
            print(f"{i}. {article.title}")
            print(f"   ID: {article.id}")
            print(f"   创建时间: {article.created_time}")
            print()

    elif args.mode == "single":
        if not args.page_id:
            print("错误: single 模式需要指定 --page-id")
            sys.exit(1)

        result = publisher.publish_single(
            args.page_id,
            dry_run=args.dry_run,
            substack_method=args.substack_method
        )
        _print_result(result)

    elif args.mode == "preview":
        if args.page_id:
            result = publisher.publish_single(
                args.page_id,
                dry_run=True,
                substack_method=args.substack_method
            )
            _print_result(result)
        else:
            results = publisher.publish_all_ready(dry_run=True)
            for result in results:
                _print_result(result)

    else:  # all
        results = publisher.publish_all_ready(
            dry_run=args.dry_run,
            substack_method=args.substack_method
        )

        # 输出总结
        print("\n" + "=" * 60)
        print("发布总结")
        print("=" * 60)
        success_count = sum(1 for r in results if r.success)
        print(f"成功: {success_count}/{len(results)}")

        for result in results:
            _print_result(result)


def _print_result(result: PublishingResult):
    """打印发布结果"""
    status = "✓" if result.success else "✗"
    print(f"\n{status} {result.article_title}")

    if result.translated_title:
        print(f"   英文标题: {result.translated_title}")

    if result.substack_url:
        print(f"   Substack: {result.substack_url}")

    if result.twitter_url:
        print(f"   Twitter: {result.twitter_url}")

    if result.error:
        print(f"   错误: {result.error}")

    if result.details:
        if result.details.get("tweet_count"):
            print(f"   推文数: {result.details['tweet_count']}")


if __name__ == "__main__":
    main()

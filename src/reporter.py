"""
Reporter module for sending news reports
"""
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List
from loguru import logger

from .config import settings
from .database import Database
from .models import NewsItem


class Reporter:
    """Reporter for sending news updates"""

    def __init__(self, db: Database):
        """
        Initialize reporter

        Args:
            db: Database instance
        """
        self.db = db

    def send_report(self):
        """
        Generate and send a report of unreported news items
        """
        # Get unreported items
        items = self.db.get_unreported_items()

        if not items:
            logger.info("No unreported items to send")
            return

        logger.info(f"Preparing report for {len(items)} items")

        # Generate report in configured format
        format_type = settings.report_format.lower()

        if format_type == 'html':
            content = self._generate_html_report(items)
            content_type = 'html'
        elif format_type == 'json':
            content = self._generate_json_report(items)
            content_type = 'plain'
        else:
            content = self._generate_text_report(items)
            content_type = 'plain'

        # Send via email if enabled
        if settings.email_enabled:
            success = self._send_email(content, content_type)
            if success:
                # Mark items as reported
                item_ids = [item.id for item in items]
                self.db.mark_as_reported(item_ids)
                logger.info(f"Report sent successfully for {len(items)} items")
            else:
                logger.error("Failed to send email report")
        else:
            # Just log the report
            logger.info("Email disabled. Report content:")
            logger.info(content)

            # Still mark as reported since we logged it
            item_ids = [item.id for item in items]
            self.db.mark_as_reported(item_ids)

    def _generate_text_report(self, items: List[NewsItem]) -> str:
        """
        Generate plain text report

        Args:
            items: List of NewsItem objects

        Returns:
            Report as plain text
        """
        lines = [
            "=" * 70,
            f"小米舆情监控报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 70,
            "",
            f"发现 {len(items)} 条新舆情",
            ""
        ]

        # Group by platform
        by_platform = {}
        for item in items:
            if item.platform not in by_platform:
                by_platform[item.platform] = []
            by_platform[item.platform].append(item)

        # Add items by platform
        for platform, platform_items in by_platform.items():
            lines.append(f"\n【{platform.upper()}】 - {len(platform_items)} 条")
            lines.append("-" * 70)

            for i, item in enumerate(platform_items, 1):
                lines.append(f"\n{i}. {item.title or '(无标题)'}")
                lines.append(f"   作者: {item.author}")
                lines.append(f"   时间: {item.published_at.strftime('%Y-%m-%d %H:%M')}")
                lines.append(f"   内容: {item.content[:200]}{'...' if len(item.content) > 200 else ''}")
                lines.append(f"   链接: {item.post_url}")
                lines.append(f"   互动: 👍{item.likes} 💬{item.comments} 🔄{item.shares}")
                lines.append("")

        lines.append("=" * 70)
        lines.append(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 70)

        return "\n".join(lines)

    def _generate_html_report(self, items: List[NewsItem]) -> str:
        """
        Generate HTML report

        Args:
            items: List of NewsItem objects

        Returns:
            Report as HTML
        """
        # Group by platform
        by_platform = {}
        for item in items:
            if item.platform not in by_platform:
                by_platform[item.platform] = []
            by_platform[item.platform].append(item)

        # Platform colors
        platform_colors = {
            'xiaohongshu': '#FF2442',
            'weibo': '#E6162D',
            'twitter': '#1DA1F2'
        }

        # Platform names
        platform_names = {
            'xiaohongshu': '小红书',
            'weibo': '微博',
            'twitter': 'Twitter/X'
        }

        # Build HTML
        html_parts = [
            '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 900px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: #f5f5f5;
                    }
                    .header {
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 30px;
                        border-radius: 10px;
                        margin-bottom: 30px;
                        text-align: center;
                    }
                    .header h1 {
                        margin: 0;
                        font-size: 28px;
                    }
                    .header p {
                        margin: 10px 0 0 0;
                        opacity: 0.9;
                    }
                    .summary {
                        background: white;
                        padding: 20px;
                        border-radius: 10px;
                        margin-bottom: 20px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    .platform-section {
                        background: white;
                        padding: 20px;
                        border-radius: 10px;
                        margin-bottom: 20px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    .platform-header {
                        border-left: 4px solid;
                        padding-left: 15px;
                        margin-bottom: 20px;
                    }
                    .platform-header h2 {
                        margin: 0;
                        font-size: 22px;
                    }
                    .item {
                        border-bottom: 1px solid #eee;
                        padding: 15px 0;
                    }
                    .item:last-child {
                        border-bottom: none;
                    }
                    .item-title {
                        font-size: 18px;
                        font-weight: bold;
                        margin-bottom: 8px;
                    }
                    .item-meta {
                        color: #666;
                        font-size: 14px;
                        margin-bottom: 8px;
                    }
                    .item-content {
                        margin-bottom: 10px;
                    }
                    .item-link {
                        display: inline-block;
                        padding: 6px 12px;
                        background: #667eea;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                        font-size: 14px;
                        margin-top: 5px;
                    }
                    .item-link:hover {
                        background: #5568d3;
                    }
                    .metrics {
                        display: flex;
                        gap: 15px;
                        margin-top: 10px;
                        font-size: 14px;
                        color: #666;
                    }
                    .metric {
                        display: flex;
                        align-items: center;
                        gap: 5px;
                    }
                    .footer {
                        text-align: center;
                        color: #666;
                        margin-top: 30px;
                        font-size: 14px;
                    }
                </style>
            </head>
            <body>
            ''',
            f'''
                <div class="header">
                    <h1>小米舆情监控报告</h1>
                    <p>{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
                </div>

                <div class="summary">
                    <h3>📊 本次报告汇总</h3>
                    <p>共发现 <strong>{len(items)}</strong> 条新舆情</p>
                    <ul>
            '''
        ]

        # Add platform summary
        for platform, platform_items in by_platform.items():
            name = platform_names.get(platform, platform)
            html_parts.append(f'<li>{name}: {len(platform_items)} 条</li>')

        html_parts.append('</ul></div>')

        # Add items by platform
        for platform, platform_items in by_platform.items():
            color = platform_colors.get(platform, '#333')
            name = platform_names.get(platform, platform)

            html_parts.append(f'''
                <div class="platform-section">
                    <div class="platform-header" style="border-color: {color}">
                        <h2>{name}</h2>
                    </div>
            ''')

            for item in platform_items:
                content_preview = item.content[:300] + ('...' if len(item.content) > 300 else '')

                html_parts.append(f'''
                    <div class="item">
                        <div class="item-title">{item.title or '(无标题)'}</div>
                        <div class="item-meta">
                            👤 {item.author} |
                            🕐 {item.published_at.strftime('%Y-%m-%d %H:%M')}
                        </div>
                        <div class="item-content">{content_preview}</div>
                        <div class="metrics">
                            <span class="metric">👍 {item.likes}</span>
                            <span class="metric">💬 {item.comments}</span>
                            <span class="metric">🔄 {item.shares}</span>
                        </div>
                        <a href="{item.post_url}" class="item-link" target="_blank">查看原文 →</a>
                    </div>
                ''')

            html_parts.append('</div>')

        # Footer
        html_parts.append(f'''
                <div class="footer">
                    <p>小米舆情监控系统自动生成</p>
                    <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </body>
            </html>
        ''')

        return ''.join(html_parts)

    def _generate_json_report(self, items: List[NewsItem]) -> str:
        """
        Generate JSON report

        Args:
            items: List of NewsItem objects

        Returns:
            Report as JSON string
        """
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_items': len(items),
            'items': [item.to_dict() for item in items]
        }

        return json.dumps(report, ensure_ascii=False, indent=2)

    def _send_email(self, content: str, content_type: str = 'plain') -> bool:
        """
        Send email report

        Args:
            content: Email content
            content_type: 'plain' or 'html'

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'小米舆情报告 - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
            msg['From'] = settings.email_from
            msg['To'] = settings.email_to

            # Attach content
            if content_type == 'html':
                part = MIMEText(content, 'html', 'utf-8')
            else:
                part = MIMEText(content, 'plain', 'utf-8')

            msg.attach(part)

            # Send via SMTP
            with smtplib.SMTP(settings.email_smtp_host, settings.email_smtp_port) as server:
                server.starttls()
                server.login(settings.email_from, settings.email_password)
                server.send_message(msg)

            logger.info(f"Email sent to {settings.email_to}")
            return True

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    def generate_and_print_report(self):
        """
        Generate and print report to console (for testing)
        """
        items = self.db.get_unreported_items()

        if not items:
            logger.info("No unreported items")
            return

        report = self._generate_text_report(items)
        print(report)

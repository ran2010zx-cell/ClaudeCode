"""
Substack 发布模块
支持多种发布方式：
1. 通过邮件发布 (Email-to-Post)
2. 通过 Selenium 浏览器自动化
3. 通过 Substack API (需要认证)
"""

import re
import time
import smtplib
import markdown
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from dataclasses import dataclass
from loguru import logger

from config import settings


@dataclass
class SubstackPost:
    """Substack 文章数据"""
    title: str
    content: str  # Markdown 格式
    subtitle: Optional[str] = None
    is_draft: bool = False
    audience: str = "everyone"  # everyone, paid, founding
    section_id: Optional[str] = None


@dataclass
class PublishResult:
    """发布结果"""
    success: bool
    post_url: Optional[str] = None
    post_id: Optional[str] = None
    error: Optional[str] = None
    method: str = ""


class SubstackPublisher:
    """Substack 发布器"""

    def __init__(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        publication_url: Optional[str] = None
    ):
        self.email = email or settings.substack.email
        self.password = password or settings.substack.password
        self.publication_url = publication_url or settings.substack.publication_url

        # 提取 publication name
        self.publication_name = self._extract_publication_name()

    def _extract_publication_name(self) -> str:
        """从 URL 提取出版物名称"""
        if not self.publication_url:
            return ""
        # 从 https://xxx.substack.com 提取 xxx
        match = re.match(r"https?://([^.]+)\.substack\.com", self.publication_url)
        if match:
            return match.group(1)
        return ""

    def publish_via_email(
        self,
        post: SubstackPost,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None
    ) -> PublishResult:
        """
        通过邮件发布到 Substack

        Substack 支持 Email-to-Post 功能，需要在设置中启用并获取专用邮箱地址。
        发送邮件到 post@<publication>.substack.com

        注意：这需要你在 Substack 后台启用 Email-to-Post 功能
        """
        if not self.publication_name:
            return PublishResult(
                success=False,
                error="未配置 publication URL",
                method="email"
            )

        # Substack Email-to-Post 地址
        to_email = f"post@{self.publication_name}.substack.com"

        # 转换 Markdown 为 HTML
        html_content = markdown.markdown(
            post.content,
            extensions=['tables', 'fenced_code', 'codehilite']
        )

        # 构建邮件
        msg = MIMEMultipart('alternative')
        msg['Subject'] = post.title
        msg['From'] = smtp_user or self.email
        msg['To'] = to_email

        # 添加副标题（如果有）
        if post.subtitle:
            html_content = f"<p><em>{post.subtitle}</em></p>\n{html_content}"

        # 添加纯文本和 HTML 版本
        text_part = MIMEText(post.content, 'plain', 'utf-8')
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(text_part)
        msg.attach(html_part)

        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user or self.email, smtp_password or self.password)
                server.sendmail(
                    smtp_user or self.email,
                    to_email,
                    msg.as_string()
                )

            logger.info(f"邮件已发送到 {to_email}")
            return PublishResult(
                success=True,
                post_url=f"{self.publication_url}/p/{self._slugify(post.title)}",
                method="email"
            )
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return PublishResult(
                success=False,
                error=str(e),
                method="email"
            )

    def publish_via_api(self, post: SubstackPost) -> PublishResult:
        """
        通过 Substack API 发布

        注意：Substack 没有公开的 API，这里使用的是逆向工程的接口，
        可能随时失效。建议使用 Selenium 方式作为备选。
        """
        import requests

        # 首先需要登录获取 session
        session = requests.Session()

        try:
            # 登录
            login_url = "https://substack.com/api/v1/login"
            login_data = {
                "email": self.email,
                "password": self.password,
                "captcha_response": None
            }

            login_response = session.post(login_url, json=login_data)
            if login_response.status_code != 200:
                return PublishResult(
                    success=False,
                    error=f"登录失败: {login_response.text}",
                    method="api"
                )

            # 获取 publication ID
            pub_url = f"https://{self.publication_name}.substack.com/api/v1/publication"
            pub_response = session.get(pub_url)
            if pub_response.status_code != 200:
                return PublishResult(
                    success=False,
                    error=f"获取 publication 信息失败",
                    method="api"
                )

            pub_data = pub_response.json()
            pub_id = pub_data.get("id")

            # 创建草稿
            draft_url = f"https://{self.publication_name}.substack.com/api/v1/drafts"
            draft_data = {
                "draft_title": post.title,
                "draft_subtitle": post.subtitle or "",
                "draft_body": self._markdown_to_draft_body(post.content),
                "audience": post.audience
            }

            draft_response = session.post(draft_url, json=draft_data)
            if draft_response.status_code != 200:
                return PublishResult(
                    success=False,
                    error=f"创建草稿失败: {draft_response.text}",
                    method="api"
                )

            draft_result = draft_response.json()
            draft_id = draft_result.get("id")

            if post.is_draft:
                return PublishResult(
                    success=True,
                    post_id=draft_id,
                    post_url=f"{self.publication_url}/publish/post/{draft_id}",
                    method="api"
                )

            # 发布
            publish_url = f"https://{self.publication_name}.substack.com/api/v1/drafts/{draft_id}/publish"
            publish_response = session.post(publish_url, json={"send": True})

            if publish_response.status_code == 200:
                publish_result = publish_response.json()
                return PublishResult(
                    success=True,
                    post_id=draft_id,
                    post_url=publish_result.get("canonical_url", ""),
                    method="api"
                )
            else:
                return PublishResult(
                    success=False,
                    error=f"发布失败: {publish_response.text}",
                    method="api"
                )

        except Exception as e:
            logger.error(f"API 发布失败: {e}")
            return PublishResult(
                success=False,
                error=str(e),
                method="api"
            )

    def publish_via_selenium(
        self,
        post: SubstackPost,
        headless: bool = True
    ) -> PublishResult:
        """
        通过 Selenium 浏览器自动化发布
        这是最可靠的方式，但需要安装 Chrome/ChromeDriver
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.options import Options
        except ImportError:
            return PublishResult(
                success=False,
                error="请安装 selenium: pip install selenium",
                method="selenium"
            )

        options = Options()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = None
        try:
            driver = webdriver.Chrome(options=options)
            wait = WebDriverWait(driver, 20)

            # 访问登录页面
            login_url = f"https://{self.publication_name}.substack.com/sign-in"
            driver.get(login_url)

            # 输入邮箱
            email_input = wait.until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            email_input.send_keys(self.email)

            # 点击继续
            continue_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            continue_btn.click()

            # 输入密码（如果需要）
            try:
                password_input = wait.until(
                    EC.presence_of_element_located((By.NAME, "password"))
                )
                password_input.send_keys(self.password)

                login_btn = driver.find_element(
                    By.CSS_SELECTOR, "button[type='submit']"
                )
                login_btn.click()
            except Exception:
                # 可能是使用魔法链接登录
                logger.warning("可能需要使用魔法链接登录，请检查邮箱")
                pass

            time.sleep(3)

            # 进入发布页面
            publish_url = f"https://{self.publication_name}.substack.com/publish/post"
            driver.get(publish_url)

            time.sleep(2)

            # 输入标题
            title_input = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "[data-testid='post-title-input'], .post-title-input, textarea[placeholder*='Title']")
                )
            )
            title_input.clear()
            title_input.send_keys(post.title)

            # 输入副标题（如果有）
            if post.subtitle:
                try:
                    subtitle_input = driver.find_element(
                        By.CSS_SELECTOR,
                        "[data-testid='post-subtitle-input'], .post-subtitle-input"
                    )
                    subtitle_input.send_keys(post.subtitle)
                except Exception:
                    pass

            # 输入内容
            # Substack 使用富文本编辑器，需要特殊处理
            content_area = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "[data-testid='post-body'], .ProseMirror, .post-content")
                )
            )

            # 使用 JavaScript 设置内容
            html_content = markdown.markdown(post.content)
            driver.execute_script(
                "arguments[0].innerHTML = arguments[1]",
                content_area,
                html_content
            )

            time.sleep(2)

            if post.is_draft:
                # 保存草稿
                logger.info("草稿已保存")
                return PublishResult(
                    success=True,
                    post_url=driver.current_url,
                    method="selenium"
                )

            # 点击发布按钮
            publish_btn = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "[data-testid='publish-button'], button:contains('Publish')")
                )
            )
            publish_btn.click()

            time.sleep(2)

            # 确认发布
            confirm_btn = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "[data-testid='confirm-publish'], .publish-confirm-button")
                )
            )
            confirm_btn.click()

            time.sleep(3)

            # 获取发布后的 URL
            post_url = driver.current_url

            return PublishResult(
                success=True,
                post_url=post_url,
                method="selenium"
            )

        except Exception as e:
            logger.error(f"Selenium 发布失败: {e}")
            return PublishResult(
                success=False,
                error=str(e),
                method="selenium"
            )
        finally:
            if driver:
                driver.quit()

    def publish(
        self,
        post: SubstackPost,
        method: str = "api"
    ) -> PublishResult:
        """
        发布文章到 Substack

        Args:
            post: 文章数据
            method: 发布方式 - "api", "email", "selenium"
        """
        logger.info(f"使用 {method} 方式发布文章: {post.title}")

        if method == "email":
            return self.publish_via_email(post)
        elif method == "selenium":
            return self.publish_via_selenium(post)
        else:
            # 默认使用 API，失败后降级到 selenium
            result = self.publish_via_api(post)
            if not result.success:
                logger.warning("API 发布失败，尝试使用 Selenium")
                result = self.publish_via_selenium(post)
            return result

    def _markdown_to_draft_body(self, markdown_text: str) -> Dict[str, Any]:
        """
        将 Markdown 转换为 Substack 草稿格式
        Substack 使用 ProseMirror 编辑器格式
        """
        # 简化处理：转换为 HTML，让 Substack 自己解析
        html = markdown.markdown(
            markdown_text,
            extensions=['tables', 'fenced_code']
        )

        return {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": html
                        }
                    ]
                }
            ]
        }

    def _slugify(self, text: str) -> str:
        """将文本转换为 URL 友好的 slug"""
        # 简单实现：小写 + 替换空格为连字符
        slug = text.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        return slug.strip('-')


# 测试代码
if __name__ == "__main__":
    publisher = SubstackPublisher()

    test_post = SubstackPost(
        title="Test Article",
        subtitle="A test subtitle",
        content="""
# Hello World

This is a test article with **bold** and *italic* text.

## Features

- Feature 1
- Feature 2
- Feature 3

```python
print("Hello, World!")
```

Thanks for reading!
""",
        is_draft=True
    )

    # 测试发布（草稿模式）
    result = publisher.publish(test_post, method="api")
    print(f"发布结果: {result}")

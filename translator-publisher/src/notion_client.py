"""
Notion API 客户端
用于从 Notion 数据库获取文章
"""

import requests
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger

from config import settings


@dataclass
class NotionArticle:
    """Notion 文章数据结构"""
    id: str
    title: str
    content: str  # Markdown 格式
    created_time: datetime
    last_edited_time: datetime
    properties: Dict[str, Any] = field(default_factory=dict)
    url: str = ""
    status: str = ""  # 用于跟踪发布状态


class NotionClient:
    """Notion API 客户端"""

    BASE_URL = "https://api.notion.com/v1"
    NOTION_VERSION = "2022-06-28"

    def __init__(self, api_key: Optional[str] = None, database_id: Optional[str] = None):
        self.api_key = api_key or settings.notion.api_key
        self.database_id = database_id or settings.notion.database_id
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": self.NOTION_VERSION
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """发送 API 请求"""
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Notion API 请求失败: {e}")
            raise

    def get_database_pages(
        self,
        filter_params: Optional[Dict] = None,
        sorts: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """获取数据库中的所有页面"""
        endpoint = f"databases/{self.database_id}/query"
        data = {}

        if filter_params:
            data["filter"] = filter_params

        if sorts:
            data["sorts"] = sorts
        else:
            # 默认按创建时间降序排列
            data["sorts"] = [{"timestamp": "created_time", "direction": "descending"}]

        result = self._make_request("POST", endpoint, data)
        return result.get("results", [])

    def get_page(self, page_id: str) -> Dict[str, Any]:
        """获取单个页面信息"""
        endpoint = f"pages/{page_id}"
        return self._make_request("GET", endpoint)

    def get_page_blocks(self, page_id: str) -> List[Dict]:
        """获取页面的所有内容块"""
        endpoint = f"blocks/{page_id}/children"
        result = self._make_request("GET", endpoint)
        blocks = result.get("results", [])

        # 递归获取嵌套块
        all_blocks = []
        for block in blocks:
            all_blocks.append(block)
            if block.get("has_children"):
                child_blocks = self.get_page_blocks(block["id"])
                all_blocks.extend(child_blocks)

        return all_blocks

    def blocks_to_markdown(self, blocks: List[Dict]) -> str:
        """将 Notion 块转换为 Markdown 格式"""
        markdown_parts = []

        for block in blocks:
            block_type = block.get("type")
            block_content = block.get(block_type, {})

            md_text = self._convert_block_to_markdown(block_type, block_content)
            if md_text:
                markdown_parts.append(md_text)

        return "\n\n".join(markdown_parts)

    def _convert_block_to_markdown(
        self,
        block_type: str,
        content: Dict
    ) -> str:
        """将单个块转换为 Markdown"""
        text = self._extract_rich_text(content.get("rich_text", []))

        converters = {
            "paragraph": lambda: text,
            "heading_1": lambda: f"# {text}",
            "heading_2": lambda: f"## {text}",
            "heading_3": lambda: f"### {text}",
            "bulleted_list_item": lambda: f"- {text}",
            "numbered_list_item": lambda: f"1. {text}",
            "to_do": lambda: f"- [{'x' if content.get('checked') else ' '}] {text}",
            "toggle": lambda: f"<details><summary>{text}</summary></details>",
            "code": lambda: f"```{content.get('language', '')}\n{text}\n```",
            "quote": lambda: f"> {text}",
            "callout": lambda: f"> {content.get('icon', {}).get('emoji', '💡')} {text}",
            "divider": lambda: "---",
            "image": lambda: self._convert_image(content),
            "video": lambda: self._convert_video(content),
            "bookmark": lambda: f"[{content.get('url', '')}]({content.get('url', '')})",
            "embed": lambda: f"[嵌入链接]({content.get('url', '')})",
            "equation": lambda: f"$${content.get('expression', '')}$$",
            "table_of_contents": lambda: "[TOC]",
        }

        converter = converters.get(block_type)
        if converter:
            return converter()
        return ""

    def _extract_rich_text(self, rich_text: List[Dict]) -> str:
        """从富文本数组中提取纯文本和格式"""
        parts = []
        for item in rich_text:
            text = item.get("plain_text", "")
            annotations = item.get("annotations", {})

            # 应用格式
            if annotations.get("bold"):
                text = f"**{text}**"
            if annotations.get("italic"):
                text = f"*{text}*"
            if annotations.get("strikethrough"):
                text = f"~~{text}~~"
            if annotations.get("code"):
                text = f"`{text}`"

            # 处理链接
            href = item.get("href")
            if href:
                text = f"[{text}]({href})"

            parts.append(text)

        return "".join(parts)

    def _convert_image(self, content: Dict) -> str:
        """转换图片块"""
        image_type = content.get("type")  # file 或 external
        if image_type == "file":
            url = content.get("file", {}).get("url", "")
        else:
            url = content.get("external", {}).get("url", "")

        caption = self._extract_rich_text(content.get("caption", []))
        return f"![{caption}]({url})"

    def _convert_video(self, content: Dict) -> str:
        """转换视频块"""
        video_type = content.get("type")
        if video_type == "file":
            url = content.get("file", {}).get("url", "")
        else:
            url = content.get("external", {}).get("url", "")
        return f"[视频链接]({url})"

    def get_article(self, page_id: str) -> NotionArticle:
        """获取单篇文章的完整内容"""
        # 获取页面基本信息
        page = self.get_page(page_id)

        # 获取页面内容块
        blocks = self.get_page_blocks(page_id)

        # 转换为 Markdown
        content = self.blocks_to_markdown(blocks)

        # 提取标题
        title = self._extract_title(page)

        # 提取状态（如果有）
        status = self._extract_property(page, "Status", "status")

        return NotionArticle(
            id=page_id,
            title=title,
            content=content,
            created_time=datetime.fromisoformat(
                page["created_time"].replace("Z", "+00:00")
            ),
            last_edited_time=datetime.fromisoformat(
                page["last_edited_time"].replace("Z", "+00:00")
            ),
            properties=page.get("properties", {}),
            url=page.get("url", ""),
            status=status
        )

    def _extract_title(self, page: Dict) -> str:
        """从页面属性中提取标题"""
        properties = page.get("properties", {})

        # 尝试常见的标题属性名
        for title_key in ["Name", "Title", "标题", "name", "title"]:
            if title_key in properties:
                title_prop = properties[title_key]
                if title_prop.get("type") == "title":
                    title_items = title_prop.get("title", [])
                    return self._extract_rich_text(title_items)

        return "无标题"

    def _extract_property(
        self,
        page: Dict,
        property_name: str,
        property_type: str
    ) -> str:
        """提取页面属性值"""
        properties = page.get("properties", {})
        prop = properties.get(property_name, {})

        if prop.get("type") == property_type:
            if property_type == "status":
                status_obj = prop.get("status", {})
                return status_obj.get("name", "") if status_obj else ""
            elif property_type == "select":
                select_obj = prop.get("select", {})
                return select_obj.get("name", "") if select_obj else ""

        return ""

    def get_ready_to_publish_articles(
        self,
        status_property: str = "Status",
        ready_status: str = "Ready to Publish"
    ) -> List[NotionArticle]:
        """获取所有准备发布的文章"""
        filter_params = {
            "property": status_property,
            "status": {
                "equals": ready_status
            }
        }

        pages = self.get_database_pages(filter_params=filter_params)
        articles = []

        for page in pages:
            try:
                article = self.get_article(page["id"])
                articles.append(article)
            except Exception as e:
                logger.error(f"获取文章失败 {page['id']}: {e}")

        return articles

    def update_page_status(
        self,
        page_id: str,
        status_property: str = "Status",
        new_status: str = "Published"
    ) -> bool:
        """更新页面状态"""
        endpoint = f"pages/{page_id}"
        data = {
            "properties": {
                status_property: {
                    "status": {
                        "name": new_status
                    }
                }
            }
        }

        try:
            self._make_request("PATCH", endpoint, data)
            logger.info(f"页面 {page_id} 状态已更新为 {new_status}")
            return True
        except Exception as e:
            logger.error(f"更新页面状态失败: {e}")
            return False

    def add_published_url(
        self,
        page_id: str,
        substack_url: str,
        twitter_url: str,
        url_property: str = "Published URLs"
    ) -> bool:
        """在页面中添加已发布的 URL"""
        endpoint = f"pages/{page_id}"
        data = {
            "properties": {
                url_property: {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"Substack: {substack_url}\nTwitter: {twitter_url}"
                            }
                        }
                    ]
                }
            }
        }

        try:
            self._make_request("PATCH", endpoint, data)
            logger.info(f"已为页面 {page_id} 添加发布 URL")
            return True
        except Exception as e:
            logger.error(f"添加发布 URL 失败: {e}")
            return False


# 测试代码
if __name__ == "__main__":
    client = NotionClient()

    # 测试获取数据库页面
    pages = client.get_database_pages()
    print(f"找到 {len(pages)} 个页面")

    if pages:
        # 测试获取第一篇文章
        first_page_id = pages[0]["id"]
        article = client.get_article(first_page_id)
        print(f"标题: {article.title}")
        print(f"内容预览: {article.content[:200]}...")

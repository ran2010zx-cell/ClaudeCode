"""
Twitter/X 发布模块
将文章智能拆分为推文线程并发布
"""

import re
import time
from typing import Optional, List, Tuple
from dataclasses import dataclass, field
from loguru import logger

from config import settings


@dataclass
class Tweet:
    """单条推文"""
    text: str
    index: int = 0
    total: int = 0
    is_last: bool = False
    reply_to_id: Optional[str] = None


@dataclass
class TweetThread:
    """推文线程"""
    tweets: List[Tweet] = field(default_factory=list)
    title: str = ""
    source_url: str = ""  # Substack 文章 URL


@dataclass
class TwitterPublishResult:
    """发布结果"""
    success: bool
    thread_url: Optional[str] = None
    tweet_ids: List[str] = field(default_factory=list)
    error: Optional[str] = None


class ArticleToThreadConverter:
    """将文章转换为推文线程"""

    def __init__(
        self,
        max_tweet_length: int = 280,
        reserve_for_counter: int = 10,  # 预留给 "1/10" 这样的计数器
        reserve_for_link: int = 25  # 预留给 t.co 短链接
    ):
        self.max_tweet_length = max_tweet_length
        self.reserve_for_counter = reserve_for_counter
        self.reserve_for_link = reserve_for_link
        self.effective_length = max_tweet_length - reserve_for_counter

    def convert(
        self,
        title: str,
        content: str,
        substack_url: str = ""
    ) -> TweetThread:
        """
        将文章转换为推文线程

        策略:
        1. 第一条推文: 标题 + 简介
        2. 中间推文: 文章主要内容
        3. 最后一条: 总结 + Substack 链接
        """
        # 清理内容
        clean_content = self._clean_content(content)

        # 提取段落
        paragraphs = self._extract_paragraphs(clean_content)

        # 构建推文
        tweets = []

        # 第一条: 标题 + 开头
        first_tweet_text = self._build_first_tweet(title, paragraphs)
        tweets.append(first_tweet_text)

        # 中间内容
        remaining_paragraphs = self._get_remaining_content(
            paragraphs,
            first_tweet_text
        )
        middle_tweets = self._split_into_tweets(remaining_paragraphs)
        tweets.extend(middle_tweets)

        # 最后一条: 链接到 Substack
        if substack_url:
            last_tweet = self._build_last_tweet(substack_url, title)
            tweets.append(last_tweet)

        # 创建 Tweet 对象
        total = len(tweets)
        thread_tweets = []
        for i, text in enumerate(tweets):
            tweet = Tweet(
                text=text,
                index=i + 1,
                total=total,
                is_last=(i == total - 1)
            )
            thread_tweets.append(tweet)

        return TweetThread(
            tweets=thread_tweets,
            title=title,
            source_url=substack_url
        )

    def _clean_content(self, content: str) -> str:
        """清理 Markdown 内容，保留关键格式"""
        # 移除图片
        content = re.sub(r'!\[.*?\]\(.*?\)', '', content)

        # 移除链接但保留文本
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)

        # 移除代码块
        content = re.sub(r'```[\s\S]*?```', '[代码示例]', content)

        # 移除行内代码
        content = re.sub(r'`([^`]+)`', r'\1', content)

        # 移除标题标记
        content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)

        # 移除粗体/斜体标记
        content = re.sub(r'\*\*([^\*]+)\*\*', r'\1', content)
        content = re.sub(r'\*([^\*]+)\*', r'\1', content)
        content = re.sub(r'__([^_]+)__', r'\1', content)
        content = re.sub(r'_([^_]+)_', r'\1', content)

        # 处理列表项
        content = re.sub(r'^[-*]\s+', '• ', content, flags=re.MULTILINE)
        content = re.sub(r'^\d+\.\s+', '• ', content, flags=re.MULTILINE)

        # 移除多余空行
        content = re.sub(r'\n{3,}', '\n\n', content)

        return content.strip()

    def _extract_paragraphs(self, content: str) -> List[str]:
        """提取段落"""
        paragraphs = content.split('\n\n')
        return [p.strip() for p in paragraphs if p.strip()]

    def _build_first_tweet(
        self,
        title: str,
        paragraphs: List[str]
    ) -> str:
        """构建第一条推文"""
        # 格式: 🧵 标题\n\n开头内容
        header = f"🧵 {title}\n\n"
        available_length = self.effective_length - len(header)

        if paragraphs:
            first_para = paragraphs[0]
            if len(first_para) <= available_length:
                return header + first_para
            else:
                # 截断到句子边界
                truncated = self._truncate_to_sentence(
                    first_para,
                    available_length - 3
                )
                return header + truncated + "..."

        return header.strip()

    def _get_remaining_content(
        self,
        paragraphs: List[str],
        first_tweet: str
    ) -> str:
        """获取除第一条推文外的剩余内容"""
        if not paragraphs:
            return ""

        # 检查第一段是否被完整使用
        first_para = paragraphs[0]
        if first_para in first_tweet:
            remaining = paragraphs[1:]
        else:
            # 第一段被截断，从截断点继续
            used_text = first_tweet.split('\n\n', 1)[-1].rstrip('...')
            if first_para.startswith(used_text):
                remaining_first = first_para[len(used_text):].strip()
                remaining = [remaining_first] + paragraphs[1:] if remaining_first else paragraphs[1:]
            else:
                remaining = paragraphs[1:]

        return '\n\n'.join(remaining)

    def _split_into_tweets(self, content: str) -> List[str]:
        """将内容拆分为多条推文"""
        if not content:
            return []

        tweets = []
        sentences = self._split_into_sentences(content)

        current_tweet = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # 检查是否可以添加到当前推文
            potential_text = current_tweet + (" " if current_tweet else "") + sentence

            if len(potential_text) <= self.effective_length:
                current_tweet = potential_text
            else:
                # 当前推文已满，保存并开始新推文
                if current_tweet:
                    tweets.append(current_tweet)

                # 如果单个句子超长，需要强制拆分
                if len(sentence) > self.effective_length:
                    split_parts = self._force_split(sentence, self.effective_length)
                    tweets.extend(split_parts[:-1])
                    current_tweet = split_parts[-1]
                else:
                    current_tweet = sentence

        # 添加最后一条
        if current_tweet:
            tweets.append(current_tweet)

        return tweets

    def _split_into_sentences(self, text: str) -> List[str]:
        """将文本拆分为句子"""
        # 支持中英文标点
        sentence_endings = r'([.!?。！？\n])'
        parts = re.split(sentence_endings, text)

        sentences = []
        i = 0
        while i < len(parts):
            sentence = parts[i]
            # 将标点符号附加到句子末尾
            if i + 1 < len(parts) and re.match(sentence_endings, parts[i + 1]):
                sentence += parts[i + 1]
                i += 2
            else:
                i += 1

            sentence = sentence.strip()
            if sentence:
                sentences.append(sentence)

        return sentences

    def _truncate_to_sentence(self, text: str, max_length: int) -> str:
        """截断文本到最近的句子边界"""
        if len(text) <= max_length:
            return text

        sentences = self._split_into_sentences(text)
        result = ""

        for sentence in sentences:
            potential = result + (" " if result else "") + sentence
            if len(potential) <= max_length:
                result = potential
            else:
                break

        # 如果没有完整句子，则强制截断
        if not result:
            result = text[:max_length].rsplit(' ', 1)[0]

        return result

    def _force_split(self, text: str, max_length: int) -> List[str]:
        """强制拆分超长文本"""
        parts = []
        while text:
            if len(text) <= max_length:
                parts.append(text)
                break

            # 尝试在空格处拆分
            split_point = text[:max_length].rfind(' ')
            if split_point == -1:
                split_point = max_length

            parts.append(text[:split_point])
            text = text[split_point:].strip()

        return parts

    def _build_last_tweet(self, substack_url: str, title: str) -> str:
        """构建最后一条推文（包含链接）"""
        # 格式: 阅读完整文章 + 链接
        templates = [
            f"📖 Read the full article:\n{substack_url}",
            f"👆 That's the thread! Read the full piece here:\n{substack_url}",
            f"🔗 Full article: {substack_url}\n\nLike & RT if you found this valuable!",
        ]

        return templates[0]  # 使用简洁模板


class TwitterPublisher:
    """Twitter/X 发布器"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_token_secret: Optional[str] = None,
        bearer_token: Optional[str] = None
    ):
        self.api_key = api_key or settings.twitter.api_key
        self.api_secret = api_secret or settings.twitter.api_secret
        self.access_token = access_token or settings.twitter.access_token
        self.access_token_secret = access_token_secret or settings.twitter.access_token_secret
        self.bearer_token = bearer_token or settings.twitter.bearer_token

        self.thread_delay = settings.twitter.thread_delay_seconds
        self.client = None
        self._init_client()

    def _init_client(self):
        """初始化 Twitter 客户端"""
        try:
            import tweepy

            # 优先使用 OAuth 1.0a（支持发推）
            if all([
                self.api_key,
                self.api_secret,
                self.access_token,
                self.access_token_secret
            ]):
                self.client = tweepy.Client(
                    consumer_key=self.api_key,
                    consumer_secret=self.api_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_token_secret
                )
                logger.info("Twitter 客户端初始化成功 (OAuth 1.0a)")
            elif self.bearer_token:
                self.client = tweepy.Client(bearer_token=self.bearer_token)
                logger.warning("使用 Bearer Token，只能读取，不能发推")
            else:
                logger.warning("未配置 Twitter API 凭证")

        except ImportError:
            logger.error("请安装 tweepy: pip install tweepy")

    def publish_thread(self, thread: TweetThread) -> TwitterPublishResult:
        """发布推文线程"""
        if not self.client:
            return TwitterPublishResult(
                success=False,
                error="Twitter 客户端未初始化"
            )

        tweet_ids = []
        reply_to_id = None

        try:
            for i, tweet in enumerate(thread.tweets):
                # 添加计数器
                counter = f" [{tweet.index}/{tweet.total}]"
                text = tweet.text

                # 确保不超长
                if len(text) + len(counter) <= 280:
                    text = text + counter

                logger.info(f"发布推文 {tweet.index}/{tweet.total}: {text[:50]}...")

                # 发布推文
                if reply_to_id:
                    response = self.client.create_tweet(
                        text=text,
                        in_reply_to_tweet_id=reply_to_id
                    )
                else:
                    response = self.client.create_tweet(text=text)

                tweet_id = response.data['id']
                tweet_ids.append(tweet_id)
                reply_to_id = tweet_id

                # 延迟，避免 rate limit
                if i < len(thread.tweets) - 1:
                    time.sleep(self.thread_delay)

            # 构建线程 URL
            thread_url = f"https://twitter.com/i/status/{tweet_ids[0]}"

            logger.info(f"推文线程发布成功: {thread_url}")
            return TwitterPublishResult(
                success=True,
                thread_url=thread_url,
                tweet_ids=tweet_ids
            )

        except Exception as e:
            logger.error(f"发布推文失败: {e}")
            return TwitterPublishResult(
                success=False,
                tweet_ids=tweet_ids,
                error=str(e)
            )

    def publish_article_as_thread(
        self,
        title: str,
        content: str,
        substack_url: str = ""
    ) -> TwitterPublishResult:
        """将文章作为推文线程发布"""
        # 转换为线程
        converter = ArticleToThreadConverter(
            max_tweet_length=settings.twitter.max_tweet_length
        )
        thread = converter.convert(title, content, substack_url)

        logger.info(f"文章已转换为 {len(thread.tweets)} 条推文")

        # 发布
        return self.publish_thread(thread)

    def preview_thread(
        self,
        title: str,
        content: str,
        substack_url: str = ""
    ) -> TweetThread:
        """预览推文线程（不发布）"""
        converter = ArticleToThreadConverter(
            max_tweet_length=settings.twitter.max_tweet_length
        )
        return converter.convert(title, content, substack_url)


# 测试代码
if __name__ == "__main__":
    # 测试文章转推文
    test_title = "The Future of AI"
    test_content = """
Artificial Intelligence is transforming our world in unprecedented ways. From smartphones to autonomous vehicles, AI has permeated every aspect of our lives.

The rise of large language models like GPT and Claude represents a significant leap forward. These models can understand context, generate human-like text, and even write code.

Key trends to watch:

• Multimodal AI combining text, images, and audio
• AI agents that can complete complex tasks autonomously
• Edge AI bringing intelligence to devices
• AI safety and alignment becoming critical concerns

The implications are profound. Jobs will change, new industries will emerge, and our relationship with technology will evolve.

As we navigate this transformation, it's crucial to develop AI responsibly. We must consider ethical implications, ensure equitable access, and maintain human oversight.

The future is not predetermined. It's up to us to shape it wisely.
"""

    # 预览线程
    publisher = TwitterPublisher()
    thread = publisher.preview_thread(
        test_title,
        test_content,
        "https://example.substack.com/p/the-future-of-ai"
    )

    print(f"共 {len(thread.tweets)} 条推文:\n")
    for tweet in thread.tweets:
        print(f"--- Tweet {tweet.index}/{tweet.total} ---")
        print(tweet.text)
        print(f"(字符数: {len(tweet.text)})")
        print()

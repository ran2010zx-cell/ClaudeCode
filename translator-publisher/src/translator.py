"""
翻译模块
支持 OpenAI 和 Anthropic (Claude) 两种翻译提供商
"""

import re
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
from dataclasses import dataclass
from loguru import logger

from config import settings


@dataclass
class TranslationResult:
    """翻译结果"""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    provider: str
    title_original: str = ""
    title_translated: str = ""


class BaseTranslator(ABC):
    """翻译器基类"""

    def __init__(
        self,
        source_language: str = "中文",
        target_language: str = "English"
    ):
        self.source_language = source_language
        self.target_language = target_language

    @abstractmethod
    def translate(self, text: str) -> str:
        """翻译文本"""
        pass

    @abstractmethod
    def translate_with_title(
        self,
        title: str,
        content: str
    ) -> Tuple[str, str]:
        """翻译标题和内容"""
        pass

    def _get_translation_prompt(self, text: str) -> str:
        """获取翻译提示词"""
        return f"""You are a professional translator. Please translate the following text from {self.source_language} to {self.target_language}.

Requirements:
1. Maintain the original meaning and tone
2. Preserve all Markdown formatting (headers, lists, links, code blocks, etc.)
3. Keep technical terms accurate
4. Make the translation natural and fluent
5. Do not add any explanations or notes, only output the translation

Text to translate:
{text}"""

    def _get_article_translation_prompt(
        self,
        title: str,
        content: str
    ) -> str:
        """获取文章翻译提示词"""
        return f"""You are a professional translator specializing in article translation. Please translate the following article from {self.source_language} to {self.target_language}.

Requirements:
1. Translate both the title and the content
2. Maintain the original meaning, tone, and style
3. Preserve all Markdown formatting (headers, lists, links, code blocks, images, etc.)
4. Keep technical terms accurate
5. Make the translation natural, fluent, and engaging for readers
6. Do not add any explanations or notes

Please output in the following format:
TITLE: [translated title]
---
[translated content]

Article to translate:

Title: {title}

Content:
{content}"""


class OpenAITranslator(BaseTranslator):
    """OpenAI 翻译器"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        source_language: str = "中文",
        target_language: str = "English"
    ):
        super().__init__(source_language, target_language)
        self.api_key = api_key or settings.translator.openai_api_key
        self.model = model or settings.translator.openai_model

        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("请安装 openai 库: pip install openai")

    def translate(self, text: str) -> str:
        """使用 OpenAI 翻译文本"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional translator. Translate from {self.source_language} to {self.target_language}. Only output the translation, nothing else."
                    },
                    {
                        "role": "user",
                        "content": self._get_translation_prompt(text)
                    }
                ],
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI 翻译失败: {e}")
            raise

    def translate_with_title(
        self,
        title: str,
        content: str
    ) -> Tuple[str, str]:
        """翻译标题和内容"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional article translator. Follow the output format exactly."
                    },
                    {
                        "role": "user",
                        "content": self._get_article_translation_prompt(title, content)
                    }
                ],
                temperature=0.3
            )

            result = response.choices[0].message.content.strip()
            return self._parse_translation_result(result)
        except Exception as e:
            logger.error(f"OpenAI 翻译失败: {e}")
            raise

    def _parse_translation_result(self, result: str) -> Tuple[str, str]:
        """解析翻译结果"""
        # 尝试解析 TITLE: xxx --- content 格式
        title_match = re.match(r"TITLE:\s*(.+?)\n---\n(.+)", result, re.DOTALL)
        if title_match:
            return title_match.group(1).strip(), title_match.group(2).strip()

        # 如果解析失败，尝试其他格式
        lines = result.split("\n", 1)
        if len(lines) >= 2:
            return lines[0].replace("TITLE:", "").strip(), lines[1].strip()

        return "", result


class AnthropicTranslator(BaseTranslator):
    """Anthropic (Claude) 翻译器"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        source_language: str = "中文",
        target_language: str = "English"
    ):
        super().__init__(source_language, target_language)
        self.api_key = api_key or settings.translator.anthropic_api_key
        self.model = model or settings.translator.anthropic_model

        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("请安装 anthropic 库: pip install anthropic")

    def translate(self, text: str) -> str:
        """使用 Claude 翻译文本"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                messages=[
                    {
                        "role": "user",
                        "content": self._get_translation_prompt(text)
                    }
                ]
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error(f"Anthropic 翻译失败: {e}")
            raise

    def translate_with_title(
        self,
        title: str,
        content: str
    ) -> Tuple[str, str]:
        """翻译标题和内容"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                messages=[
                    {
                        "role": "user",
                        "content": self._get_article_translation_prompt(title, content)
                    }
                ]
            )

            result = response.content[0].text.strip()
            return self._parse_translation_result(result)
        except Exception as e:
            logger.error(f"Anthropic 翻译失败: {e}")
            raise

    def _parse_translation_result(self, result: str) -> Tuple[str, str]:
        """解析翻译结果"""
        # 尝试解析 TITLE: xxx --- content 格式
        title_match = re.match(r"TITLE:\s*(.+?)\n---\n(.+)", result, re.DOTALL)
        if title_match:
            return title_match.group(1).strip(), title_match.group(2).strip()

        # 如果解析失败，尝试其他格式
        lines = result.split("\n", 1)
        if len(lines) >= 2:
            return lines[0].replace("TITLE:", "").strip(), lines[1].strip()

        return "", result


class Translator:
    """翻译器工厂类"""

    def __init__(
        self,
        provider: Optional[str] = None,
        source_language: Optional[str] = None,
        target_language: Optional[str] = None
    ):
        self.provider = provider or settings.translator.provider
        self.source_language = source_language or settings.translator.source_language
        self.target_language = target_language or settings.translator.target_language

        self._translator = self._create_translator()

    def _create_translator(self) -> BaseTranslator:
        """创建翻译器实例"""
        if self.provider == "openai":
            return OpenAITranslator(
                source_language=self.source_language,
                target_language=self.target_language
            )
        elif self.provider == "anthropic":
            return AnthropicTranslator(
                source_language=self.source_language,
                target_language=self.target_language
            )
        else:
            raise ValueError(f"不支持的翻译提供商: {self.provider}")

    def translate(self, text: str) -> str:
        """翻译文本"""
        logger.info(f"使用 {self.provider} 翻译文本 ({len(text)} 字符)")
        return self._translator.translate(text)

    def translate_article(
        self,
        title: str,
        content: str
    ) -> TranslationResult:
        """翻译完整文章"""
        logger.info(f"翻译文章: {title}")

        translated_title, translated_content = self._translator.translate_with_title(
            title, content
        )

        return TranslationResult(
            original_text=content,
            translated_text=translated_content,
            source_language=self.source_language,
            target_language=self.target_language,
            provider=self.provider,
            title_original=title,
            title_translated=translated_title
        )


# 测试代码
if __name__ == "__main__":
    # 测试翻译
    translator = Translator()

    test_title = "人工智能的未来"
    test_content = """
# 人工智能的未来

人工智能（AI）正在改变我们的世界。从智能手机到自动驾驶汽车，AI 已经渗透到我们生活的方方面面。

## 主要趋势

1. **大语言模型**: GPT、Claude 等模型正在变得越来越强大
2. **多模态AI**: 结合文本、图像、音频的综合能力
3. **AI代理**: 能够自主完成复杂任务的智能系统

## 结论

未来已来，让我们拥抱变化！
"""

    result = translator.translate_article(test_title, test_content)
    print(f"原标题: {result.title_original}")
    print(f"翻译标题: {result.title_translated}")
    print(f"翻译内容预览: {result.translated_text[:300]}...")

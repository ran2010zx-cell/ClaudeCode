"""
配置管理模块
使用 Pydantic 进行配置验证
"""

import os
from typing import Optional, Literal
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class NotionConfig(BaseModel):
    """Notion API 配置"""
    api_key: str = Field(default="", description="Notion Integration Token")
    database_id: str = Field(default="", description="Notion 数据库 ID")


class TranslatorConfig(BaseModel):
    """翻译配置"""
    provider: Literal["openai", "anthropic"] = Field(
        default="openai",
        description="翻译提供商: openai 或 anthropic"
    )
    openai_api_key: str = Field(default="", description="OpenAI API Key")
    openai_model: str = Field(default="gpt-4o", description="OpenAI 模型")
    anthropic_api_key: str = Field(default="", description="Anthropic API Key")
    anthropic_model: str = Field(default="claude-sonnet-4-20250514", description="Anthropic 模型")
    source_language: str = Field(default="中文", description="源语言")
    target_language: str = Field(default="English", description="目标语言")


class SubstackConfig(BaseModel):
    """Substack 配置"""
    email: str = Field(default="", description="Substack 登录邮箱")
    password: str = Field(default="", description="Substack 密码")
    publication_url: str = Field(default="", description="Substack 出版物 URL")
    # 注意: Substack 没有公开 API，需要使用浏览器自动化或邮件发布


class TwitterConfig(BaseModel):
    """Twitter/X API 配置"""
    api_key: str = Field(default="", description="Twitter API Key")
    api_secret: str = Field(default="", description="Twitter API Secret")
    access_token: str = Field(default="", description="Twitter Access Token")
    access_token_secret: str = Field(default="", description="Twitter Access Token Secret")
    bearer_token: str = Field(default="", description="Twitter Bearer Token")
    max_tweet_length: int = Field(default=280, description="推文最大长度")
    thread_delay_seconds: int = Field(default=2, description="推文线程发送间隔")


class Settings(BaseSettings):
    """主配置类"""

    # Notion 配置
    notion_api_key: str = Field(default="")
    notion_database_id: str = Field(default="")

    # 翻译配置
    translator_provider: str = Field(default="openai")
    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-4o")
    anthropic_api_key: str = Field(default="")
    anthropic_model: str = Field(default="claude-sonnet-4-20250514")
    source_language: str = Field(default="中文")
    target_language: str = Field(default="English")

    # Substack 配置
    substack_email: str = Field(default="")
    substack_password: str = Field(default="")
    substack_publication_url: str = Field(default="")

    # Twitter 配置
    twitter_api_key: str = Field(default="")
    twitter_api_secret: str = Field(default="")
    twitter_access_token: str = Field(default="")
    twitter_access_token_secret: str = Field(default="")
    twitter_bearer_token: str = Field(default="")
    twitter_max_tweet_length: int = Field(default=280)
    twitter_thread_delay_seconds: int = Field(default=2)

    # 日志配置
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="logs/translator.log")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def notion(self) -> NotionConfig:
        return NotionConfig(
            api_key=self.notion_api_key,
            database_id=self.notion_database_id
        )

    @property
    def translator(self) -> TranslatorConfig:
        return TranslatorConfig(
            provider=self.translator_provider,
            openai_api_key=self.openai_api_key,
            openai_model=self.openai_model,
            anthropic_api_key=self.anthropic_api_key,
            anthropic_model=self.anthropic_model,
            source_language=self.source_language,
            target_language=self.target_language
        )

    @property
    def substack(self) -> SubstackConfig:
        return SubstackConfig(
            email=self.substack_email,
            password=self.substack_password,
            publication_url=self.substack_publication_url
        )

    @property
    def twitter(self) -> TwitterConfig:
        return TwitterConfig(
            api_key=self.twitter_api_key,
            api_secret=self.twitter_api_secret,
            access_token=self.twitter_access_token,
            access_token_secret=self.twitter_access_token_secret,
            bearer_token=self.twitter_bearer_token,
            max_tweet_length=self.twitter_max_tweet_length,
            thread_delay_seconds=self.twitter_thread_delay_seconds
        )


# 全局配置实例
settings = Settings()

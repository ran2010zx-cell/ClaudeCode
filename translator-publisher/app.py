"""
Notion 文章自动翻译发布工具 - Web 界面版
使用 Streamlit 构建，支持 DeepSeek 翻译
"""

import streamlit as st
import requests
import re
import time
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Tuple

# 页面配置
st.set_page_config(
    page_title="文章翻译发布工具",
    page_icon="📝",
    layout="wide"
)

# ============== 配置管理 ==============

CONFIG_FILE = Path(__file__).parent / "config.json"

def load_config():
    """加载配置"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_config(config):
    """保存配置"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


# ============== DeepSeek 翻译 ==============

def translate_with_deepseek(
    text: str,
    title: str,
    api_key: str,
    source_lang: str = "中文",
    target_lang: str = "English"
) -> Tuple[str, str]:
    """
    使用 DeepSeek API 翻译文章
    返回: (翻译后的标题, 翻译后的内容)
    """
    url = "https://api.deepseek.com/chat/completions"

    prompt = f"""You are a professional translator. Please translate the following article from {source_lang} to {target_lang}.

Requirements:
1. Translate both the title and the content
2. Maintain the original meaning, tone, and style
3. Preserve all formatting (paragraphs, lists, etc.)
4. Make the translation natural and fluent
5. Do not add any explanations

Output format:
TITLE: [translated title]
---
[translated content]

Article to translate:

Title: {title}

Content:
{text}"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    response = requests.post(url, headers=headers, json=data, timeout=120)
    response.raise_for_status()

    result = response.json()
    content = result["choices"][0]["message"]["content"].strip()

    # 解析结果
    title_match = re.match(r"TITLE:\s*(.+?)\n---\n(.+)", content, re.DOTALL)
    if title_match:
        return title_match.group(1).strip(), title_match.group(2).strip()

    # 备用解析
    lines = content.split("\n", 1)
    if len(lines) >= 2:
        return lines[0].replace("TITLE:", "").strip(), lines[1].strip()

    return title, content


# ============== 推文线程生成 ==============

@dataclass
class Tweet:
    text: str
    index: int
    total: int

def split_to_tweets(
    title: str,
    content: str,
    substack_url: str = "",
    max_length: int = 270  # 留一点余量给计数器
) -> List[Tweet]:
    """将文章拆分为推文线程"""

    # 清理内容
    clean_content = content
    # 移除 markdown 格式
    clean_content = re.sub(r'\*\*([^\*]+)\*\*', r'\1', clean_content)
    clean_content = re.sub(r'\*([^\*]+)\*', r'\1', clean_content)
    clean_content = re.sub(r'^#+\s*', '', clean_content, flags=re.MULTILINE)
    clean_content = re.sub(r'!\[.*?\]\(.*?\)', '', clean_content)
    clean_content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean_content)

    tweets_text = []

    # 第一条：标题
    first_tweet = f"🧵 {title}\n\n"

    # 拆分段落
    paragraphs = [p.strip() for p in clean_content.split('\n\n') if p.strip()]

    current_tweet = first_tweet

    for para in paragraphs:
        # 拆分句子
        sentences = re.split(r'([.!?。！？])', para)

        i = 0
        while i < len(sentences):
            sentence = sentences[i]
            # 合并标点
            if i + 1 < len(sentences) and re.match(r'[.!?。！？]', sentences[i + 1]):
                sentence += sentences[i + 1]
                i += 2
            else:
                i += 1

            sentence = sentence.strip()
            if not sentence:
                continue

            potential = current_tweet + (" " if current_tweet and not current_tweet.endswith('\n') else "") + sentence

            if len(potential) <= max_length:
                current_tweet = potential
            else:
                if current_tweet.strip():
                    tweets_text.append(current_tweet.strip())

                if len(sentence) > max_length:
                    # 强制拆分长句
                    while sentence:
                        tweets_text.append(sentence[:max_length])
                        sentence = sentence[max_length:]
                    current_tweet = ""
                else:
                    current_tweet = sentence

    if current_tweet.strip():
        tweets_text.append(current_tweet.strip())

    # 添加最后一条：链接
    if substack_url:
        tweets_text.append(f"📖 Read the full article:\n{substack_url}")

    # 创建 Tweet 对象
    total = len(tweets_text)
    return [Tweet(text=t, index=i+1, total=total) for i, t in enumerate(tweets_text)]


# ============== Substack 发布指南 ==============

def get_substack_guide():
    """获取 Substack 手动发布指南"""
    return """
### 发布到 Substack 的步骤：

1. 打开你的 Substack 后台: `https://你的名字.substack.com/publish/post`

2. 复制下面的**英文标题**粘贴到标题栏

3. 复制下面的**英文内容**粘贴到正文

4. 点击 **Publish** 发布

5. 发布后，复制文章链接，回来粘贴到下面，用于生成推文线程
"""


# ============== Twitter 发布指南 ==============

def get_twitter_guide():
    """获取 Twitter 发布指南"""
    return """
### 发布推文线程的步骤：

**方法一：手动发布（推荐新手）**
1. 打开 Twitter/X
2. 复制第 1 条推文，发布
3. 在自己的推文下回复第 2 条
4. 以此类推...

**方法二：使用 API 自动发布**
1. 申请 Twitter 开发者账号: https://developer.twitter.com/
2. 创建项目，获取 API Key
3. 在左侧「设置」中填入 API 信息
4. 点击「自动发布到 Twitter」
"""


# ============== 主界面 ==============

def main():
    st.title("📝 文章翻译发布工具")
    st.markdown("将中文文章翻译成英文，发布到 Substack 和 Twitter")

    # 加载配置
    config = load_config()

    # 侧边栏 - 设置
    with st.sidebar:
        st.header("⚙️ 设置")

        # DeepSeek API
        st.subheader("DeepSeek API")
        deepseek_key = st.text_input(
            "API Key",
            value=config.get("deepseek_api_key", ""),
            type="password",
            help="从 https://platform.deepseek.com/ 获取"
        )

        st.divider()

        # Twitter API (可选)
        st.subheader("Twitter API (可选)")
        twitter_api_key = st.text_input(
            "API Key",
            value=config.get("twitter_api_key", ""),
            type="password"
        )
        twitter_api_secret = st.text_input(
            "API Secret",
            value=config.get("twitter_api_secret", ""),
            type="password"
        )
        twitter_access_token = st.text_input(
            "Access Token",
            value=config.get("twitter_access_token", ""),
            type="password"
        )
        twitter_access_secret = st.text_input(
            "Access Token Secret",
            value=config.get("twitter_access_token_secret", ""),
            type="password"
        )

        # 保存设置
        if st.button("💾 保存设置"):
            config["deepseek_api_key"] = deepseek_key
            config["twitter_api_key"] = twitter_api_key
            config["twitter_api_secret"] = twitter_api_secret
            config["twitter_access_token"] = twitter_access_token
            config["twitter_access_token_secret"] = twitter_access_secret
            save_config(config)
            st.success("设置已保存！")

    # 主区域 - 使用 tabs
    tab1, tab2, tab3 = st.tabs(["1️⃣ 翻译", "2️⃣ 发布 Substack", "3️⃣ 发布 Twitter"])

    # ========== Tab 1: 翻译 ==========
    with tab1:
        st.header("第一步：翻译文章")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📄 中文原文")
            title_cn = st.text_input("文章标题", placeholder="输入你的文章标题")
            content_cn = st.text_area(
                "文章内容",
                height=400,
                placeholder="在这里粘贴你的中文文章内容..."
            )

        with col2:
            st.subheader("📄 英文翻译")

            # 翻译按钮
            if st.button("🔄 翻译", type="primary", use_container_width=True):
                if not deepseek_key:
                    st.error("请先在左侧设置中填入 DeepSeek API Key")
                elif not title_cn or not content_cn:
                    st.error("请输入标题和内容")
                else:
                    with st.spinner("正在翻译，请稍候..."):
                        try:
                            title_en, content_en = translate_with_deepseek(
                                content_cn, title_cn, deepseek_key
                            )
                            st.session_state["title_en"] = title_en
                            st.session_state["content_en"] = content_en
                            st.success("翻译完成！")
                        except Exception as e:
                            st.error(f"翻译失败: {e}")

            # 显示翻译结果
            title_en = st.text_input(
                "英文标题",
                value=st.session_state.get("title_en", ""),
                key="title_en_input"
            )
            content_en = st.text_area(
                "英文内容",
                value=st.session_state.get("content_en", ""),
                height=350,
                key="content_en_input"
            )

            # 更新 session state
            if title_en:
                st.session_state["title_en"] = title_en
            if content_en:
                st.session_state["content_en"] = content_en

    # ========== Tab 2: 发布 Substack ==========
    with tab2:
        st.header("第二步：发布到 Substack")

        st.markdown(get_substack_guide())

        st.divider()

        if st.session_state.get("title_en") and st.session_state.get("content_en"):
            st.subheader("📋 复制以下内容到 Substack")

            # 标题
            st.markdown("**英文标题：**")
            st.code(st.session_state.get("title_en", ""), language=None)

            # 内容
            st.markdown("**英文内容：**")
            st.text_area(
                "内容预览",
                value=st.session_state.get("content_en", ""),
                height=300,
                label_visibility="collapsed"
            )

            st.divider()

            # 输入 Substack 链接
            st.subheader("📎 发布后，粘贴文章链接")
            substack_url = st.text_input(
                "Substack 文章链接",
                placeholder="https://你的名字.substack.com/p/文章标题",
                key="substack_url"
            )

            if substack_url:
                st.session_state["substack_url"] = substack_url
                st.success("链接已保存！去第三步发布 Twitter 线程吧")
        else:
            st.info("👈 请先在「翻译」标签页完成翻译")

    # ========== Tab 3: 发布 Twitter ==========
    with tab3:
        st.header("第三步：发布 Twitter 线程")

        title_en = st.session_state.get("title_en", "")
        content_en = st.session_state.get("content_en", "")
        substack_url = st.session_state.get("substack_url", "")

        if not title_en or not content_en:
            st.info("👈 请先在「翻译」标签页完成翻译")
        else:
            # 生成推文线程
            if st.button("🐦 生成推文线程", type="primary"):
                tweets = split_to_tweets(title_en, content_en, substack_url)
                st.session_state["tweets"] = tweets

            # 显示推文线程
            if "tweets" in st.session_state:
                tweets = st.session_state["tweets"]

                st.success(f"共生成 {len(tweets)} 条推文")

                st.markdown(get_twitter_guide())

                st.divider()

                st.subheader("📋 推文线程预览")

                for tweet in tweets:
                    with st.container():
                        st.markdown(f"**Tweet {tweet.index}/{tweet.total}**")
                        st.text_area(
                            f"tweet_{tweet.index}",
                            value=tweet.text,
                            height=100,
                            label_visibility="collapsed",
                            key=f"tweet_display_{tweet.index}"
                        )
                        st.caption(f"字符数: {len(tweet.text)}/280")
                        st.divider()

                # 自动发布（如果有 API）
                if all([twitter_api_key, twitter_api_secret,
                       twitter_access_token, twitter_access_secret]):
                    st.divider()
                    if st.button("🚀 自动发布到 Twitter", type="primary"):
                        with st.spinner("正在发布..."):
                            try:
                                import tweepy

                                client = tweepy.Client(
                                    consumer_key=twitter_api_key,
                                    consumer_secret=twitter_api_secret,
                                    access_token=twitter_access_token,
                                    access_token_secret=twitter_access_secret
                                )

                                reply_to_id = None
                                tweet_ids = []

                                progress = st.progress(0)
                                for i, tweet in enumerate(tweets):
                                    if reply_to_id:
                                        response = client.create_tweet(
                                            text=tweet.text,
                                            in_reply_to_tweet_id=reply_to_id
                                        )
                                    else:
                                        response = client.create_tweet(text=tweet.text)

                                    tweet_id = response.data['id']
                                    tweet_ids.append(tweet_id)
                                    reply_to_id = tweet_id

                                    progress.progress((i + 1) / len(tweets))
                                    time.sleep(2)  # 避免限流

                                thread_url = f"https://twitter.com/i/status/{tweet_ids[0]}"
                                st.success(f"发布成功！\n\n线程链接: {thread_url}")
                                st.balloons()

                            except ImportError:
                                st.error("请安装 tweepy: pip install tweepy")
                            except Exception as e:
                                st.error(f"发布失败: {e}")
                else:
                    st.info("💡 填写左侧的 Twitter API 设置后，可以自动发布")


if __name__ == "__main__":
    main()

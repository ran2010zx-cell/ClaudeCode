# Notion → Substack + Twitter 自动翻译发布工具

一个自动化工具，用于将 Notion 中的中文文章翻译成英文，并同时发布到 Substack 和 Twitter。

## 功能特性

- **Notion 集成**: 自动从 Notion 数据库获取待发布文章
- **AI 翻译**: 支持 OpenAI (GPT-4) 和 Anthropic (Claude) 进行高质量翻译
- **Substack 发布**: 多种发布方式 (API/邮件/浏览器自动化)
- **Twitter 线程**: 智能拆分文章为推文线程，最后一条链接到 Substack
- **状态同步**: 自动更新 Notion 中的发布状态和链接

## 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                     Notion 数据库                           │
│  [文章1: Ready] [文章2: Ready] [文章3: Draft]               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   1. 获取待发布文章                          │
│         (status = "Ready to Publish")                       │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   2. AI 翻译 (中文 → 英文)                   │
│              OpenAI GPT-4 / Anthropic Claude                │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   3. 发布到 Substack                         │
│                 API / Email / Selenium                       │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   4. 发布推文线程                            │
│          🧵 Tweet 1/5 → Tweet 2/5 → ... → 📖 Link           │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   5. 更新 Notion 状态                        │
│        status → "Published" + 添加发布链接                   │
└─────────────────────────────────────────────────────────────┘
```

## 安装

### 1. 克隆项目

```bash
cd translator-publisher
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥
```

## 配置说明

### Notion 设置

1. 创建 Notion Integration: https://www.notion.so/my-integrations
2. 获取 API Key
3. 在你的数据库页面分享给 Integration
4. 复制数据库 ID (从 URL 获取)

**数据库推荐结构**:
| 属性名 | 类型 | 说明 |
|--------|------|------|
| Name | Title | 文章标题 |
| Status | Status | 发布状态 (Draft / Ready to Publish / Published) |
| Published URLs | Rich Text | 发布后的链接 |

### 翻译 API

选择其中一个:

- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic**: https://console.anthropic.com/

### Substack 设置

Substack 没有官方 API，本工具支持三种发布方式:

1. **API 方式** (推荐): 使用逆向工程的接口，需要邮箱密码
2. **邮件方式**: 需要在 Substack 启用 Email-to-Post
3. **Selenium**: 浏览器自动化，最可靠但较慢

### Twitter API

1. 申请开发者账号: https://developer.twitter.com/
2. 创建项目和应用
3. 获取 API Key, Secret, Access Token

## 使用方法

### 命令行

```bash
cd src

# 列出待发布文章
python main.py --mode list

# 预览 (不实际发布)
python main.py --mode preview

# 发布所有待发布文章
python main.py --mode all

# 发布单篇文章
python main.py --mode single --page-id <notion-page-id>

# 试运行模式
python main.py --mode all --dry-run

# 指定 Substack 发布方式
python main.py --mode all --substack-method selenium
```

### Python 代码

```python
from main import AutoPublisher

publisher = AutoPublisher()

# 发布所有待发布文章
results = publisher.publish_all_ready()

# 发布单篇
result = publisher.publish_single("notion-page-id")

# 预览模式
result = publisher.publish_single("notion-page-id", dry_run=True)
```

## 推文线程示例

输入文章: "人工智能的未来" (1500 字)

输出推文线程:

```
🧵 The Future of AI [1/6]

Artificial Intelligence is transforming our world in unprecedented ways...

---

Key trends to watch: [2/6]

• Multimodal AI combining text, images, and audio
• AI agents that can complete complex tasks autonomously
• Edge AI bringing intelligence to devices

---

The implications are profound... [3/6]

---

As we navigate this transformation... [4/6]

---

The future is not predetermined. It's up to us to shape it wisely. [5/6]

---

📖 Read the full article: [6/6]
https://your-publication.substack.com/p/the-future-of-ai
```

## 项目结构

```
translator-publisher/
├── src/
│   ├── __init__.py
│   ├── config.py           # 配置管理
│   ├── notion_client.py    # Notion API 客户端
│   ├── translator.py       # AI 翻译模块
│   ├── substack.py         # Substack 发布
│   ├── twitter_publisher.py # Twitter 线程发布
│   └── main.py             # 主程序
├── requirements.txt
├── .env.example
└── README.md
```

## 注意事项

1. **API 限制**: 注意各平台的 API 调用限制
2. **Substack**: 没有官方 API，接口可能变化
3. **Twitter**: 免费版 API 有发推数量限制
4. **翻译费用**: OpenAI/Anthropic API 按 token 收费

## License

MIT

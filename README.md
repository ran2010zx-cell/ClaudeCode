# 小米新闻追踪系统 (Xiaomi News Tracker)

自动化社交媒体舆情监控系统，用于追踪小红书、微博和Twitter/X上关于小米的新闻和讨论。

## 功能特点

- 多平台监控: 支持小红书、微博、Twitter/X三大平台
- 自动采集: 定时自动爬取关键词相关内容
- 智能去重: 自动识别和过滤重复内容
- 实时通知: 邮件汇报新发现的舆情
- 数据存储: SQLite/PostgreSQL/MySQL数据库支持
- 灵活配置: 通过环境变量轻松配置

## 系统架构

```
xiaomi-news-tracker/
├── src/
│   ├── __init__.py
│   ├── config.py          # 配置管理
│   ├── models.py          # 数据模型
│   ├── database.py        # 数据库操作
│   ├── crawlers/          # 爬虫模块
│   │   ├── __init__.py
│   │   ├── base.py        # 基础爬虫类
│   │   ├── xiaohongshu.py # 小红书爬虫
│   │   ├── weibo.py       # 微博爬虫
│   │   └── twitter.py     # X/Twitter爬虫
│   ├── scheduler.py       # 定时任务
│   ├── reporter.py        # 汇报模块
│   └── main.py            # 主程序
├── data/                  # 数据存储目录
├── logs/                  # 日志目录
├── .env.example           # 环境变量示例
├── requirements.txt       # Python依赖
└── README.md              # 说明文档
```

## 快速开始

### 1. 环境要求

- Python 3.8+
- pip

### 2. 安装依赖

```bash
# 克隆仓库
git clone <repository-url>
cd xiaomi-news-tracker

# 创建虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置

复制环境变量示例文件并编辑:

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置必要的参数:

```env
# 基本配置
SEARCH_KEYWORDS=xiaomi,小米,Xiaomi,雷军
CRAWL_INTERVAL_MINUTES=60

# Twitter API (必需 - 如果要使用Twitter)
TWITTER_BEARER_TOKEN=your_bearer_token_here

# 邮件通知 (可选)
EMAIL_ENABLED=true
EMAIL_FROM=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_TO=recipient@example.com
```

### 4. 运行

```bash
# 方式1: 作为Python模块运行
python -m src.main

# 方式2: 直接运行主文件
python src/main.py

# 只运行一次 (测试用)
python -m src.main --mode once

# 查看统计信息
python -m src.main --mode stats

# 测试报告生成
python -m src.main --mode test

# 调试模式
python -m src.main --debug
```

## API凭证获取

### Twitter/X API

1. 访问 [Twitter Developer Portal](https://developer.twitter.com/)
2. 创建应用
3. 获取 Bearer Token (推荐) 或 API Key/Secret
4. 将凭证添加到 `.env` 文件

**注意**: Twitter免费版有限制，建议升级到付费版以获得更高的访问限制。

### 微博 API (可选)

1. 访问 [微博开放平台](https://open.weibo.com/)
2. 创建应用
3. 获取 App Key 和 App Secret
4. 如果没有API凭证，系统会自动使用网页爬取

### 小红书

小红书没有公开API。当前实现提供了模板结构，您需要:

1. 使用Selenium进行网页自动化
2. 使用第三方API服务 (如果有)
3. 参考 `src/crawlers/xiaohongshu.py` 中的说明实现

## 配置选项

### 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接URL | `sqlite:///data/xiaomi_news.db` |
| `SEARCH_KEYWORDS` | 搜索关键词 (逗号分隔) | `xiaomi,小米,Xiaomi,XIAOMI` |
| `CRAWL_INTERVAL_MINUTES` | 爬取间隔 (分钟) | `60` |
| `MAX_ITEMS_PER_PLATFORM` | 每次最多爬取条目数 | `50` |
| `EMAIL_ENABLED` | 是否启用邮件通知 | `false` |
| `REPORT_FORMAT` | 报告格式 (text/html/json) | `html` |
| `REPORT_MIN_ITEMS` | 发送报告的最小新条目数 | `1` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

完整配置选项请参考 `.env.example`

## 使用Gmail发送邮件

如果使用Gmail发送通知邮件:

1. 启用两步验证
2. 生成应用专用密码: [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. 在 `.env` 中使用应用专用密码

```env
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_FROM=your_email@gmail.com
EMAIL_PASSWORD=your_app_password  # 16位应用专用密码
EMAIL_TO=recipient@example.com
```

## 运行模式

### 1. 持续运行模式 (默认)

```bash
python -m src.main
```

按照配置的时间间隔持续监控，适合长期运行。

### 2. 单次运行模式

```bash
python -m src.main --mode once
```

只运行一次爬取，适合测试或配合cron定时任务使用。

### 3. 查看统计

```bash
python -m src.main --mode stats
```

显示数据库中的统计信息。

### 4. 测试报告

```bash
python -m src.main --mode test
```

生成并打印报告 (不发送邮件)。

## 使用Cron定时任务

如果不想让程序持续运行，可以使用系统的cron:

```bash
# 编辑crontab
crontab -e

# 添加任务 (每小时运行一次)
0 * * * * cd /path/to/xiaomi-news-tracker && /path/to/venv/bin/python -m src.main --mode once >> /path/to/logs/cron.log 2>&1
```

## 数据库

### 默认使用SQLite

开箱即用，数据存储在 `data/xiaomi_news.db`

### 使用PostgreSQL

```env
DATABASE_URL=postgresql://user:password@localhost/xiaomi_news
```

### 使用MySQL

```env
DATABASE_URL=mysql://user:password@localhost/xiaomi_news
```

## 报告格式

### HTML报告 (默认)

精美的HTML格式邮件，包含:
- 分平台汇总
- 详细内容展示
- 互动数据 (点赞、评论、转发)
- 原文链接

### 文本报告

纯文本格式，适合简单通知。

### JSON报告

机器可读的JSON格式，适合进一步处理。

## 开发和调试

### 启用调试日志

```bash
python -m src.main --debug
```

### 查看日志文件

```bash
tail -f logs/xiaomi_tracker.log
```

### 直接查询数据库

```bash
sqlite3 data/xiaomi_news.db
```

```sql
-- 查看所有表
.tables

-- 查看最新的新闻条目
SELECT * FROM news_items ORDER BY created_at DESC LIMIT 10;

-- 查看爬取日志
SELECT * FROM crawl_logs ORDER BY started_at DESC LIMIT 10;
```

## 注意事项

### 1. API限制

- **Twitter**: 免费版有严格的速率限制，建议使用付费版
- **微博**: API需要审核，没有API时会使用网页爬取
- **小红书**: 无公开API，需要自己实现爬取逻辑

### 2. 反爬虫

网页爬取可能遇到反爬虫机制:
- 使用合理的请求延迟 (`REQUEST_DELAY`)
- 使用真实的User-Agent
- 考虑使用代理IP (如果需要)
- 遵守网站的robots.txt

### 3. 法律合规

- 仅用于个人学习和研究
- 遵守各平台的服务条款
- 不要过度爬取造成服务器负担
- 尊重内容版权

### 4. 小红书爬虫实现

当前小红书爬虫是模板实现，您需要:

1. 安装Selenium: `pip install selenium`
2. 下载ChromeDriver
3. 实现 `src/crawlers/xiaohongshu.py` 中的爬取逻辑
4. 或使用第三方API服务

参考文件中的注释说明。

## 故障排除

### 问题: Twitter爬虫报错

**解决**: 检查API凭证是否正确，确认是否超过速率限制。

### 问题: 邮件发送失败

**解决**:
1. 检查SMTP配置
2. 如使用Gmail，确保使用应用专用密码
3. 检查防火墙设置

### 问题: 数据库锁定错误

**解决**:
- SQLite不适合高并发，考虑使用PostgreSQL
- 确保没有多个实例同时运行

### 问题: 爬虫没有返回数据

**解决**:
1. 启用调试模式查看详细日志
2. 检查网络连接
3. 验证API凭证
4. 检查关键词是否正确

## 贡献

欢迎提交Issue和Pull Request!

## 许可证

MIT License

## 免责声明

本项目仅供学习和研究使用。使用者需要:
- 遵守相关平台的服务条款
- 遵守当地法律法规
- 合理使用，不对平台造成负担
- 尊重数据隐私和版权

作者不对使用本项目造成的任何后果负责。

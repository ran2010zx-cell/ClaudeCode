# 📝 文章翻译发布工具

将中文文章翻译成英文，发布到 Substack 和 Twitter。

## 功能

- ✅ 使用 DeepSeek AI 翻译文章
- ✅ 发布到 Substack (手动复制)
- ✅ 自动生成 Twitter 推文线程
- ✅ 支持自动发布到 Twitter (需要 API)

## 界面预览

```
┌─────────────────────────────────────────────────────────┐
│  📝 文章翻译发布工具                                     │
├─────────────────────────────────────────────────────────┤
│  [1️⃣ 翻译]    [2️⃣ 发布 Substack]    [3️⃣ 发布 Twitter]  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   📄 中文原文              📄 英文翻译                   │
│  ┌──────────────┐        ┌──────────────┐              │
│  │ 标题         │        │ Title        │              │
│  │              │   →    │              │              │
│  │ 内容...      │  翻译  │ Content...   │              │
│  └──────────────┘        └──────────────┘              │
│                                                         │
│              [ 🔄 翻译 ]                                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 使用方法

### Windows 用户

1. **安装 Python** (如果没有的话)
   - 下载: https://www.python.org/downloads/
   - 安装时勾选 "Add Python to PATH"

2. **双击运行** `启动工具.bat`
   - 首次运行会自动安装依赖
   - 浏览器会自动打开

3. **配置 API**
   - 在左侧填入你的 DeepSeek API Key
   - 点击「保存设置」

4. **开始使用**
   - 粘贴中文文章 → 点击翻译
   - 复制英文到 Substack 发布
   - 生成推文线程发布到 Twitter

### Mac/Linux 用户

```bash
cd translator-publisher

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动
streamlit run app.py
```

## 获取 API Key

### DeepSeek API (必需)

1. 访问 https://platform.deepseek.com/
2. 注册账号
3. 创建 API Key
4. 复制到工具设置中

### Twitter API (可选，用于自动发布)

1. 访问 https://developer.twitter.com/
2. 申请开发者账号
3. 创建项目和应用
4. 获取以下 4 个密钥:
   - API Key
   - API Secret
   - Access Token
   - Access Token Secret

## 工作流程

```
第一步: 翻译
┌─────────────┐      ┌─────────────┐
│ 中文文章    │ ──→  │ 英文文章    │
│ (粘贴)     │ 翻译  │ (DeepSeek)  │
└─────────────┘      └─────────────┘

第二步: 发布 Substack
┌─────────────┐      ┌─────────────┐
│ 英文文章    │ ──→  │ Substack    │
│ (复制)     │ 粘贴  │ (发布)      │
└─────────────┘      └─────────────┘

第三步: 发布 Twitter
┌─────────────┐      ┌─────────────┐
│ 英文文章    │ ──→  │ 推文线程    │
│ + 链接     │ 生成  │ 1/5, 2/5... │
└─────────────┘      └─────────────┘
```

## 常见问题

**Q: 翻译失败怎么办？**
- 检查 DeepSeek API Key 是否正确
- 检查网络连接

**Q: Twitter 自动发布失败？**
- 确认 4 个 API 密钥都填写正确
- 确认你的 Twitter 开发者账号有发推权限

**Q: 如何停止程序？**
- 在命令行窗口按 Ctrl+C
- 或直接关闭窗口

## 文件说明

```
translator-publisher/
├── app.py           # 主程序
├── requirements.txt # 依赖
├── 启动工具.bat     # Windows 启动脚本
├── config.json      # 配置文件 (自动生成)
└── README.md        # 说明文档
```

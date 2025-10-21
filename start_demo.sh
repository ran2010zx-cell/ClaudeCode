#!/bin/bash

# 小米新闻追踪系统 - 快速演示启动脚本

echo "========================================"
echo "  小米新闻追踪系统 - 演示模式"
echo "========================================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python 3.8或更高版本"
    echo "访问: https://www.python.org/downloads/"
    exit 1
fi

echo "✓ Python已安装: $(python3 --version)"
echo ""

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
    echo "✓ 虚拟环境已创建"
    echo ""
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "检查并安装依赖..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✓ 依赖已安装"
echo ""

# 创建必要的目录
mkdir -p data logs

# 创建默认.env文件（如果不存在）
if [ ! -f ".env" ]; then
    echo "创建默认配置文件..."
    cat > .env << 'EOF'
# 演示模式配置 - 无需修改即可运行
DATABASE_URL=sqlite:///data/xiaomi_news.db
SEARCH_KEYWORDS=xiaomi,小米,Xiaomi
CRAWL_INTERVAL_MINUTES=60
EMAIL_ENABLED=false
REPORT_FORMAT=html
LOG_LEVEL=INFO
EOF
    echo "✓ 配置文件已创建 (.env)"
    echo ""
fi

echo "========================================"
echo "  启动演示模式..."
echo "========================================"
echo ""

# 运行演示
python -m src.main --mode demo

echo ""
echo "========================================"
echo "  演示完成!"
echo "========================================"
echo ""
echo "接下来你可以:"
echo "  1. 查看数据库: data/xiaomi_news.db"
echo "  2. 查看日志: logs/xiaomi_tracker.log"
echo "  3. 再次运行演示: ./start_demo.sh"
echo "  4. 查看统计: python -m src.main --mode stats"
echo ""
echo "配置真实API后可以:"
echo "  - 编辑 .env 文件添加Twitter等API密钥"
echo "  - 运行真实抓取: python -m src.main --mode once"
echo ""

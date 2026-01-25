#!/bin/bash
# Notion → Substack + Twitter 自动发布工具启动脚本

set -e

echo "================================================"
echo "  Notion → Substack + Twitter 自动发布工具"
echo "================================================"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查 Python 版本
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "错误: 未找到 Python，请先安装 Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "检测到 Python 版本: $PYTHON_VERSION"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo ""
    echo "创建虚拟环境..."
    $PYTHON_CMD -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
if [ ! -f "venv/.deps_installed" ]; then
    echo ""
    echo "安装依赖..."
    pip install -r requirements.txt
    touch venv/.deps_installed
fi

# 检查配置文件
if [ ! -f ".env" ]; then
    echo ""
    echo "注意: 未找到 .env 配置文件"
    echo "请复制 .env.example 为 .env 并填入你的 API 密钥"
    echo ""
    echo "  cp .env.example .env"
    echo "  nano .env  # 或使用你喜欢的编辑器"
    echo ""
    exit 1
fi

# 创建日志目录
mkdir -p logs

# 运行主程序
echo ""
echo "启动程序..."
echo "------------------------------------------------"
cd src
$PYTHON_CMD main.py "$@"

@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo   小米新闻追踪系统 - 演示模式
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8或更高版本
    echo 访问: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYVER=%%i
echo ✓ Python已安装: !PYVER!
echo.

REM 检查虚拟环境是否存在
if not exist "venv\" (
    echo 创建虚拟环境...
    python -m venv venv
    echo ✓ 虚拟环境已创建
    echo.
)

REM 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo 检查并安装依赖...
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt
echo ✓ 依赖已安装
echo.

REM 创建必要的目录
if not exist "data\" mkdir data
if not exist "logs\" mkdir logs

REM 创建默认.env文件（如果不存在）
if not exist ".env" (
    echo 创建默认配置文件...
    (
        echo # 演示模式配置 - 无需修改即可运行
        echo DATABASE_URL=sqlite:///data/xiaomi_news.db
        echo SEARCH_KEYWORDS=xiaomi,小米,Xiaomi
        echo CRAWL_INTERVAL_MINUTES=60
        echo EMAIL_ENABLED=false
        echo REPORT_FORMAT=html
        echo LOG_LEVEL=INFO
    ) > .env
    echo ✓ 配置文件已创建 ^(.env^)
    echo.
)

echo ========================================
echo   启动演示模式...
echo ========================================
echo.

REM 运行演示
python -m src.main --mode demo

echo.
echo ========================================
echo   演示完成!
echo ========================================
echo.
echo 接下来你可以:
echo   1. 查看数据库: data\xiaomi_news.db
echo   2. 查看日志: logs\xiaomi_tracker.log
echo   3. 再次运行演示: start_demo.bat
echo   4. 查看统计: python -m src.main --mode stats
echo.
echo 配置真实API后可以:
echo   - 编辑 .env 文件添加Twitter等API密钥
echo   - 运行真实抓取: python -m src.main --mode once
echo.

pause

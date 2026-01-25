@echo off
chcp 65001 >nul
title 文章翻译发布工具

echo ================================================
echo   文章翻译发布工具
echo   中文 → 英文 → Substack + Twitter
echo ================================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: 获取脚本所在目录
cd /d "%~dp0"

:: 检查虚拟环境
if not exist "venv" (
    echo 首次运行，正在创建虚拟环境...
    python -m venv venv
    echo.
)

:: 激活虚拟环境
call venv\Scripts\activate.bat

:: 检查依赖
if not exist "venv\.deps_installed" (
    echo 正在安装依赖，请稍候...
    pip install -r requirements.txt -q
    echo. > venv\.deps_installed
    echo 依赖安装完成！
    echo.
)

:: 启动应用
echo 正在启动，浏览器将自动打开...
echo 如果没有自动打开，请手动访问: http://localhost:8501
echo.
echo 按 Ctrl+C 可以停止程序
echo ------------------------------------------------
streamlit run app.py --server.headless true

pause

@echo off
REM Health Tracker 快速启动脚本 (Windows)

chcp 65001 >nul

REM 检查虚拟环境
if not exist venv (
    echo ❌ 虚拟环境不存在，请先运行 install.bat
    pause
    exit /b 1
)

REM 激活虚拟环境
call venv\Scripts\activate

REM 运行 CLI
python cli.py %*

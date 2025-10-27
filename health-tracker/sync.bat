@echo off
REM 一键同步健康数据

cd /d %~dp0

REM 激活虚拟环境
call venv\Scripts\activate

REM 解析今天的笔记
echo 📝 正在解析今天的健康日志...
python cli.py parse --date today

REM 同步到云端
echo ☁️  正在同步到云端...
python sync_cli.py push

echo ✅ 同步完成！
pause

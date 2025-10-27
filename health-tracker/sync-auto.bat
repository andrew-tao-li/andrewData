@echo off
REM 静默定时同步脚本（后台运行，记录日志）

cd /d %~dp0

REM 创建日志目录
if not exist "logs" mkdir logs

REM 日志文件
set LOG_FILE=logs\sync-%date:~0,4%%date:~5,2%%date:~8,2%.log

REM 记录开始时间
echo ======================================== >> %LOG_FILE%
echo 开始时间: %date% %time% >> %LOG_FILE%

REM 激活虚拟环境
call venv\Scripts\activate

REM 解析今天的笔记
echo 📝 解析今天的健康日志... >> %LOG_FILE%
python cli.py parse --date today >> %LOG_FILE% 2>&1

REM 同步到云端
echo ☁️  同步到云端... >> %LOG_FILE%
python sync_cli.py push >> %LOG_FILE% 2>&1

REM 记录结束时间
echo 完成时间: %date% %time% >> %LOG_FILE%
echo ✅ 同步完成 >> %LOG_FILE%

REM 清理30天前的日志
forfiles /p "logs" /m sync-*.log /d -30 /c "cmd /c del @path" 2>nul

exit

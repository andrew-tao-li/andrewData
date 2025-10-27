#!/bin/bash
# 静默定时同步脚本（不弹窗，记录日志）

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 日志文件
LOG_FILE="$SCRIPT_DIR/logs/sync-$(date +%Y%m%d).log"
mkdir -p "$SCRIPT_DIR/logs"

# 记录开始时间
echo "========================================" >> "$LOG_FILE"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"

# 激活虚拟环境
source venv/bin/activate

# 解析今天的笔记
echo "📝 解析今天的健康日志..." >> "$LOG_FILE"
python cli.py parse --date today >> "$LOG_FILE" 2>&1

# 同步到云端
echo "☁️  同步到云端..." >> "$LOG_FILE"
python sync_cli.py push >> "$LOG_FILE" 2>&1

# 记录结束时间
echo "完成时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "✅ 同步完成" >> "$LOG_FILE"

# 清理30天前的日志
find "$SCRIPT_DIR/logs" -name "sync-*.log" -mtime +30 -delete

exit 0

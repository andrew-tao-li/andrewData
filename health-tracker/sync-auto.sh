#!/bin/bash
# 自动化健康数据同步脚本
# 功能：从佳明同步 → AI分析 → 写入Obsidian → 同步到云端

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 日志文件
LOG_FILE="$SCRIPT_DIR/logs/sync-$(date +%Y%m%d).log"
mkdir -p "$SCRIPT_DIR/logs"

# 记录开始时间
echo "========================================" >> "$LOG_FILE"
echo "🚀 开始时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"

# 激活虚拟环境
source venv/bin/activate

# 1. 从 Garmin 同步最新数据
echo "" >> "$LOG_FILE"
echo "📥 步骤 1: 从 Garmin 同步健康数据..." >> "$LOG_FILE"
python3 cli.py garmin-sync --date today >> "$LOG_FILE" 2>&1

# 2. 解析今天的 Obsidian 笔记（如果有手动记录）
echo "" >> "$LOG_FILE"
echo "📝 步骤 2: 解析 Obsidian 笔记..." >> "$LOG_FILE"
python3 cli.py parse --date today >> "$LOG_FILE" 2>&1

# 3. 同步到 Google Sheets
echo "" >> "$LOG_FILE"
echo "☁️  步骤 3: 同步到 Google Sheets..." >> "$LOG_FILE"
python3 cli.py sync --days 1 >> "$LOG_FILE" 2>&1

# 注意：周报和月报由 scheduler.py 自动生成
# - 周报：每周日 08:00 自动生成
# - 月报：每月最后一天 20:00 自动生成

# 记录结束时间
echo "" >> "$LOG_FILE"
echo "✅ 完成时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# 清理30天前的日志
find "$SCRIPT_DIR/logs" -name "sync-*.log" -mtime +30 -delete

exit 0

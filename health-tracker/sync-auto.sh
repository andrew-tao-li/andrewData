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

# 3. 生成健康分析报告（7天 & 30天）
echo "" >> "$LOG_FILE"
echo "📊 步骤 3: 生成健康分析报告..." >> "$LOG_FILE"
python3 cli.py report --days 7 >> "$LOG_FILE" 2>&1
python3 cli.py report --days 30 >> "$LOG_FILE" 2>&1

# 4. 获取个性化健康建议
echo "" >> "$LOG_FILE"
echo "💡 步骤 4: 生成个性化健康建议..." >> "$LOG_FILE"
python3 cli.py recommend >> "$LOG_FILE" 2>&1

# 5. 同步到 Google Sheets
echo "" >> "$LOG_FILE"
echo "☁️  步骤 5: 同步到 Google Sheets..." >> "$LOG_FILE"
python3 cli.py sync --days 1 >> "$LOG_FILE" 2>&1

# 记录结束时间
echo "" >> "$LOG_FILE"
echo "✅ 完成时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# 清理30天前的日志
find "$SCRIPT_DIR/logs" -name "sync-*.log" -mtime +30 -delete

exit 0

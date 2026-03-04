#!/bin/bash
# 验证今天12:00的每日同步是否成功执行
# 用法：在每天12:05运行此脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

TODAY=$(date +%Y-%m-%d)
YESTERDAY=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d "yesterday" +%Y-%m-%d)
LOG_FILE="logs/scheduler-error.log"
DB_FILE="health_data.db"

echo "=========================================="
echo "📊 每日同步验证报告"
echo "=========================================="
echo "验证时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "今天日期: $TODAY"
echo "同步目标日期: $YESTERDAY (昨天)"
echo ""

# 1. 检查调度器进程
echo "1️⃣ 检查调度器进程状态..."
if ps aux | grep -E "(cli.*start-scheduler|python.*scheduler)" | grep -v grep > /dev/null; then
    PID=$(ps aux | grep -E "(cli.*start-scheduler|python.*scheduler)" | grep -v grep | awk '{print $2}')
    UPTIME=$(ps -p $PID -o etime= | tr -d ' ')
    echo "   ✅ 调度器正在运行 (PID: $PID, 运行时长: $UPTIME)"
else
    echo "   ❌ 调度器进程未运行！"
    exit 1
fi
echo ""

# 2. 检查日志中是否有今天12:00的执行记录
echo "2️⃣ 检查日志中的执行记录..."
if [ -f "$LOG_FILE" ]; then
    echo "   日志文件: $LOG_FILE"

    # 查找函数调用记录
    if grep -q "🔔 SYNC_GARMIN_DATA 函数被调用" "$LOG_FILE" | tail -1 | grep -q "$TODAY 12:"; then
        echo "   ✅ 发现函数调用记录 (今天12点)"
        grep "🔔 SYNC_GARMIN_DATA 函数被调用" "$LOG_FILE" | tail -1
    else
        echo "   ⚠️  未发现今天12:00的函数调用记录"
        echo "   最近一次调用："
        grep "🔔 SYNC_GARMIN_DATA 函数被调用" "$LOG_FILE" | tail -1 || echo "   (无记录)"
    fi

    # 查找成功记录
    if grep -q "✅.*数据同步成功" "$LOG_FILE" | tail -1 | grep -q "$YESTERDAY"; then
        echo "   ✅ 发现同步成功记录 (昨天的数据)"
        grep "✅.*数据同步成功" "$LOG_FILE" | tail -1
    else
        echo "   ⚠️  未发现昨天数据的同步成功记录"
        echo "   最近一次成功："
        grep "✅.*数据同步成功" "$LOG_FILE" | tail -1 || echo "   (无记录)"
    fi
else
    echo "   ❌ 日志文件不存在: $LOG_FILE"
fi
echo ""

# 3. 检查数据库最后更新时间
echo "3️⃣ 检查数据库更新状态..."
if [ -f "$DB_FILE" ]; then
    DB_MTIME=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$DB_FILE" 2>/dev/null || stat -c "%y" "$DB_FILE" | cut -d. -f1)
    echo "   数据库文件: $DB_FILE"
    echo "   最后修改时间: $DB_MTIME"

    # 检查是否今天修改过
    if [[ "$DB_MTIME" == "$TODAY"* ]]; then
        echo "   ✅ 数据库今天有更新"
    else
        echo "   ⚠️  数据库今天未更新（可能同步失败）"
    fi

    # 查询最新记录
    if command -v sqlite3 &> /dev/null; then
        echo ""
        echo "   📊 最近5条记录："
        sqlite3 "$DB_FILE" "SELECT date, sleep_duration, hrv, resting_heart_rate FROM health_records ORDER BY date DESC LIMIT 5;" 2>/dev/null | while read line; do
            DATE_PART=$(echo "$line" | cut -d'|' -f1)
            if [ "$DATE_PART" = "$YESTERDAY" ]; then
                echo "   ✅ $line"
            else
                echo "      $line"
            fi
        done
    fi
else
    echo "   ❌ 数据库文件不存在: $DB_FILE"
fi
echo ""

# 4. 检查Obsidian日记是否更新
echo "4️⃣ 检查Obsidian日记更新..."
if [ -f "config/config.json" ]; then
    VAULT_PATH=$(python3 -c "import json; print(json.load(open('config/config.json'))['obsidian_vault_path'])" 2>/dev/null)
    if [ -n "$VAULT_PATH" ]; then
        DAILY_NOTE="$VAULT_PATH/Daily/$YESTERDAY.md"
        if [ -f "$DAILY_NOTE" ]; then
            NOTE_MTIME=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$DAILY_NOTE" 2>/dev/null || stat -c "%y" "$DAILY_NOTE" | cut -d. -f1)
            echo "   日记文件: $DAILY_NOTE"
            echo "   最后修改时间: $NOTE_MTIME"

            # 检查是否有健康日志标记
            if grep -q "（健康日志）" "$DAILY_NOTE"; then
                echo "   ✅ 日记中包含健康日志标记"
                # 检查是否有最新数据
                if grep -q "睡眠时长\|HRV\|静息心率" "$DAILY_NOTE"; then
                    echo "   ✅ 日记中包含健康数据"
                else
                    echo "   ⚠️  日记中没有健康数据"
                fi
            else
                echo "   ⚠️  日记中没有健康日志标记"
            fi
        else
            echo "   ⚠️  昨天的日记文件不存在: $DAILY_NOTE"
        fi
    else
        echo "   ⚠️  无法获取Obsidian vault路径"
    fi
else
    echo "   ⚠️  配置文件不存在"
fi
echo ""

# 5. 生成结论
echo "=========================================="
echo "📋 验证结论"
echo "=========================================="

PASS_COUNT=0
TOTAL_COUNT=4

# 检查1: 进程运行
ps aux | grep -E "(cli.*start-scheduler|python.*scheduler)" | grep -v grep > /dev/null && ((PASS_COUNT++))

# 检查2: 日志记录
[ -f "$LOG_FILE" ] && grep -q "🔔 SYNC_GARMIN_DATA 函数被调用" "$LOG_FILE" && ((PASS_COUNT++))

# 检查3: 数据库更新
if [ -f "$DB_FILE" ]; then
    DB_MTIME=$(stat -f "%Sm" -t "%Y-%m-%d" "$DB_FILE" 2>/dev/null || stat -c "%y" "$DB_FILE" | cut -d' ' -f1)
    [ "$DB_MTIME" = "$TODAY" ] && ((PASS_COUNT++))
fi

# 检查4: Obsidian更新
if [ -n "$VAULT_PATH" ] && [ -f "$DAILY_NOTE" ]; then
    grep -q "（健康日志）" "$DAILY_NOTE" && grep -q "睡眠时长\|HRV\|静息心率" "$DAILY_NOTE" && ((PASS_COUNT++))
fi

echo "通过检查: $PASS_COUNT / $TOTAL_COUNT"
echo ""

if [ $PASS_COUNT -eq $TOTAL_COUNT ]; then
    echo "🎉 完美！所有检查都通过了！"
    echo "今天12:00的同步任务已成功执行。"
    exit 0
elif [ $PASS_COUNT -ge 2 ]; then
    echo "⚠️  部分检查通过，但仍有问题需要解决。"
    echo "建议：查看详细日志以了解具体问题。"
    exit 1
else
    echo "❌ 严重问题！大部分检查都失败了。"
    echo "建议：立即检查调度器配置和日志。"
    exit 2
fi

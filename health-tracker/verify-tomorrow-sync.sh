#!/bin/bash
# 验证明天的自动同步是否成功
# 使用方法: ./verify-tomorrow-sync.sh

set -e

PROJECT_ROOT="/Users/taoli/andrewData/health-tracker"
LOG_DIR="$PROJECT_ROOT/logs"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo "======================================"
echo "  验证昨天的自动同步"
echo "======================================"
echo ""

# 获取昨天的日期
YESTERDAY=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d "yesterday" +%Y-%m-%d)
echo "检查日期: $YESTERDAY"
echo ""

ERRORS=0

# ========================================
# 1. 检查调度器进程
# ========================================
echo "[1/5] 检查调度器进程"
if ps aux | grep -v grep | grep -q "start-scheduler"; then
    print_success "调度器进程正在运行"
else
    print_error "调度器进程未运行"
    ((ERRORS++))
fi

# ========================================
# 2. 检查 LaunchAgent
# ========================================
echo ""
echo "[2/5] 检查 LaunchAgent"
if launchctl list | grep -q "health-tracker"; then
    print_success "LaunchAgent 正在运行"
else
    print_error "LaunchAgent 未运行"
    ((ERRORS++))
fi

# ========================================
# 3. 检查调度器日志
# ========================================
echo ""
echo "[3/5] 检查调度器日志"
if [ -f "$LOG_DIR/garmin_scheduler.log" ]; then
    # 查找昨天的同步记录
    if grep -q "$YESTERDAY 数据同步成功" "$LOG_DIR/garmin_scheduler.log"; then
        print_success "日志显示 $YESTERDAY 数据同步成功"
    else
        print_warning "日志中未找到 $YESTERDAY 的同步成功记录"
        echo "  最近的同步记录："
        grep "数据同步" "$LOG_DIR/garmin_scheduler.log" | tail -3
        ((ERRORS++))
    fi
else
    print_error "调度器日志文件不存在"
    ((ERRORS++))
fi

# ========================================
# 4. 检查数据库
# ========================================
echo ""
echo "[4/5] 检查数据库中的数据"
cd "$PROJECT_ROOT"
source venv/bin/activate

if python3 -c "from storage import HealthDatabase; db = HealthDatabase(); record = db.get_record_by_date('$YESTERDAY'); exit(0 if record else 1)" 2>/dev/null; then
    print_success "数据库中有 $YESTERDAY 的数据"

    # 显示数据摘要
    python3 -c "
from storage import HealthDatabase
db = HealthDatabase()
record = db.get_record_by_date('$YESTERDAY')
if record:
    print('  数据摘要:')
    if record.get('sleep_duration'):
        print(f'    睡眠: {record[\"sleep_duration\"]} 分钟')
    if record.get('hrv'):
        print(f'    HRV: {record[\"hrv\"]}')
    if record.get('stress_avg'):
        print(f'    压力: {record[\"stress_avg\"]}')
    if record.get('activities'):
        print(f'    运动: {len(record[\"activities\"])} 条记录')
"
else
    print_error "数据库中没有 $YESTERDAY 的数据"
    ((ERRORS++))
fi

# ========================================
# 5. 检查 Obsidian 日记
# ========================================
echo ""
echo "[5/5] 检查 Obsidian 日记"
OBSIDIAN_FILE="/Users/taoli/Documents/Hercules/Health/$YESTERDAY.md"
if [ -f "$OBSIDIAN_FILE" ]; then
    if grep -q "（健康日志）" "$OBSIDIAN_FILE"; then
        print_success "Obsidian 日记已更新"
    else
        print_warning "Obsidian 日记文件存在，但可能未包含健康日志"
        ((ERRORS++))
    fi
else
    print_warning "Obsidian 日记文件不存在: $OBSIDIAN_FILE"
    ((ERRORS++))
fi

# ========================================
# 总结
# ========================================
echo ""
echo "======================================"
echo "  验证总结"
echo "======================================"
echo ""

if [ $ERRORS -eq 0 ]; then
    print_success "所有检查通过！自动同步工作正常！"
    echo ""
    echo "🎉 自动化系统完全成功！"
    echo ""
    echo "接下来："
    echo "  - 系统会每天 12:00 自动同步"
    echo "  - 每周日 08:00 生成周报"
    echo "  - 每月最后一天 20:00 生成月报"
    echo ""
    echo "查看实时日志: tail -f $LOG_DIR/garmin_scheduler.log"
else
    print_error "发现 $ERRORS 个问题"
    echo ""
    echo "请查看上方错误信息"
    echo "查看详细日志: tail -50 $LOG_DIR/garmin_scheduler.log"
    exit 1
fi

echo ""

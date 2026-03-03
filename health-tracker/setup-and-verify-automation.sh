#!/bin/bash
# 健康追踪自动化 - 完整安装和验证脚本
# 用途：一键安装、测试、验证自动化系统

set -e  # 遇到错误立即退出

PROJECT_ROOT="/Users/taoli/andrewData/health-tracker"
LOG_DIR="$PROJECT_ROOT/logs"
CONFIG_FILE="$PROJECT_ROOT/config/config.json"

echo "======================================"
echo "  健康追踪自动化安装和验证"
echo "======================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 步骤计数
STEP=1
TOTAL_STEPS=7
ERRORS=0

# 辅助函数
print_step() {
    echo ""
    echo "[$STEP/$TOTAL_STEPS] $1"
    ((STEP++))
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    ((ERRORS++))
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# ========================================
# 步骤 1: 检查环境
# ========================================
print_step "检查环境和依赖"

if [ ! -d "$PROJECT_ROOT" ]; then
    print_error "项目目录不存在: $PROJECT_ROOT"
    exit 1
fi

cd "$PROJECT_ROOT"
print_success "项目目录: $PROJECT_ROOT"

# 检查 Python 虚拟环境
if [ ! -d "venv" ]; then
    print_error "虚拟环境不存在，请先运行: python3 -m venv venv"
    exit 1
fi
print_success "虚拟环境存在"

# 激活虚拟环境
source venv/bin/activate
print_success "虚拟环境已激活"

# 检查必需的包
python3 -c "import garminconnect, apscheduler, pytz" 2>/dev/null
if [ $? -eq 0 ]; then
    print_success "必需的 Python 包已安装"
else
    print_warning "缺少必需的包，正在安装..."
    pip install garminconnect apscheduler pytz -q
    print_success "依赖包安装完成"
fi

# ========================================
# 步骤 2: 验证配置文件
# ========================================
print_step "验证配置文件"

if [ ! -f "$CONFIG_FILE" ]; then
    print_error "配置文件不存在: $CONFIG_FILE"
    exit 1
fi

# 检查 Garmin 密码
PASSWORD=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['garmin_password'])")
if [ "$PASSWORD" == "YOUR_PASSWORD_HERE" ] || [ -z "$PASSWORD" ]; then
    print_error "Garmin 密码未配置，请编辑 config/config.json"
    exit 1
fi
print_success "Garmin 密码已配置"

# 检查 Obsidian 路径
VAULT_PATH=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['obsidian_vault_path'])")
if [ ! -d "$VAULT_PATH" ]; then
    print_warning "Obsidian vault 不存在: $VAULT_PATH"
    print_warning "数据将只保存到数据库和 Google Sheets"
else
    print_success "Obsidian vault: $VAULT_PATH"
fi

# ========================================
# 步骤 3: 测试 Garmin 连接
# ========================================
print_step "测试 Garmin 连接（这可能需要 10-30 秒）"

TEST_OUTPUT=$(python3 cli.py garmin-test 2>&1)
if echo "$TEST_OUTPUT" | grep -q "✓ Garmin 认证成功"; then
    print_success "Garmin 连接正常"
else
    print_error "Garmin 连接失败"
    echo "错误详情："
    echo "$TEST_OUTPUT"
    exit 1
fi

# ========================================
# 步骤 4: 测试手动同步
# ========================================
print_step "测试手动同步昨天的数据"

SYNC_OUTPUT=$(python3 cli.py garmin-sync --date yesterday 2>&1)
if echo "$SYNC_OUTPUT" | grep -q "✓ 同步成功"; then
    print_success "手动同步成功"

    # 检查是否生成了数据
    YESTERDAY=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d "yesterday" +%Y-%m-%d)
    if python3 -c "from storage import HealthDatabase; db = HealthDatabase(); record = db.get_record_by_date('$YESTERDAY'); exit(0 if record else 1)" 2>/dev/null; then
        print_success "数据已保存到数据库"
    else
        print_warning "数据可能未保存到数据库"
    fi
else
    print_error "手动同步失败"
    echo "错误详情："
    echo "$SYNC_OUTPUT"
    exit 1
fi

# ========================================
# 步骤 5: 创建日志目录
# ========================================
print_step "创建日志目录"

mkdir -p "$LOG_DIR"
print_success "日志目录: $LOG_DIR"

# ========================================
# 步骤 6: 安装 LaunchAgent
# ========================================
print_step "安装 LaunchAgent（开机自启）"

PLIST_SOURCE="$PROJECT_ROOT/com.health-tracker.scheduler.plist"
PLIST_TARGET="$HOME/Library/LaunchAgents/com.health-tracker.scheduler.plist"

if [ ! -f "$PLIST_SOURCE" ]; then
    print_error "LaunchAgent 配置文件不存在: $PLIST_SOURCE"
    exit 1
fi

# 停止旧的服务（如果存在）
launchctl unload "$PLIST_TARGET" 2>/dev/null || true

# 复制配置文件
cp "$PLIST_SOURCE" "$PLIST_TARGET"
print_success "LaunchAgent 配置文件已复制"

# 启动服务
launchctl load "$PLIST_TARGET"
sleep 2

# 验证服务启动
if launchctl list | grep -q "health-tracker.scheduler"; then
    print_success "LaunchAgent 已启动"
else
    print_error "LaunchAgent 启动失败"
    exit 1
fi

# ========================================
# 步骤 7: 验证调度器运行
# ========================================
print_step "验证调度器运行状态"

# 等待调度器初始化
sleep 3

# 检查进程
if ps aux | grep -v grep | grep -q "cli.py start-scheduler"; then
    print_success "调度器进程正在运行"
else
    print_warning "调度器进程未找到（可能刚启动）"
fi

# 检查日志
if [ -f "$LOG_DIR/scheduler.log" ]; then
    print_success "调度器日志文件已创建"

    # 显示最新日志
    echo ""
    echo "最新日志（最后 5 行）："
    tail -5 "$LOG_DIR/scheduler.log"
else
    print_warning "调度器日志文件未创建（请等待几分钟后查看）"
fi

# ========================================
# 总结
# ========================================
echo ""
echo "======================================"
echo "  安装总结"
echo "======================================"
echo ""

if [ $ERRORS -eq 0 ]; then
    print_success "所有检查通过！自动化已成功配置！"
    echo ""
    echo "接下来："
    echo "1. 明天 12:00 系统会自动同步今天的数据"
    echo "2. 查看实时日志: tail -f $LOG_DIR/scheduler.log"
    echo "3. 查看调度器状态: launchctl list | grep health-tracker"
    echo ""
    echo "验证明天的同步："
    TOMORROW=$(date -v+1d +%Y-%m-%d 2>/dev/null || date -d "tomorrow" +%Y-%m-%d)
    TOMORROW_LOG="$LOG_DIR/sync-$TOMORROW.log"
    echo "  - 检查日志文件: ls -lh $TOMORROW_LOG"
    echo "  - 查看同步状态: grep '✓.*成功' $LOG_DIR/scheduler.log"
else
    print_error "安装过程中遇到 $ERRORS 个错误"
    echo ""
    echo "请查看上方错误信息并修复后重新运行此脚本"
    exit 1
fi

echo ""
echo "======================================"
echo "  当前配置"
echo "======================================"
echo "同步时间: 每天 12:00"
echo "重试时间: 13:00, 14:00, 15:00, 16:00, 17:00, 18:00"
echo "周报生成: 每周日 08:00"
echo "月报生成: 每月最后一天 20:00"
echo ""
echo "如有问题，请查看日志: $LOG_DIR/scheduler.log"
echo ""

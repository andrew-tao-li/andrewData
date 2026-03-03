#!/bin/bash
# Health Tracker - 系统健康检查脚本
# 用途: 验证所有组件是否正常工作

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Health Tracker - 系统健康检查${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# 测试计数器
TESTS_PASSED=0
TESTS_FAILED=0
TOTAL_TESTS=0

# 测试函数
run_test() {
    local test_name="$1"
    local test_command="$2"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${YELLOW}[测试 $TOTAL_TESTS]${NC} $test_name"

    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅ 通过${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "   ${RED}❌ 失败${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# 测试函数（带输出）
run_test_with_output() {
    local test_name="$1"
    local test_command="$2"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${YELLOW}[测试 $TOTAL_TESTS]${NC} $test_name"

    local output
    output=$(eval "$test_command" 2>&1)
    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        echo -e "   ${GREEN}✅ 通过${NC}"
        if [ ! -z "$output" ]; then
            echo "   输出: $output"
        fi
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "   ${RED}❌ 失败${NC}"
        if [ ! -z "$output" ]; then
            echo "   错误: $output"
        fi
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

echo -e "${BLUE}=== 第 1 部分: 基础系统检查 ===${NC}"
echo ""

# 测试 1: LaunchAgent 状态
run_test_with_output "LaunchAgent 是否运行" \
    "launchctl list | grep health-tracker"

# 测试 2: 调度器进程
run_test_with_output "调度器进程是否活跃" \
    "ps aux | grep 'start-scheduler' | grep -v grep"

# 测试 3: 虚拟环境
run_test "Python 虚拟环境是否存在" \
    "test -d venv && test -f venv/bin/python"

# 测试 4: 日志目录
run_test "日志目录是否存在" \
    "test -d logs"

# 测试 5: 调度器日志
if [ -f "logs/garmin_scheduler.log" ]; then
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${YELLOW}[测试 $TOTAL_TESTS]${NC} 调度器日志是否正常"
    if grep -q "Scheduler started" logs/garmin_scheduler.log; then
        echo -e "   ${GREEN}✅ 通过${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "   ${RED}❌ 失败 - 未找到启动记录${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${YELLOW}[测试 $TOTAL_TESTS]${NC} 调度器日志是否正常"
    echo -e "   ${RED}❌ 失败 - 日志文件不存在${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""
echo -e "${BLUE}=== 第 2 部分: 配置验证 ===${NC}"
echo ""

# 测试 6: misfire_grace_time 配置
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -e "${YELLOW}[测试 $TOTAL_TESTS]${NC} misfire_grace_time 是否设置为 60"
if grep -q "misfire_grace_time=60" garmin/scheduler.py; then
    echo -e "   ${GREEN}✅ 通过${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "   ${RED}❌ 失败 - 配置错误${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# 测试 7: LaunchAgent plist 文件
run_test "LaunchAgent plist 文件是否存在" \
    "test -f ~/Library/LaunchAgents/com.health-tracker.scheduler.plist"

# 测试 8: 环境变量配置
run_test ".env 文件是否存在" \
    "test -f .env"

echo ""
echo -e "${BLUE}=== 第 3 部分: Garmin 连接测试 ===${NC}"
echo ""

# 测试 9: 测试 Garmin 登录（需要激活 venv）
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -e "${YELLOW}[测试 $TOTAL_TESTS]${NC} Garmin API 连接是否正常"
echo -e "   ${YELLOW}⏳ 正在测试 Garmin 登录...${NC}"

source venv/bin/activate
if python -c "
from garmin.auth import GarminAuth
from config import Config
try:
    config = Config()
    auth = GarminAuth(config)
    client = auth.login()
    print('✅ Garmin 登录成功')
    exit(0)
except Exception as e:
    print(f'❌ Garmin 登录失败: {e}')
    exit(1)
" 2>&1; then
    echo -e "   ${GREEN}✅ 通过${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "   ${RED}❌ 失败${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""
echo -e "${BLUE}=== 第 4 部分: 调度任务验证 ===${NC}"
echo ""

# 测试 10: 验证已添加的任务
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -e "${YELLOW}[测试 $TOTAL_TESTS]${NC} 每日同步任务是否已添加"
if grep -q "Added job.*每日 Garmin 数据同步" logs/garmin_scheduler.log; then
    echo -e "   ${GREEN}✅ 通过${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "   ${RED}❌ 失败${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -e "${YELLOW}[测试 $TOTAL_TESTS]${NC} 周报任务是否已添加"
if grep -q "Added job.*每周健康报告" logs/garmin_scheduler.log; then
    echo -e "   ${GREEN}✅ 通过${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "   ${RED}❌ 失败${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -e "${YELLOW}[测试 $TOTAL_TESTS]${NC} 月报任务是否已添加"
if grep -q "Added job.*每月健康报告" logs/garmin_scheduler.log; then
    echo -e "   ${GREEN}✅ 通过${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "   ${RED}❌ 失败${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}测试结果汇总${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""
echo -e "总测试数: $TOTAL_TESTS"
echo -e "${GREEN}通过: $TESTS_PASSED${NC}"
echo -e "${RED}失败: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 所有测试通过！系统运行正常！${NC}"
    echo ""
    echo -e "${BLUE}📅 明天 12:00 同步任务应该会正常执行！${NC}"
    exit 0
else
    echo -e "${RED}⚠️  发现 $TESTS_FAILED 个问题，需要修复！${NC}"
    exit 1
fi

#!/bin/bash
# 设置 Garmin 自动同步调度器（macOS LaunchAgent）

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PLIST_NAME="com.health-tracker.scheduler.plist"
PLIST_SRC="$SCRIPT_DIR/$PLIST_NAME"
PLIST_DST="$HOME/Library/LaunchAgents/$PLIST_NAME"

echo "========================================="
echo "Health Tracker - 调度器安装脚本"
echo "========================================="
echo ""

if [ "${HEALTH_TRACKER_ALLOW_LEGACY_SCHEDULER:-}" != "1" ]; then
    echo "❌ 已阻止：这是旧版常驻 scheduler，会使用过时的同步逻辑。"
    echo ""
    echo "当前稳定方案："
    echo "  • Garmin: com.health-tracker.garmin-guard（12:00, 13:00, 14:00, 15:00, 16:00）"
    echo "  • 晨间备忘录: com.health-tracker.notes-sync（19:00, 20:00, 21:00, 22:00, 23:00）"
    echo ""
    echo "如确需调试旧 scheduler，请显式设置："
    echo "  HEALTH_TRACKER_ALLOW_LEGACY_SCHEDULER=1 ./setup-scheduler.sh"
    exit 2
fi

# 检查 plist 文件是否存在
if [ ! -f "$PLIST_SRC" ]; then
    echo "❌ 错误: 找不到 $PLIST_NAME"
    exit 1
fi

# 创建 LaunchAgents 目录（如果不存在）
mkdir -p "$HOME/Library/LaunchAgents"

# 停止旧的服务（如果正在运行）
if launchctl list | grep -q "com.health-tracker.scheduler"; then
    echo "⏹  停止现有的调度器服务..."
    launchctl bootout "gui/$(id -u)/$PLIST_NAME" 2>/dev/null || launchctl unload "$PLIST_DST" 2>/dev/null
fi

# 停止手动运行的调度器进程（如果存在）
echo "🛑 停止手动运行的调度器进程..."
pkill -f "start-scheduler" 2>/dev/null || true

# 复制 plist 文件
echo "📋 复制配置文件到 ~/Library/LaunchAgents/..."
cp "$PLIST_SRC" "$PLIST_DST"

# 设置正确的权限
chmod 644 "$PLIST_DST"

# 加载服务（使用现代命令）
echo "🚀 启动调度器服务..."
launchctl bootstrap "gui/$(id -u)" "$PLIST_DST" 2>/dev/null || launchctl load "$PLIST_DST"

# 检查状态
echo ""
if launchctl list | grep -q "com.health-tracker.scheduler"; then
    echo "✅ 调度器已成功启动！"
    echo ""
    echo "📊 自动化任务："
    echo "  • 每天 12:00 - 从 Garmin 同步数据"
    echo "  • 每周日 08:00 - 生成健康周报"
    echo "  • 每月最后一天 20:00 - 生成健康月报"
    echo "  • 失败重试时间: 13:00, 14:00, 15:00, 16:00, 17:00, 18:00"
    echo ""
    echo "📝 日志位置："
    echo "  • 标准输出: $SCRIPT_DIR/logs/scheduler.log"
    echo "  • 错误日志: $SCRIPT_DIR/logs/scheduler-error.log"
    echo ""
    echo "🔧 管理命令："
    echo "  • 停止服务: launchctl bootout gui/\$(id -u) ~/Library/LaunchAgents/$PLIST_NAME"
    echo "  • 启动服务: launchctl bootstrap gui/\$(id -u) ~/Library/LaunchAgents/$PLIST_NAME"
    echo "  • 查看状态: launchctl list | grep health-tracker"
    echo "  • 查看进程: ps aux | grep start-scheduler"
else
    echo "❌ 调度器启动失败，请检查日志"
    exit 1
fi

echo "========================================="

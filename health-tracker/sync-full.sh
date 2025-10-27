#!/bin/bash
# 完整双向同步：拉取 → 解析 → 推送

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

source venv/bin/activate

echo "📥 拉取云端最新数据..."
python sync_cli.py pull

echo ""
echo "📝 解析今天的健康日志..."
python cli.py parse --date today

echo ""
echo "📊 查看今天的数据..."
python cli.py show --date today

echo ""
echo "☁️  推送到云端..."
python sync_cli.py push

echo ""
echo "✅ 完整同步完成！"

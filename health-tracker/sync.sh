#!/bin/bash
# 一键同步健康数据

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 激活虚拟环境
source venv/bin/activate

# 解析今天的笔记
echo "📝 正在解析今天的健康日志..."
python cli.py parse --date today

# 同步到云端
echo "☁️  正在同步到云端..."
python sync_cli.py push

echo "✅ 同步完成！"

#!/bin/bash
# Health Tracker 快速启动脚本 (macOS/Linux)

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ 虚拟环境不存在，请先运行 ./install.sh"
    exit 1
fi

# 运行 CLI
python cli.py "$@"

#!/bin/bash
# Health Tracker 一键安装脚本 (macOS/Linux)

set -e  # 遇到错误立即退出

echo "🚀 Health Tracker 安装脚本"
echo "=========================="
echo ""

# 检查 Python
echo "📌 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3"
    echo ""
    echo "请先安装 Python 3.8+："
    echo "  macOS: brew install python@3.11"
    echo "  Linux: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
echo "✓ Python 版本: $PYTHON_VERSION"

# 检查版本是否满足要求
REQUIRED_VERSION="3.8"
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python 版本过低，需要 3.8 或更高版本"
    exit 1
fi

echo ""

# 创建虚拟环境
echo "📦 创建虚拟环境..."
if [ -d "venv" ]; then
    echo "⚠️  虚拟环境已存在，跳过创建"
else
    python3 -m venv venv
    echo "✓ 虚拟环境创建成功"
fi

echo ""

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate
echo "✓ 虚拟环境已激活"

echo ""

# 升级 pip
echo "⬆️  升级 pip..."
pip install --upgrade pip -q
echo "✓ pip 已升级"

echo ""

# 安装依赖
echo "📥 安装项目依赖..."
echo "   (这可能需要几分钟...)"
pip install -r requirements.txt -q

if [ $? -eq 0 ]; then
    echo "✓ 依赖安装成功"
else
    echo "❌ 依赖安装失败，尝试使用国内镜像..."
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
fi

echo ""

# 创建配置文件
echo "⚙️  配置项目..."
if [ ! -f config/config.json ]; then
    cp config/config.example.json config/config.json
    echo "✓ 配置文件已创建: config/config.json"
    echo "⚠️  请编辑此文件填写你的配置"
else
    echo "⚠️  配置文件已存在，跳过创建"
fi

echo ""

# 测试安装
echo "🧪 测试安装..."
if python cli.py --help > /dev/null 2>&1; then
    echo "✓ 安装测试通过"
else
    echo "❌ 安装测试失败"
    exit 1
fi

echo ""
echo "✅ 安装完成！"
echo "=========================="
echo ""
echo "📋 下一步："
echo ""
echo "1️⃣  编辑配置文件："
echo "   nano config/config.json"
echo "   或"
echo "   open -a TextEdit config/config.json  # macOS"
echo ""
echo "   需要填写："
echo "   - Claude API Key (从 https://console.anthropic.com/ 获取)"
echo "   - Obsidian Vault 路径"
echo ""
echo "2️⃣  激活虚拟环境（每次使用前）："
echo "   source venv/bin/activate"
echo ""
echo "3️⃣  开始使用："
echo "   python cli.py parse --date today"
echo "   python cli.py stats"
echo "   python cli.py --help"
echo ""
echo "📚 查看文档："
echo "   cat INSTALLATION.md  - 安装指南"
echo "   cat SETUP.md         - 配置说明"
echo "   cat EXAMPLES.md      - 使用示例"
echo ""
echo "🎉 祝使用愉快！"

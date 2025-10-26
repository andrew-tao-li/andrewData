#!/bin/bash

# Health Tracker - macOS + Conda 安装脚本
# 适用于已安装 conda/miniconda/anaconda 的 macOS 系统

set -e  # 遇到错误时退出

echo "🚀 Health Tracker 安装脚本 (macOS + Conda)"
echo "=========================================="
echo ""

# 检查 conda 是否安装
if ! command -v conda &> /dev/null; then
    echo "❌ 未找到 conda，请先安装 Anaconda 或 Miniconda"
    echo "   下载地址: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

echo "✓ Conda 版本: $(conda --version)"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "📂 项目目录: $SCRIPT_DIR"
echo ""

# 检查是否已有同名环境
ENV_NAME="health-tracker"
if conda env list | grep -q "^${ENV_NAME} "; then
    echo "⚠️  环境 '$ENV_NAME' 已存在"
    read -p "是否删除并重新创建? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  删除旧环境..."
        conda env remove -n $ENV_NAME -y
    else
        echo "❌ 安装取消"
        exit 1
    fi
fi

# 创建 conda 环境
echo "📦 创建 conda 环境 '$ENV_NAME' (Python 3.11)..."
conda create -n $ENV_NAME python=3.11 -y

# 激活环境并安装依赖
echo ""
echo "📥 安装项目依赖..."
# 使用 conda run 在指定环境中执行命令
conda run -n $ENV_NAME pip install --upgrade pip
conda run -n $ENV_NAME pip install -r requirements.txt

# 检查是否安装成功
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 依赖安装成功！"
else
    echo ""
    echo "⚠️  安装过程中出现警告，尝试使用国内镜像..."
    conda run -n $ENV_NAME pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
fi

# 创建配置文件
echo ""
if [ ! -f config/config.json ]; then
    echo "⚙️  创建配置文件..."
    cp config/config.example.json config/config.json
    echo "✓ 配置文件已创建: config/config.json"
else
    echo "ℹ️  配置文件已存在，跳过创建"
fi

# 测试安装
echo ""
echo "🧪 测试安装..."
if conda run -n $ENV_NAME python cli.py --help &> /dev/null; then
    echo "✅ 测试通过！"
else
    echo "⚠️  测试失败，请检查安装"
fi

echo ""
echo "=========================================="
echo "🎉 安装完成！"
echo ""
echo "📝 下一步操作："
echo ""
echo "1️⃣  激活 conda 环境："
echo "   conda activate health-tracker"
echo ""
echo "2️⃣  编辑配置文件（必须）："
echo "   nano config/config.json"
echo "   或: code config/config.json  (如果你用 VSCode)"
echo ""
echo "   需要填写："
echo "   - API Key (Anthropic 或 OpenRouter)"
echo "   - Obsidian vault 路径"
echo ""
echo "3️⃣  测试运行："
echo "   python cli.py --help"
echo "   python cli.py parse --date today"
echo ""
echo "4️⃣  查看文档："
echo "   - README.md - 项目概览"
echo "   - INSTALLATION.md - 详细安装指南"
echo "   - QUICKSTART.md - 快速开始"
echo "   - docs/IMAGE_PROCESSING_WALKTHROUGH.md - 图片处理详解"
echo ""
echo "💡 提示："
echo "   - 每次使用前运行: conda activate health-tracker"
echo "   - 用完后可运行: conda deactivate"
echo ""
echo "❓ 遇到问题？查看 FAQ.md 或项目文档"
echo "=========================================="

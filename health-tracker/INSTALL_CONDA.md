# Health Tracker - Conda 安装指南

本指南适用于已安装 **Conda/Miniconda/Anaconda** 的 macOS、Linux 或 Windows 系统。

---

## 🎯 快速安装（推荐）

### macOS / Linux

```bash
# 1. 克隆或下载项目到本地
git clone <你的仓库URL>
cd health-tracker

# 2. 运行安装脚本
chmod +x install_conda.sh
./install_conda.sh

# 3. 激活环境
conda activate health-tracker

# 4. 编辑配置文件
nano config/config.json

# 5. 开始使用！
python cli.py --help
```

### Windows

```cmd
REM 1. 克隆或下载项目到本地
git clone <你的仓库URL>
cd health-tracker

REM 2. 打开 Anaconda Prompt，然后执行：
conda create -n health-tracker python=3.11 -y
conda activate health-tracker
pip install -r requirements.txt

REM 3. 创建配置文件
copy config\config.example.json config\config.json
notepad config\config.json

REM 4. 开始使用！
python cli.py --help
```

---

## 📋 详细步骤

### 前置要求

- ✅ 已安装 **Conda** (Anaconda/Miniconda)
  - 检查：在终端运行 `conda --version`
  - 如未安装，访问：https://docs.conda.io/en/latest/miniconda.html

### 步骤 1: 获取项目

**方法 A: 使用 Git**

```bash
git clone <你的仓库URL>
cd health-tracker
```

**方法 B: 下载 ZIP**

1. 下载项目 ZIP 文件
2. 解压到任意目录
3. 在终端/命令提示符中进入该目录

### 步骤 2: 创建 Conda 环境

```bash
# 创建名为 health-tracker 的环境，使用 Python 3.11
conda create -n health-tracker python=3.11 -y

# 激活环境
conda activate health-tracker

# 激活后，命令提示符前会显示 (health-tracker)
```

### 步骤 3: 安装依赖

```bash
# 升级 pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

**如果安装速度慢（国内用户）：**

```bash
# 使用清华镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 步骤 4: 配置项目

```bash
# 复制配置模板
cp config/config.example.json config/config.json

# 编辑配置文件
# macOS/Linux:
nano config/config.json
# 或使用 VSCode:
code config/config.json

# Windows:
notepad config\config.json
```

**配置示例：**

```json
{
  "use_openrouter": true,
  "openrouter_api_key": "sk-or-你的密钥",
  "openrouter_model": "anthropic/claude-sonnet-5",
  "obsidian_vault_path": "/Users/你的用户名/Documents/Obsidian/MyVault",
  "obsidian_health_folder": "Health",
  "database_path": "health_data.db",
  "claude_model": "claude-sonnet-5"
}
```

**必填项：**

1. **API Key**
   - 如使用 Anthropic API：填写 `claude_api_key`
   - 如使用 OpenRouter：填写 `openrouter_api_key`，并设置 `use_openrouter: true`

2. **Obsidian Vault 路径**
   - macOS: `/Users/用户名/Documents/Obsidian/VaultName`
   - Windows: `C:\\Users\\用户名\\Documents\\Obsidian\\VaultName` （注意双反斜杠）
   - Linux: `/home/用户名/Documents/Obsidian/VaultName`

**如何找到 Obsidian vault 路径？**

- **macOS**: 在 Finder 中找到 vault 文件夹，拖动到终端窗口
- **Windows**: 在文件资源管理器中打开 vault，点击地址栏复制路径
- **Linux**: 右键 vault 文件夹 → 属性 → 位置

### 步骤 5: 测试安装

```bash
# 确保 conda 环境已激活
conda activate health-tracker

# 运行帮助命令
python cli.py --help

# 如果看到命令列表，说明安装成功！
```

---

## 🎮 日常使用

### 每次使用的步骤

```bash
# 1. 激活环境（必须）
conda activate health-tracker

# 2. 进入项目目录
cd /path/to/health-tracker

# 3. 使用命令
python cli.py parse --date today
python cli.py show --date today
python cli.py stats --days 7
python cli.py chat "我最近睡眠质量如何？"

# 4. 用完后退出环境（可选）
conda deactivate
```

### 常用命令速查

```bash
# 解析笔记
python cli.py parse --date today
python cli.py parse --date 2024-01-15
python cli.py parse --date yesterday

# 查看数据
python cli.py show --date today
python cli.py stats --days 7
python cli.py stats --days 30

# AI 对话分析
python cli.py chat "我的血压趋势如何？"
python cli.py chat "最近有什么健康建议吗？"

# 生成报告
python cli.py report --days 7
python cli.py report --days 30

# 同步到 Google Sheets（需配置）
python cli.py sync
```

---

## 🔧 Conda 环境管理

### 查看所有环境

```bash
conda env list
```

### 删除环境

```bash
conda env remove -n health-tracker
```

### 导出环境（用于分享）

```bash
conda env export > environment.yml
```

### 从文件创建环境

```bash
conda env create -f environment.yml
```

### 更新依赖

```bash
conda activate health-tracker
pip install -r requirements.txt --upgrade
```

---

## 💡 Conda vs Virtualenv

**为什么选择 Conda？**

| 特性 | Conda | Virtualenv |
|------|-------|------------|
| 包管理 | Python + 非 Python 包 | 仅 Python 包 |
| 环境隔离 | 完全隔离（包括系统库） | Python 包隔离 |
| 跨平台 | 优秀 | 良好 |
| 科学计算库 | 优化编译版本 | 标准版本 |
| 磁盘占用 | 较大 | 较小 |

**本项目使用 Conda 的优势：**

- ✅ 更好地处理 Pillow、matplotlib 等图像处理库
- ✅ 避免编译问题（特别是在 Windows 上）
- ✅ 统一的跨平台体验

---

## ❓ 常见问题

### Q: conda 命令找不到？

**A**: 需要初始化 conda

```bash
# 查找 conda 安装路径
which conda

# 如果安装了 Anaconda/Miniconda 但命令不可用，运行：
source ~/anaconda3/bin/activate  # Anaconda
# 或
source ~/miniconda3/bin/activate  # Miniconda

# 初始化 shell
conda init bash  # 或 conda init zsh
```

重启终端后再试。

### Q: 环境激活失败？

**A**:

```bash
# 尝试手动激活
source activate health-tracker

# 或使用完整路径
conda activate health-tracker
```

### Q: Windows 上 conda activate 不工作？

**A**: 使用 **Anaconda Prompt** 而不是普通命令提示符

1. 开始菜单搜索 "Anaconda Prompt"
2. 在 Anaconda Prompt 中运行命令

### Q: 依赖安装失败？

**A**:

```bash
# 方法 1: 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 方法 2: 分步安装
conda activate health-tracker
pip install anthropic
pip install gspread google-auth
pip install python-frontmatter
pip install Pillow matplotlib pandas
pip install python-dotenv schedule click rich

# 方法 3: 使用 conda 安装部分包
conda install -c conda-forge pillow matplotlib pandas
pip install anthropic gspread python-frontmatter click rich
```

### Q: 如何在 Jupyter Notebook 中使用？

**A**:

```bash
# 安装 Jupyter
conda activate health-tracker
conda install jupyter ipykernel

# 添加内核
python -m ipykernel install --user --name=health-tracker

# 启动 Jupyter
jupyter notebook
```

然后在 Notebook 中选择 "health-tracker" 内核。

### Q: macOS 上遇到权限问题？

**A**:

```bash
# 不要使用 sudo！
# 确保 conda 安装在用户目录下

# 检查 conda 路径
which conda
# 应该显示类似: /Users/你的用户名/anaconda3/bin/conda

# 如果需要修复权限
chmod -R u+w ~/anaconda3
```

---

## 🚀 进阶配置

### 设置别名（可选）

在 `~/.bashrc` 或 `~/.zshrc` 中添加：

```bash
# Health Tracker 快捷命令
alias ht='conda activate health-tracker && cd ~/path/to/health-tracker'
alias ht-parse='python ~/path/to/health-tracker/cli.py parse'
alias ht-stats='python ~/path/to/health-tracker/cli.py stats'
alias ht-chat='python ~/path/to/health-tracker/cli.py chat'
```

使用：

```bash
ht              # 激活环境并进入目录
ht-parse --date today
ht-stats --days 7
ht-chat "我的健康趋势如何？"
```

### 自动激活环境（可选）

创建项目启动脚本 `start.sh`：

```bash
#!/bin/bash
conda activate health-tracker
cd "$(dirname "$0")"
python cli.py "$@"
```

使用：

```bash
chmod +x start.sh
./start.sh parse --date today
./start.sh stats --days 7
```

---

## 📚 相关文档

- **README.md** - 项目概览
- **INSTALLATION.md** - 通用安装指南（包括 virtualenv）
- **QUICKSTART.md** - 快速开始教程
- **SETUP.md** - Google Sheets 配置
- **docs/OPENROUTER_SETUP.md** - OpenRouter API 配置
- **docs/IMAGE_PROCESSING_WALKTHROUGH.md** - 图片处理详解
- **FAQ.md** - 常见问题解答

---

## 💬 获取帮助

如遇到问题：

1. 查看 **FAQ.md**
2. 查看 **INSTALLATION.md** 的故障排除部分
3. 检查配置文件格式是否正确
4. 确保 API key 有效且有余额

---

**祝你使用愉快！** 🎉

有问题随时查看文档或提 issue。

# 跨平台安装指南

本指南适用于 macOS、Windows 和 Linux 系统。

## 目录

- [前置要求](#前置要求)
- [macOS 安装](#macos-安装)
- [Windows 安装](#windows-安装)
- [Linux 安装](#linux-安装)
- [配置说明](#配置说明)
- [验证安装](#验证安装)
- [常见问题](#常见问题)

---

## 前置要求

### 所有平台共同要求

- **Python 3.8+**
- **pip** (Python 包管理器)
- **Git** (可选，用于克隆仓库)
- **Obsidian** (可选，用于编辑笔记)

---

## macOS 安装

### 1. 安装 Python

**方法 A: 使用 Homebrew（推荐）**

```bash
# 安装 Homebrew（如果还没有）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 Python
brew install python@3.11

# 验证安装
python3 --version
```

**方法 B: 从官网下载**

1. 访问 https://www.python.org/downloads/
2. 下载 macOS 安装包
3. 运行安装程序
4. 在终端验证：`python3 --version`

### 2. 克隆/下载项目

```bash
# 使用 Git
git clone <your-repo-url>
cd health-tracker

# 或者下载 ZIP 并解压
# cd /path/to/health-tracker
```

### 3. 创建虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 激活后，提示符前会显示 (venv)
```

### 4. 安装依赖

```bash
# 升级 pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

### 5. 配置项目

```bash
# 复制配置文件
cp config/config.example.json config/config.json

# 使用文本编辑器编辑配置
# macOS 自带的编辑器
open -a TextEdit config/config.json

# 或使用 VSCode
code config/config.json

# 或使用 vim
vim config/config.json
```

**配置示例（macOS）：**

```json
{
  "claude_api_key": "sk-ant-...",
  "obsidian_vault_path": "/Users/你的用户名/Documents/Obsidian/MyVault",
  "obsidian_health_folder": "Health",
  "database_path": "health_data.db",
  "claude_model": "claude-3-5-sonnet-20241022"
}
```

**如何找到 Obsidian vault 路径：**

```bash
# 在 Finder 中找到 vault 文件夹
# 右键 → "服务" → "新建位于文件夹位置的终端窗口"
# 然后运行：
pwd
# 复制显示的路径
```

### 6. 测试运行

```bash
# 测试命令行工具
python cli.py --help

# 如果看到帮助信息，说明安装成功！
```

### macOS 特殊注意事项

#### 权限问题

```bash
# 如果遇到权限错误，给脚本执行权限
chmod +x cli.py

# 现在可以直接运行
./cli.py --help
```

#### 中文路径支持

macOS 完全支持中文路径，可以安全使用：

```json
{
  "obsidian_vault_path": "/Users/张三/文档/我的笔记"
}
```

#### 使用 zsh shell

macOS Catalina+ 默认使用 zsh，所有命令都兼容。

---

## Windows 安装

### 1. 安装 Python

**方法 A: 从官网下载（推荐）**

1. 访问 https://www.python.org/downloads/
2. 下载 Windows 安装包（64位）
3. **重要**: 运行安装程序时，勾选 "Add Python to PATH"
4. 选择 "Install Now"
5. 验证安装：

```cmd
# 打开命令提示符（Win + R，输入 cmd）
python --version
```

**方法 B: 使用 Microsoft Store**

1. 打开 Microsoft Store
2. 搜索 "Python 3.11"
3. 点击安装
4. 安装完成后在命令提示符验证

### 2. 下载项目

**方法 A: 使用 Git**

```cmd
# 如果没有 Git，先安装：https://git-scm.com/download/win
git clone <your-repo-url>
cd health-tracker
```

**方法 B: 下载 ZIP**

1. 下载项目 ZIP 文件
2. 解压到任意文件夹，例如 `C:\Users\你的用户名\health-tracker`
3. 在该文件夹中打开命令提示符

**如何在文件夹中打开命令提示符：**
- 在文件夹地址栏输入 `cmd` 然后回车
- 或者 Shift + 右键 → "在此处打开命令窗口"

### 3. 创建虚拟环境

```cmd
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 激活后，提示符前会显示 (venv)
```

**如果遇到执行策略错误：**

```powershell
# 使用 PowerShell 以管理员身份运行
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 然后再次激活虚拟环境
venv\Scripts\activate
```

### 4. 安装依赖

```cmd
# 升级 pip
python -m pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

**常见问题：**

如果安装 `Pillow` 失败，可能需要安装 Visual C++ 构建工具：
- 下载：https://visualstudio.microsoft.com/visual-cpp-build-tools/
- 或者使用预编译的 wheel：`pip install --upgrade Pillow`

### 5. 配置项目

```cmd
# 复制配置文件
copy config\config.example.json config\config.json

# 使用记事本编辑
notepad config\config.json

# 或使用 VSCode
code config\config.json
```

**配置示例（Windows）：**

```json
{
  "claude_api_key": "sk-ant-...",
  "obsidian_vault_path": "C:\\Users\\你的用户名\\Documents\\Obsidian\\MyVault",
  "obsidian_health_folder": "Health",
  "database_path": "health_data.db",
  "claude_model": "claude-3-5-sonnet-20241022"
}
```

**⚠️ 重要：Windows 路径需要双反斜杠 `\\` 或使用正斜杠 `/`**

```json
// 方式 1: 双反斜杠（推荐）
"obsidian_vault_path": "C:\\Users\\Andrew\\Documents\\Obsidian\\MyVault"

// 方式 2: 正斜杠
"obsidian_vault_path": "C:/Users/Andrew/Documents/Obsidian/MyVault"

// ❌ 错误：单反斜杠
"obsidian_vault_path": "C:\Users\Andrew\Documents\Obsidian\MyVault"
```

**如何找到 Obsidian vault 路径：**

1. 在文件资源管理器中打开 vault 文件夹
2. 点击地址栏，会显示完整路径
3. 复制路径
4. 在 JSON 中替换 `\` 为 `\\`

### 6. 测试运行

```cmd
# 测试命令行工具
python cli.py --help

# 如果看到帮助信息，说明安装成功！
```

### Windows 特殊注意事项

#### 中文路径问题

Windows 支持中文路径，但建议：
- 使用 UTF-8 编码保存配置文件
- 确保命令提示符使用 UTF-8：

```cmd
chcp 65001
```

可以将此命令添加到批处理文件中。

#### 创建快捷方式

**方法 1: 批处理文件**

创建 `health-tracker.bat`：

```batch
@echo off
cd /d C:\Users\你的用户名\health-tracker
call venv\Scripts\activate
python cli.py %*
```

使用：
```cmd
health-tracker.bat parse --date today
```

**方法 2: PowerShell 脚本**

创建 `health-tracker.ps1`：

```powershell
$scriptPath = "C:\Users\你的用户名\health-tracker"
Set-Location $scriptPath
& .\venv\Scripts\Activate.ps1
python cli.py $args
```

#### 使用 Windows Terminal（推荐）

1. 从 Microsoft Store 安装 "Windows Terminal"
2. 更好的中文支持和彩色输出
3. 支持多标签页

---

## Linux 安装

### 1. 安装 Python

**Ubuntu/Debian：**

```bash
# 更新包列表
sudo apt update

# 安装 Python 3 和 pip
sudo apt install python3 python3-pip python3-venv

# 验证
python3 --version
```

**Fedora/RHEL：**

```bash
sudo dnf install python3 python3-pip

# 验证
python3 --version
```

**Arch Linux：**

```bash
sudo pacman -S python python-pip

# 验证
python --version
```

### 2. 克隆项目

```bash
git clone <your-repo-url>
cd health-tracker
```

### 3. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. 配置项目

```bash
cp config/config.example.json config/config.json
nano config/config.json  # 或使用 vim, gedit 等
```

配置示例：

```json
{
  "claude_api_key": "sk-ant-...",
  "obsidian_vault_path": "/home/你的用户名/Documents/Obsidian/MyVault",
  "obsidian_health_folder": "Health",
  "database_path": "health_data.db",
  "claude_model": "claude-3-5-sonnet-20241022"
}
```

### 6. 测试运行

```bash
python cli.py --help
```

---

## 配置说明

### 必需配置

#### 1. Claude API Key

**获取方式：**

1. 访问 https://console.anthropic.com/
2. 注册/登录账号
3. 进入 "API Keys" 页面
4. 点击 "Create Key"
5. 复制 API Key（格式：`sk-ant-...`）
6. 粘贴到配置文件的 `claude_api_key` 字段

**💰 费用估算：**
- 每天解析 1-2 条笔记：约 $0.05-0.10
- 每月约 $1.5-3

#### 2. Obsidian Vault 路径

**各平台路径示例：**

```json
// macOS
"obsidian_vault_path": "/Users/andrew/Documents/Obsidian/MyVault"

// Windows
"obsidian_vault_path": "C:\\Users\\Andrew\\Documents\\Obsidian\\MyVault"

// Linux
"obsidian_vault_path": "/home/andrew/Documents/Obsidian/MyVault"
```

**验证路径是否正确：**

```bash
# macOS/Linux
ls "/Users/andrew/Documents/Obsidian/MyVault"

# Windows
dir "C:\Users\Andrew\Documents\Obsidian\MyVault"
```

### 可选配置

#### Google Sheets 同步（可选）

如果要使用云端同步功能，需要配置 Google Sheets：

**详细步骤见 SETUP.md**，简要流程：

1. 创建 Google Cloud 项目
2. 启用 Sheets API 和 Drive API
3. 创建服务账号
4. 下载凭证 JSON 文件保存为 `config/google-credentials.json`
5. 创建 Google Sheet 并分享给服务账号
6. 在配置文件中添加：

```json
{
  "google_sheets_credentials": "config/google-credentials.json",
  "google_sheet_id": "your-sheet-id-here"
}
```

---

## 验证安装

### 基础测试

```bash
# 1. 检查 Python 版本
python --version
# 或 python3 --version

# 2. 检查依赖
pip list | grep anthropic
pip list | grep rich

# 3. 运行 CLI
python cli.py --help

# 4. 运行测试
python tests/test_parser.py
```

### 完整测试流程

#### 1. 创建测试笔记

在你的 Obsidian vault 的 Health 文件夹中创建今天的笔记：

```bash
# macOS/Linux
touch "/Users/andrew/Documents/Obsidian/MyVault/Health/$(date +%Y-%m-%d).md"

# Windows (PowerShell)
New-Item "C:\Users\Andrew\Documents\Obsidian\MyVault\Health\$(Get-Date -Format yyyy-MM-dd).md"
```

编辑笔记内容（参考 `example_note.md`）。

#### 2. 解析笔记

```bash
python cli.py parse --date today
```

如果成功，你会看到提取的数据！

#### 3. 查看数据

```bash
# 查看今天的记录
python cli.py show --date today

# 查看统计
python cli.py stats --days 7
```

---

## 常见问题

### 所有平台通用

#### Q: 找不到 `python` 命令

**A**: 尝试使用 `python3`：

```bash
# 创建别名（可选）
# macOS/Linux: 添加到 ~/.bashrc 或 ~/.zshrc
alias python=python3
alias pip=pip3

# Windows: 通常不需要，安装时勾选 "Add to PATH" 即可
```

#### Q: pip 安装依赖很慢

**A**: 使用国内镜像：

```bash
# 临时使用
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 永久配置（推荐）
# macOS/Linux
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# Windows
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

#### Q: 虚拟环境激活失败

**macOS/Linux:**
```bash
# 确保脚本有执行权限
chmod +x venv/bin/activate
source venv/bin/activate
```

**Windows:**
```cmd
# 使用完整路径
C:\path\to\health-tracker\venv\Scripts\activate
```

### macOS 特定

#### Q: 安装时提示 "command not found: python3"

**A**:

```bash
# 使用 Homebrew 安装
brew install python@3.11

# 或从 python.org 下载安装包
```

#### Q: SSL 证书错误

**A**:

```bash
# 安装证书
/Applications/Python\ 3.11/Install\ Certificates.command
```

### Windows 特定

#### Q: "无法加载文件...执行策略"

**A**: 使用管理员权限运行 PowerShell：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Q: 中文显示乱码

**A**:

```cmd
# 设置 UTF-8 编码
chcp 65001

# 使用 Windows Terminal（推荐）
# 从 Microsoft Store 安装
```

#### Q: 路径中的反斜杠问题

**A**: 在 JSON 中使用双反斜杠或正斜杠：

```json
// 正确
"path": "C:\\Users\\Andrew\\Documents"
"path": "C:/Users/Andrew/Documents"

// 错误
"path": "C:\Users\Andrew\Documents"
```

### Linux 特定

#### Q: 没有 pip

**A**:

```bash
# Ubuntu/Debian
sudo apt install python3-pip

# Fedora
sudo dnf install python3-pip
```

#### Q: SQLite 版本太低

**A**:

```bash
# 升级 SQLite
# Ubuntu
sudo apt update && sudo apt upgrade sqlite3
```

---

## 自动化脚本

### macOS/Linux: 一键安装脚本

创建 `install.sh`：

```bash
#!/bin/bash

echo "🚀 Health Tracker 安装脚本"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装"
    exit 1
fi

echo "✓ Python 版本: $(python3 --version)"

# 创建虚拟环境
echo "📦 创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo "📥 安装依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 创建配置
if [ ! -f config/config.json ]; then
    echo "⚙️ 创建配置文件..."
    cp config/config.example.json config/config.json
    echo "⚠️ 请编辑 config/config.json 填写配置"
fi

echo "✅ 安装完成！"
echo ""
echo "下一步："
echo "1. 编辑 config/config.json"
echo "2. 运行: source venv/bin/activate"
echo "3. 运行: python cli.py --help"
```

使用：

```bash
chmod +x install.sh
./install.sh
```

### Windows: 一键安装脚本

创建 `install.bat`：

```batch
@echo off
echo 🚀 Health Tracker 安装脚本

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到 Python，请先安装
    pause
    exit /b 1
)

echo ✓ Python 已安装

REM 创建虚拟环境
echo 📦 创建虚拟环境...
python -m venv venv
call venv\Scripts\activate

REM 安装依赖
echo 📥 安装依赖...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM 创建配置
if not exist config\config.json (
    echo ⚙️ 创建配置文件...
    copy config\config.example.json config\config.json
    echo ⚠️ 请编辑 config\config.json 填写配置
)

echo.
echo ✅ 安装完成！
echo.
echo 下一步：
echo 1. 编辑 config\config.json
echo 2. 运行: venv\Scripts\activate
echo 3. 运行: python cli.py --help
echo.
pause
```

使用：双击 `install.bat`

---

## 快速参考

### 日常使用命令

```bash
# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 解析笔记
python cli.py parse --date today

# 查看统计
python cli.py stats

# 同步到云端
python cli.py sync

# 退出虚拟环境
deactivate
```

### 路径快速参考

| 平台 | Obsidian Vault 典型路径 |
|------|------------------------|
| macOS | `/Users/用户名/Documents/Obsidian/Vault名` |
| Windows | `C:\Users\用户名\Documents\Obsidian\Vault名` |
| Linux | `/home/用户名/Documents/Obsidian/Vault名` |

---

## 下一步

1. ✅ 完成安装
2. 📝 阅读 [SETUP.md](SETUP.md) 了解详细配置
3. 💡 查看 [EXAMPLES.md](EXAMPLES.md) 学习使用方法
4. ❓ 遇到问题查看 [FAQ.md](FAQ.md)

**祝你使用愉快！** 🎉

@echo off
REM Health Tracker 一键安装脚本 (Windows)

chcp 65001 >nul
echo.
echo 🚀 Health Tracker 安装脚本
echo ==========================
echo.

REM 检查 Python
echo 📌 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到 Python
    echo.
    echo 请先安装 Python 3.8+：
    echo   访问 https://www.python.org/downloads/
    echo   或从 Microsoft Store 安装 Python 3.11
    echo.
    echo ⚠️ 安装时请务必勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

python --version
echo ✓ Python 已安装
echo.

REM 创建虚拟环境
echo 📦 创建虚拟环境...
if exist venv (
    echo ⚠️ 虚拟环境已存在，跳过创建
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ❌ 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo ✓ 虚拟环境创建成功
)
echo.

REM 激活虚拟环境
echo 🔄 激活虚拟环境...
call venv\Scripts\activate
if errorlevel 1 (
    echo ❌ 激活虚拟环境失败
    echo.
    echo 如果遇到执行策略错误，请以管理员身份运行 PowerShell 并执行：
    echo Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
    echo.
    pause
    exit /b 1
)
echo ✓ 虚拟环境已激活
echo.

REM 升级 pip
echo ⬆️ 升级 pip...
python -m pip install --upgrade pip -q
echo ✓ pip 已升级
echo.

REM 安装依赖
echo 📥 安装项目依赖...
echo    (这可能需要几分钟...)
pip install -r requirements.txt -q

if errorlevel 1 (
    echo ⚠️ 使用国内镜像重试...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
)

echo ✓ 依赖安装成功
echo.

REM 创建配置文件
echo ⚙️ 配置项目...
if not exist config\config.json (
    copy config\config.example.json config\config.json >nul
    echo ✓ 配置文件已创建: config\config.json
    echo ⚠️ 请编辑此文件填写你的配置
) else (
    echo ⚠️ 配置文件已存在，跳过创建
)
echo.

REM 测试安装
echo 🧪 测试安装...
python cli.py --help >nul 2>&1
if errorlevel 1 (
    echo ❌ 安装测试失败
    pause
    exit /b 1
)
echo ✓ 安装测试通过
echo.

echo ✅ 安装完成！
echo ==========================
echo.
echo 📋 下一步：
echo.
echo 1️⃣ 编辑配置文件：
echo    notepad config\config.json
echo.
echo    需要填写：
echo    - Claude API Key (从 https://console.anthropic.com/ 获取)
echo    - Obsidian Vault 路径 (使用 \\ 或 / 作为分隔符)
echo.
echo    路径示例：
echo    "C:\\Users\\YourName\\Documents\\Obsidian\\MyVault"
echo    或
echo    "C:/Users/YourName/Documents/Obsidian/MyVault"
echo.
echo 2️⃣ 激活虚拟环境（每次使用前）：
echo    venv\Scripts\activate
echo.
echo 3️⃣ 开始使用：
echo    python cli.py parse --date today
echo    python cli.py stats
echo    python cli.py --help
echo.
echo 📚 查看文档：
echo    type INSTALLATION.md  - 安装指南
echo    type SETUP.md         - 配置说明
echo    type EXAMPLES.md      - 使用示例
echo.
echo 💡 提示：
echo    - 推荐使用 Windows Terminal 获得更好的体验
echo    - 从 Microsoft Store 安装
echo.
echo 🎉 祝使用愉快！
echo.
pause

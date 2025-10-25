# 快速开始指南

5分钟上手 Health Tracker！

## 🚀 一键安装

### macOS / Linux

```bash
# 1. 进入项目目录
cd health-tracker

# 2. 运行安装脚本
chmod +x install.sh
./install.sh

# 3. 编辑配置
nano config/config.json
# 填写 Claude API Key 和 Obsidian Vault 路径
```

### Windows

```cmd
# 1. 进入项目目录
cd health-tracker

# 2. 双击运行
install.bat

# 3. 编辑配置
notepad config\config.json
# 填写 Claude API Key 和 Obsidian Vault 路径
```

## 📝 最小配置

编辑 `config/config.json`，只需填写两项：

```json
{
  "claude_api_key": "sk-ant-你的API密钥",
  "obsidian_vault_path": "你的Obsidian笔记路径"
}
```

### 如何获取 Claude API Key

1. 访问：https://console.anthropic.com/
2. 注册/登录账号
3. 点击 "API Keys" → "Create Key"
4. 复制密钥（以 `sk-ant-` 开头）

### 如何找到 Obsidian Vault 路径

**macOS:**
```bash
# 在 Finder 中右键 vault 文件夹
# → "服务" → "新建位于文件夹位置的终端窗口"
# → 运行：
pwd
```

**Windows:**
```
1. 在文件资源管理器中打开 vault 文件夹
2. 点击地址栏
3. 复制完整路径
4. 在 JSON 中将 \ 替换为 \\
```

**Linux:**
```bash
# 进入 vault 目录后运行：
pwd
```

## 📖 第一次使用

### 1. 创建健康笔记

在 Obsidian 中创建今天的笔记（例如 `Health/2025-10-25.md`）：

```markdown
# 今天的健康

早上体重 68.5kg，感觉不错

昨晚睡了 7.5 小时，质量挺好的

下午跑步 5 公里，用了 30 分钟
```

### 2. 解析笔记

**macOS/Linux:**
```bash
# 激活环境
source venv/bin/activate

# 解析今天的笔记
python cli.py parse --date today

# 或使用快捷脚本
./run.sh parse --date today
```

**Windows:**
```cmd
# 激活环境
venv\Scripts\activate

# 解析今天的笔记
python cli.py parse --date today

# 或使用快捷脚本
run.bat parse --date today
```

### 3. 查看数据

```bash
# 查看今天的记录
python cli.py show --date today

# 查看统计
python cli.py stats

# 生成周报
python cli.py report --period week
```

## 💡 常用命令

```bash
# 解析笔记
python cli.py parse --date today
python cli.py parse --date 2025-10-25

# 查看数据
python cli.py show --date today
python cli.py stats --days 30

# 生成报告
python cli.py report --period week
python cli.py report --period month

# 智能问答
python cli.py chat "为什么我这周体重没变化？"

# 获取建议
python cli.py recommend --goal "减重5kg"

# 同步到云端（需要先配置 Google Sheets）
python cli.py sync --days 7
```

## 🎯 每日工作流

### 方法 1: 手动运行

```bash
# 早上：写今天的笔记
# 在 Obsidian 中记录昨晚睡眠、早上体重等

# 晚上：解析笔记
python cli.py parse --date today

# 查看统计
python cli.py stats
```

### 方法 2: 自动化

**macOS/Linux - 使用 cron:**

```bash
# 编辑 crontab
crontab -e

# 添加定时任务（每晚 11 点自动解析）
0 23 * * * cd /path/to/health-tracker && /path/to/health-tracker/venv/bin/python cli.py parse --date today
```

**Windows - 使用任务计划程序:**

1. 打开"任务计划程序"
2. 创建基本任务
3. 触发器：每天 23:00
4. 操作：启动程序
   - 程序：`C:\path\to\health-tracker\run.bat`
   - 参数：`parse --date today`

## 📱 移动端使用

### 记录数据

- 在手机上使用 Obsidian 手机版写笔记
- 可以拍照（体重秤、健身 APP 截图）并插入笔记
- Obsidian 会自动同步到电脑

### 查看数据

**方法 1: 同步到 Google Sheets**
```bash
# 在电脑上运行
python cli.py sync --all

# 然后在手机上打开 Google Sheets 查看
```

**方法 2: 使用 SSH**
```bash
# 如果你的电脑允许 SSH 访问
# 在手机上使用 Termius 等 SSH 客户端
ssh user@your-computer
cd health-tracker
source venv/bin/activate
python cli.py stats
```

## ⚙️ 进阶配置

### 配置 Google Sheets 云端同步

详见 [SETUP.md](SETUP.md#配置-google-sheets-可选)

简要步骤：
1. 创建 Google Cloud 项目
2. 启用 Sheets API
3. 创建服务账号
4. 下载凭证文件
5. 创建 Google Sheet 并分享给服务账号

### 自定义健康文件夹

```json
{
  "obsidian_health_folder": "Daily/Health"
}
```

### 使用不同的 Claude 模型

```json
{
  "claude_model": "claude-3-opus-20240229"
}
```

## 🆘 遇到问题？

### Python 找不到

```bash
# 尝试使用 python3
python3 cli.py --help

# 或创建别名
alias python=python3
```

### 虚拟环境激活失败

```bash
# macOS/Linux
chmod +x venv/bin/activate
source venv/bin/activate

# Windows - 如果遇到执行策略错误
# 以管理员身份运行 PowerShell：
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 找不到笔记

检查配置文件中的路径是否正确：

```bash
# macOS/Linux
ls -la "$(python -c "import json; print(json.load(open('config/config.json'))['obsidian_vault_path'])")"

# Windows
dir "配置中的路径"
```

### Claude API 调用失败

- 检查 API Key 是否正确
- 确认账户有余额
- 检查网络连接

### 更多问题

查看详细文档：
- [FAQ.md](FAQ.md) - 常见问题
- [INSTALLATION.md](INSTALLATION.md) - 安装问题
- [SETUP.md](SETUP.md) - 配置问题

## 📚 下一步

1. ✅ 完成基础配置
2. 📝 查看 [EXAMPLES.md](EXAMPLES.md) 学习更多用法
3. 🎨 探索高级功能：
   - 相关性分析
   - 智能问答
   - 个性化建议
4. ☁️ 配置 Google Sheets 云端同步
5. 🤖 设置自动化任务

## 🎉 开始你的健康追踪之旅！

记住：
- **随意记录**：不需要严格格式，用自然语言即可
- **坚持记录**：每天花2分钟记录，Claude 会帮你分析
- **定期回顾**：每周看看报告，了解自己的健康趋势
- **持续改进**：根据 Claude 的建议调整生活方式

健康是一场马拉松，不是短跑。让 AI 成为你的健康伙伴！💪

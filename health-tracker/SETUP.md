# 安装和配置指南

## 1. 环境要求

- Python 3.8+
- pip
- Obsidian (可选，用于编辑笔记)

## 2. 安装步骤

### 2.1 克隆仓库

```bash
git clone <your-repo-url>
cd health-tracker
```

### 2.2 安装依赖

```bash
pip install -r requirements.txt
```

### 2.3 配置系统

#### a. 创建配置文件

```bash
cp config/config.example.json config/config.json
```

#### b. 编辑配置文件

编辑 `config/config.json`，填写以下信息：

```json
{
  "claude_api_key": "your-claude-api-key",
  "obsidian_vault_path": "/path/to/your/obsidian/vault",
  "obsidian_health_folder": "Health",
  "database_path": "health_data.db",
  "claude_model": "claude-sonnet-5"
}
```

**获取 Claude API Key:**
1. 访问 https://console.anthropic.com/
2. 注册/登录账号
3. 在 API Keys 页面创建新的 API Key
4. 复制 API Key 到配置文件

#### c. 配置 Google Sheets (可选)

如果要使用云端同步功能：

1. **创建 Google Cloud 项目**
   - 访问 https://console.cloud.google.com/
   - 创建新项目

2. **启用 Google Sheets API**
   - 在项目中启用 "Google Sheets API" 和 "Google Drive API"

3. **创建服务账号**
   - 转到 "IAM & Admin" > "Service Accounts"
   - 创建服务账号
   - 创建密钥 (JSON 格式)
   - 下载密钥文件保存为 `config/google-credentials.json`

4. **创建 Google Sheet**
   - 在 Google Sheets 中创建新表格
   - 复制 URL 中的表格 ID (在 /d/ 和 /edit 之间的部分)
   - 将服务账号邮箱添加为表格的编辑者

5. **更新配置**
   ```json
   {
     ...
     "google_sheets_credentials": "config/google-credentials.json",
     "google_sheet_id": "your-google-sheet-id"
   }
   ```

## 3. 设置 Obsidian Vault

### 3.1 创建健康文件夹

在你的 Obsidian vault 中创建一个文件夹用于存放健康日志，例如 `Health` 或 `Daily/Health`。

### 3.2 笔记命名格式

系统支持以下命名格式：
- `YYYY-MM-DD.md` (推荐)
- `YYYY-MM-DD 星期X.md`
- 在子文件夹中：`Daily/YYYY-MM-DD.md`

### 3.3 笔记模板

参考 `example_note.md` 创建你的笔记。你可以使用自然语言，Claude 会智能提取数据：

```markdown
---
tags: [health, daily]
---

# 2025-10-25 健康日志

今天早上68.5kg，感觉不错。
昨晚睡了7.5小时，质量还可以。
晚上跑步5公里，30分钟。

午餐吃了鸡胸肉沙拉，健康！
```

也支持附带图片（体重秤截图、健身 APP 截图等）：

```markdown
![[weight_scale.png]]
![健身数据](fitness_app_screenshot.jpg)
```

## 4. 测试安装

### 4.1 测试基础功能

```bash
# 运行测试
cd health-tracker
python tests/test_parser.py
```

### 4.2 测试 CLI

```bash
# 查看帮助
python cli.py --help

# 解析今天的笔记（需要先创建笔记）
python cli.py parse --date today

# 查看统计
python cli.py stats
```

## 5. 日常使用流程

### 5.1 每日记录

1. 在 Obsidian 中写今天的健康日志
2. 可以用自然语言描述，可以添加截图
3. 运行命令解析：
   ```bash
   python cli.py parse --date today
   ```

### 5.2 查看数据

```bash
# 查看今天的数据
python cli.py show --date today

# 查看统计
python cli.py stats --days 30

# 生成周报
python cli.py report --period week
```

### 5.3 分析和建议

```bash
# 提问
python cli.py chat "为什么我这周体重没变化？"

# 获取建议
python cli.py recommend --goal "减重3kg"

# 分析相关性
python cli.py correlations --days 30
```

### 5.4 云端同步

```bash
# 同步到 Google Sheets
python cli.py sync --days 7

# 同步所有未同步的数据
python cli.py sync --all
```

## 6. 自动化 (可选)

### 6.1 使用 cron 定时解析

在 Linux/Mac 上，可以设置 cron 任务自动解析笔记：

```bash
# 编辑 crontab
crontab -e

# 添加定时任务 (每天晚上 11 点解析今天的笔记)
0 23 * * * cd /path/to/health-tracker && python cli.py parse --date today

# 每周日晚上生成周报
0 20 * * 0 cd /path/to/health-tracker && python cli.py report --period week
```

### 6.2 使用 Python 脚本定时同步

创建 `sync_daemon.py`:

```python
import schedule
import time
import subprocess

def sync_to_sheets():
    subprocess.run(['python', 'cli.py', 'sync', '--all'])
    print("Synced to Google Sheets")

# 每天晚上 11:30 同步
schedule.every().day.at("23:30").do(sync_to_sheets)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## 7. 故障排除

### 问题：Claude API 调用失败

- 检查 API Key 是否正确
- 检查网络连接
- 确认 API 配额是否充足

### 问题：找不到 Obsidian 笔记

- 检查 `obsidian_vault_path` 是否正确
- 检查笔记文件名格式是否正确
- 确认 `obsidian_health_folder` 配置正确

### 问题：Google Sheets 同步失败

- 检查服务账号凭证文件是否存在
- 确认服务账号已添加为表格编辑者
- 检查 Google Sheets API 是否已启用

### 问题：数据库错误

- 删除 `health_data.db` 重新初始化
- 检查磁盘空间

## 8. 进阶使用

### 8.1 批量处理历史笔记

```bash
# 创建批处理脚本
for i in {1..30}; do
  date=$(date -d "$i days ago" +%Y-%m-%d)
  python cli.py parse --date $date
done
```

### 8.2 导出数据

```python
# 使用 Python 直接访问数据库
from storage import HealthDatabase

db = HealthDatabase('health_data.db')
records = db.get_recent_records(days=365)

# 导出为 JSON
import json
with open('health_data_export.json', 'w') as f:
    json.dump(records, f, ensure_ascii=False, indent=2)
```

### 8.3 自定义分析

可以直接使用 Python 脚本调用分析模块：

```python
from extractors import HealthDataExtractor
from storage import HealthDatabase
from analytics import HealthAnalyzer

extractor = HealthDataExtractor('your-api-key')
db = HealthDatabase('health_data.db')
analyzer = HealthAnalyzer(extractor, db)

# 自定义分析
answer = analyzer.answer_question("分析我的睡眠和运动的关系")
print(answer)
```

## 9. 数据隐私

- **本地优先**: 所有数据首先存储在本地 SQLite 数据库
- **API 安全**: Claude API 调用通过 HTTPS 加密
- **Google Sheets**: 数据通过服务账号同步，可选功能
- **敏感信息**: 配置文件已添加到 .gitignore，不会被提交到 git

## 10. 获取帮助

如有问题，可以：
- 查看 README.md
- 查看代码注释
- 提交 Issue
- 运行 `python cli.py --help` 查看命令帮助

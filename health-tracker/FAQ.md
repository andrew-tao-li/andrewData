# 常见问题 (FAQ)

## 基础问题

### Q1: 这个系统需要花钱吗？

**A**: 主要成本是 Claude API 的使用费用。

- **Claude API**: 按使用量付费
  - Claude 3.5 Sonnet: 输入 $3/MTok，输出 $15/MTok
  - 日常使用估算：每天解析1-2条笔记，约 $0.05-0.10
  - 每月大约：$1.5-3
- **Google Sheets**: 免费（使用 Google Drive 配额）
- **其他组件**: 全部开源免费

### Q2: 我的数据安全吗？

**A**: 是的，系统设计时充分考虑了隐私：

1. **本地优先**: 数据首先存储在本地 SQLite
2. **加密传输**: Claude API 使用 HTTPS
3. **可选云端**: Google Sheets 同步是可选功能
4. **无第三方追踪**: 没有统计或追踪代码
5. **开源透明**: 所有代码可审查

### Q3: 必须使用 Obsidian 吗？

**A**: 不是必须的，但推荐使用。

- Obsidian 只是方便的编辑工具
- 你可以用任何文本编辑器创建 Markdown 文件
- 只要文件格式和命名符合要求即可
- 甚至可以修改代码，支持其他来源（如纯文本文件）

### Q4: 支持中文吗？

**A**: 完全支持！

- Claude 对中文的理解非常好
- 可以用中文自然语言记录
- 所有输出都支持中文
- CLI 界面有中文提示

### Q5: 可以在手机上使用吗？

**A**: 间接支持：

- **记录**: 在手机上用 Obsidian 手机版记录
- **查看**: 通过 Google Sheets 在手机上查看数据
- **CLI**: 需要在电脑上运行，或使用 Termux 等工具

## 技术问题

### Q6: 解析笔记时遇到"未找到笔记"错误

**可能原因**：
1. 笔记文件不存在
2. 文件命名格式不对
3. 配置的路径不正确

**解决方法**：
```bash
# 检查配置
cat config/config.json

# 验证路径
ls -la /path/to/your/obsidian/vault/Health/

# 检查文件名（应该是 YYYY-MM-DD.md 格式）
ls -la /path/to/your/obsidian/vault/Health/2025-10-25.md
```

### Q7: Claude API 调用失败

**可能原因**：
1. API Key 不正确
2. 网络问题
3. API 配额用完
4. 请求格式错误

**解决方法**：
```bash
# 测试 API Key
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $CLAUDE_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-5-sonnet-20241022","max_tokens":1024,"messages":[{"role":"user","content":"Hello"}]}'

# 检查配置
python -c "import json; print(json.load(open('config/config.json'))['claude_api_key'])"

# 查看详细错误
python cli.py parse --date today --verbose
```

### Q8: Google Sheets 同步失败

**常见问题**：

1. **认证失败**
   - 检查 `google-credentials.json` 是否存在
   - 确认服务账号有权限

2. **找不到表格**
   - 检查 Sheet ID 是否正确
   - 确认服务账号邮箱已添加为编辑者

3. **API 未启用**
   - 在 Google Cloud Console 启用 Sheets API
   - 启用 Drive API

**解决步骤**：
```bash
# 验证凭证文件
ls -la config/google-credentials.json

# 测试连接
python -c "
import gspread
from google.oauth2.service_account import Credentials

creds = Credentials.from_service_account_file(
    'config/google-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
client = gspread.authorize(creds)
print('连接成功！')
"
```

### Q9: 图片识别不准确

**优化建议**：

1. **图片质量**
   - 确保图片清晰
   - 光线充足
   - 避免反光

2. **图片内容**
   - 截图包含完整信息
   - 数字清晰可见
   - 避免遮挡

3. **提供上下文**
   - 在文本中补充说明
   - 例如："这是今天的体重秤截图"

### Q10: 数据提取不完整

**如果 Claude 没有提取某些数据**：

1. **使用更明确的描述**
   ```markdown
   ❌ "睡得还行"
   ✅ "睡了7.5小时，质量8分"
   ```

2. **检查原始数据**
   ```bash
   # 查看 Claude 提取的原始 JSON
   python -c "
   from storage import HealthDatabase
   db = HealthDatabase('health_data.db')
   record = db.get_record_by_date('2025-10-25')
   import json
   print(json.dumps(record, ensure_ascii=False, indent=2))
   "
   ```

3. **手动补充**
   - 可以直接编辑数据库
   - 或者重新解析（使用 `--force`）

## 使用问题

### Q11: 如何批量导入历史数据？

**方法 1: 批量解析**
```bash
# 处理过去30天
for i in {1..30}; do
  python cli.py parse --date $(date -d "$i days ago" +%Y-%m-%d)
done
```

**方法 2: 直接导入**
```python
# 创建导入脚本
from storage import HealthDatabase
import json

db = HealthDatabase('health_data.db')

# 准备数据
historical_data = [
    {
        "date": "2025-09-01",
        "weight": 70.5,
        "sleep_duration": 7.0,
        # ...
    },
    # 更多记录...
]

for data in historical_data:
    db.save_health_record(data)
```

### Q12: 如何备份数据？

**方法 1: 备份数据库文件**
```bash
# 复制数据库
cp health_data.db health_data_backup_$(date +%Y%m%d).db

# 定期自动备份
echo "0 2 * * * cp /path/to/health_data.db /path/to/backup/health_data_\$(date +\%Y\%m\%d).db" | crontab -
```

**方法 2: 导出为 JSON**
```bash
python -c "
from storage import HealthDatabase
import json

db = HealthDatabase('health_data.db')
records = db.get_recent_records(days=365)

with open('health_data_export.json', 'w') as f:
    json.dump(records, f, ensure_ascii=False, indent=2)
"
```

**方法 3: Google Sheets 作为云端备份**
```bash
python cli.py sync --all
```

### Q13: 可以多人使用吗？

**当前版本不直接支持多用户，但可以通过以下方式实现**：

**方法 1: 独立环境**
```bash
# 为每个用户创建独立配置
mkdir -p ~/health-tracker-user1
cp -r health-tracker/* ~/health-tracker-user1/
cd ~/health-tracker-user1
# 编辑 config.json，使用不同的数据库和 Sheet
```

**方法 2: 使用不同数据库**
```json
{
  "database_path": "health_data_john.db",
  "google_sheet_id": "john-sheet-id"
}
```

### Q14: 如何删除错误的记录？

**方法 1: 使用 SQLite**
```bash
sqlite3 health_data.db
> DELETE FROM health_records WHERE date = '2025-10-25';
> DELETE FROM exercises WHERE date = '2025-10-25';
> DELETE FROM meals WHERE date = '2025-10-25';
> .quit
```

**方法 2: 重新解析**
```bash
# 修改 Obsidian 笔记后重新解析
python cli.py parse --date 2025-10-25 --force
```

### Q15: 如何自定义分析？

**使用 Python 脚本**：

```python
from extractors import HealthDataExtractor
from storage import HealthDatabase
import json

# 加载配置
with open('config/config.json') as f:
    config = json.load(f)

extractor = HealthDataExtractor(config['claude_api_key'])
db = HealthDatabase(config['database_path'])

# 获取数据
records = db.get_recent_records(days=30)

# 自定义提问
custom_question = """
请分析我的数据，重点关注：
1. 周末和工作日的运动差异
2. 季节对睡眠的影响
3. 特定食物对体重的影响
"""

answer = extractor.analyze_trends(records, custom_question)
print(answer)
```

## 高级问题

### Q16: 如何添加新的健康指标？

**步骤**：

1. 修改数据库结构（`storage/sqlite_storage.py`）
2. 更新提取提示词（`extractors/health_extractor.py`）
3. 更新显示函数（`cli.py`）

**示例：添加"心情"指标**：
```python
# 在 sqlite_storage.py 中添加列
cursor.execute("""
    ALTER TABLE health_records ADD COLUMN mood TEXT
""")

# 在 health_extractor.py 的提示词中添加
"""
- mood: 心情（1-10分或描述）
"""
```

### Q17: 如何集成其他健康设备？

**可以通过插件方式集成**：

```python
# 创建 importers/fitbit_importer.py
class FitbitImporter:
    def import_data(self, date):
        # 从 Fitbit API 获取数据
        fitbit_data = self.fetch_from_fitbit(date)

        # 转换为标准格式
        health_data = {
            'date': date,
            'weight': fitbit_data['weight'],
            'steps': fitbit_data['steps'],
            'heart_rate': fitbit_data['heart_rate'],
            # ...
        }

        return health_data

# 使用
importer = FitbitImporter(token='your-token')
data = importer.import_data('2025-10-25')
db.save_health_record(data)
```

### Q18: 如何贡献代码？

欢迎贡献！

1. Fork 仓库
2. 创建功能分支
3. 提交代码
4. 发起 Pull Request

**建议的改进方向**：
- 新的数据源支持（Apple Health、小米健康等）
- 数据可视化增强
- 移动端应用
- Web 界面
- 更多语言支持

### Q19: 性能优化建议

**如果数据量很大（>1000条记录）**：

1. **添加索引**
```sql
CREATE INDEX idx_date ON health_records(date);
CREATE INDEX idx_created_at ON health_records(created_at);
```

2. **分页查询**
```python
def get_records_paginated(db, page=1, per_page=50):
    offset = (page - 1) * per_page
    # 修改查询添加 LIMIT 和 OFFSET
```

3. **缓存分析结果**
```python
# 分析结果已保存在 insights 表中
# 可以直接读取而不是重新分析
```

### Q20: 如何迁移到新电脑？

**完整迁移步骤**：

```bash
# 在旧电脑上
cd health-tracker
tar -czf health-tracker-backup.tar.gz \
  config/config.json \
  config/google-credentials.json \
  health_data.db

# 传输到新电脑
scp health-tracker-backup.tar.gz user@newcomputer:~

# 在新电脑上
git clone <repo-url>
cd health-tracker
tar -xzf ~/health-tracker-backup.tar.gz

# 安装依赖
pip install -r requirements.txt

# 测试
python cli.py stats
```

## 更多帮助

如果这里没有解决你的问题：

1. 查看代码注释
2. 阅读 `SETUP.md` 和 `EXAMPLES.md`
3. 提交 Issue 到 GitHub
4. 查看 Claude API 文档：https://docs.anthropic.com/

## 故障排除清单

遇到问题时，按此顺序检查：

- [ ] Python 版本 >= 3.8
- [ ] 所有依赖已安装 (`pip install -r requirements.txt`)
- [ ] 配置文件存在且格式正确
- [ ] Claude API Key 有效
- [ ] Obsidian vault 路径正确
- [ ] 笔记文件命名符合格式
- [ ] 网络连接正常
- [ ] 磁盘空间充足

如果以上都检查过，查看详细错误日志并搜索相关错误信息。

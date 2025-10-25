# 本地数据库与 Google Sheets 同步机制详解

## 📊 整体架构

### 数据流向图

```
┌─────────────────┐
│  Obsidian 笔记  │  (你的原始记录)
└────────┬────────┘
         │ parse 命令
         ↓
┌─────────────────┐
│   Claude AI     │  (提取结构化数据)
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ 本地 SQLite DB  │  ← 主要数据源 (离线可用)
└────────┬────────┘
         │ sync 命令
         ↓
┌─────────────────┐
│ Google Sheets   │  ← 云端备份 (跨设备访问)
└─────────────────┘
```

## 🎯 核心概念

### 1. 本地 SQLite 数据库（主数据源）

**位置**: `health_data.db` (项目目录下)

**作用**:
- ✅ **主要数据存储**: 所有解析的健康数据首先保存这里
- ✅ **快速查询**: 本地查询，毫秒级响应
- ✅ **离线工作**: 不需要网络也能查看数据
- ✅ **完整功能**: 支持复杂的统计和分析
- ✅ **数据安全**: 完全在你的电脑上

**数据表结构**:
```sql
health_records  -- 主健康数据表
├── date (日期)
├── weight (体重)
├── sleep_duration (睡眠)
├── overall_feeling (整体感受)
└── ...

exercises  -- 运动记录表
├── date
├── type (运动类型)
├── duration (时长)
└── ...

meals  -- 饮食记录表
├── date
├── meal_type (餐次)
├── description
└── ...

insights  -- Claude分析记录表
├── analysis (分析内容)
├── created_at
└── ...
```

### 2. Google Sheets（云端备份）

**位置**: 你的 Google Drive

**作用**:
- ☁️ **云端备份**: 防止本地数据丢失
- 📱 **跨设备访问**: 在手机、平板上查看
- 📊 **可视化**: 可以创建图表、透视表
- 🔗 **分享**: 可以分享给医生、教练等
- 📈 **自定义分析**: 使用 Google Sheets 的强大功能

**工作表结构**:
```
你的 Google Sheet
├── Health Data (主健康数据)
├── Exercises (运动明细)
├── Meals (饮食明细)
└── Statistics (统计数据)
```

## 🔄 同步机制详解

### 单向同步 (本地 → 云端)

**重要**: 同步是**单向**的，从本地到 Google Sheets

```
本地数据库 ─────同步────→ Google Sheets
    ↑                         ↓
    │                    只能查看
    │                    不要手动修改
  所有修改
  都在这里
```

### 为什么是单向？

1. **本地是真实数据源**
   - Claude 解析的结果直接保存到 SQLite
   - SQLite 支持复杂的数据类型和关系

2. **Google Sheets 是展示层**
   - 方便查看和分享
   - 创建自定义图表
   - 跨设备访问

3. **避免冲突**
   - 如果双向同步，容易产生数据冲突
   - 单向同步保证数据一致性

## 📝 实际工作流程

### 场景 1: 日常记录和查看

```bash
# 第 1 步: 在 Obsidian 中写今天的健康笔记
# 文件: vault/Health/2025-10-25.md
---
今天体重 68.5kg，睡了 7.5 小时
下午跑步 5 公里
---

# 第 2 步: 解析笔记到本地数据库
python cli.py parse --date today
# ✓ 数据保存到 health_data.db

# 第 3 步: 查看本地数据（离线也可以）
python cli.py show --date today
python cli.py stats --days 30

# 第 4 步: 同步到云端（可选，有网络时）
python cli.py sync --days 7
# ✓ 数据上传到 Google Sheets

# 第 5 步: 在手机上打开 Google Sheets 查看
# 打开浏览器: https://docs.google.com/spreadsheets/d/你的ID
```

### 场景 2: 出差在外（离线使用）

```bash
# 情况: 没有网络

# ✅ 可以做的:
python cli.py show --date today     # 查看本地数据
python cli.py stats                 # 查看统计
python cli.py report --period week  # 生成报告

# ❌ 不能做的:
python cli.py sync  # 同步需要网络

# 回到有网络的地方后:
python cli.py sync --all  # 同步所有未同步的数据
```

### 场景 3: 手机查看数据

```
1. 在电脑上: python cli.py sync
2. 在手机上: 打开 Google Sheets APP
3. 查看最新的健康数据
4. 可以创建自定义图表
```

## 🔧 同步命令详解

### `python cli.py sync`

**作用**: 将本地数据同步到 Google Sheets

**选项**:
```bash
# 同步最近 7 天
python cli.py sync --days 7

# 同步所有未同步的数据
python cli.py sync --all
```

**内部流程**:

```python
# 1. 从 SQLite 读取数据
records = db.get_unsynced_records()  # 或最近N天

# 2. 连接到 Google Sheets
sheets_sync = GoogleSheetsSync(credentials, sheet_id)

# 3. 同步主数据
for record in records:
    # 检查 Google Sheets 中是否已存在该日期
    if date exists:
        # 更新该行
        update_row(record)
    else:
        # 添加新行
        append_row(record)

# 4. 同步运动数据
# 删除该日期的旧运动记录，添加新的
delete_exercises_for_date(date)
append_new_exercises(exercises)

# 5. 同步饮食数据
# 同上

# 6. 更新统计数据
update_statistics_sheet()

# 7. 标记为已同步
db.mark_as_synced(date)
```

## 🎨 Google Sheets 的结构

### 工作表 1: Health Data

| Date | Weight(kg) | Body Fat(%) | Sleep(h) | Steps | ... | Last Updated |
|------|-----------|-------------|----------|-------|-----|--------------|
| 2025-10-25 | 68.5 | 23 | 7.5 | 8500 | ... | 2025-10-25 23:00 |
| 2025-10-24 | 68.8 | 23.2 | 7.0 | 7200 | ... | 2025-10-24 23:05 |

**自动功能**:
- 按日期排序
- 重复日期会自动更新（不会重复添加）
- 显示最后更新时间

### 工作表 2: Exercises

| Date | Type | Duration(min) | Distance(km) | Calories |
|------|------|--------------|--------------|----------|
| 2025-10-25 | 跑步 | 30 | 5 | 350 |
| 2025-10-25 | 力量训练 | 40 | - | 200 |

### 工作表 3: Meals

| Date | Meal Type | Description | Calories |
|------|-----------|-------------|----------|
| 2025-10-25 | 早餐 | 燕麦+牛奶 | 350 |
| 2025-10-25 | 午餐 | 鸡胸肉沙拉 | 500 |

### 工作表 4: Statistics

| Metric | Value | Period | Last Updated |
|--------|-------|--------|--------------|
| Current Weight | 68.5 kg | 30 days | 2025-10-25 |
| Average Sleep | 7.3 hours | 30 days | 2025-10-25 |
| Total Exercise | 840 min | 30 days | 2025-10-25 |

## 💡 为什么需要两者？

### 为什么不只用 Google Sheets？

**问题**:
- ❌ 需要网络才能使用
- ❌ 查询速度慢
- ❌ 不支持复杂的数据关系
- ❌ 不便于 Python 代码操作
- ❌ 每次 API 调用都有成本

**SQLite 的优势**:
- ✅ 离线可用
- ✅ 查询速度极快
- ✅ 支持复杂的 SQL 查询
- ✅ 免费无限制
- ✅ 数据完全在你控制之下

### 为什么不只用 SQLite？

**问题**:
- ❌ 只能在安装系统的电脑上访问
- ❌ 手机上不方便查看
- ❌ 不便于分享
- ❌ 没有可视化界面
- ❌ 数据只在一台电脑上，有丢失风险

**Google Sheets 的优势**:
- ✅ 随时随地访问
- ✅ 手机友好
- ✅ 自动云端备份
- ✅ 可以创建图表
- ✅ 可以分享给他人

## 🔐 数据安全性

### 三层保护

```
1. 本地数据库 (health_data.db)
   └─ 在你的电脑上，完全私密

2. Google Sheets
   └─ Google 云端加密存储
   └─ 只有你的 Google 账号可以访问

3. Obsidian 笔记 (原始数据)
   └─ 可以设置 Obsidian 的云同步
   └─ 或手动备份到多个位置
```

### 备份策略

```bash
# 本地数据库备份
cp health_data.db health_data_backup_$(date +%Y%m%d).db

# 导出为 JSON
python -c "
from storage import HealthDatabase
import json
db = HealthDatabase('health_data.db')
records = db.get_recent_records(days=365)
with open('backup.json', 'w') as f:
    json.dump(records, f, ensure_ascii=False, indent=2)
"

# Google Sheets 自动备份
python cli.py sync --all
```

## 🎯 使用建议

### 推荐工作流

**每天晚上**:
```bash
# 1. 写 Obsidian 笔记 (2分钟)
# 2. 解析到本地数据库 (自动或手动)
python cli.py parse --date today
```

**每周日晚上**:
```bash
# 1. 生成周报
python cli.py report --period week

# 2. 同步到云端
python cli.py sync --days 7

# 3. 在手机上打开 Google Sheets，查看数据和图表
```

**外出时**:
```bash
# 在手机上打开 Google Sheets
# 查看最新的健康数据
# 无需电脑
```

## 📱 在 Google Sheets 中自定义分析

### 创建图表

在 Google Sheets 中，你可以：

1. **体重趋势图**:
   - 选择 Date 和 Weight 列
   - 插入 → 图表 → 折线图

2. **睡眠质量热图**:
   - 使用条件格式
   - 根据睡眠时长设置颜色

3. **运动统计**:
   - 使用数据透视表
   - 按运动类型汇总

### 使用公式

```
// 计算 BMI
=B2/(1.75^2)  // B2是体重列，1.75是身高

// 平均睡眠
=AVERAGE(D2:D30)  // D列是睡眠时长

// 本周运动总时长
=SUMIF(A:A, ">="&TODAY()-7, Exercises!C:C)
```

## 🔄 同步状态追踪

### 数据库中的同步字段

```sql
health_records 表:
├── synced_to_sheets  -- 是否已同步 (TRUE/FALSE)
└── last_sync_at      -- 最后同步时间
```

### 查看同步状态

```bash
# 查看未同步的记录
python -c "
from storage import HealthDatabase
db = HealthDatabase('health_data.db')
unsynced = db.get_unsynced_records()
print(f'有 {len(unsynced)} 条记录未同步')
for record in unsynced:
    print(f'  - {record[\"date\"]}')
"
```

## ⚠️ 注意事项

### 1. 不要在 Google Sheets 中手动修改数据

**为什么？**
- 下次同步时会被覆盖
- 本地数据库是真实数据源

**如果想修改数据**:
```bash
# 方法 1: 修改 Obsidian 笔记，重新解析
python cli.py parse --date 2025-10-25 --force

# 方法 2: 直接修改 SQLite 数据库
sqlite3 health_data.db
> UPDATE health_records SET weight=68.0 WHERE date='2025-10-25';

# 方法 3: 然后重新同步
python cli.py sync --days 1
```

### 2. Google Sheets 仅用于查看和分析

**正确使用**:
- ✅ 查看数据
- ✅ 创建图表
- ✅ 导出报告
- ✅ 分享给他人

**不要**:
- ❌ 在 Sheets 中添加新数据
- ❌ 修改现有数据
- ❌ 删除行
- ❌ 作为主数据源

### 3. 同步频率建议

```bash
# 推荐: 每周同步一次
python cli.py sync --days 7

# 或: 有新数据时同步
python cli.py sync --all

# 不推荐: 频繁同步（浪费 API 配额）
# 每次只有一条新数据时就同步
```

## 🎉 总结

### 数据流向

```
你写笔记 → Claude解析 → 本地SQLite → 云端Sheets
   ↑                         ↓              ↓
 原始记录              主数据源        备份+查看
```

### 核心理念

**本地优先，云端备份**

- 🏠 **本地 SQLite**: 主数据源，快速、离线、功能强大
- ☁️ **Google Sheets**: 备份副本，跨设备、可视化、分享

### 两者关系

```
SQLite = 你的主要工作空间（读写频繁）
Google Sheets = 展示和备份（只读，偶尔同步）
```

希望这样解释清楚了！还有什么不明白的地方吗？😊


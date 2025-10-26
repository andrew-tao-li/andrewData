# CSV数据导入指南

将你的历史健康数据（200+行）一键导入到系统中。

## 快速开始

### 1. 预览模式（推荐先运行）

先用预览模式查看数据是否正确解析：

```bash
python import_csv.py your_health_data.csv --dry-run
```

这会显示：
- ✓ 清理了哪些空列
- ✓ 合并后有多少条记录
- ✓ 前3条记录的预览

### 2. 正式导入

确认预览无误后，执行导入：

```bash
python import_csv.py your_health_data.csv
```

默认行为：
- ✓ 自动清理空列和Unnamed列
- ✓ 按日期合并同一天的多行数据
- ✓ 跳过已存在的日期（不覆盖）
- ✓ 自动转换时间格式（7:16 → 7.27小时）

### 3. 更新模式

如果想更新已存在的记录（而不是跳过）：

```bash
python import_csv.py your_health_data.csv --update
```

## 支持的数据类型

### 晨测数据（一天一行）
自动识别并导入：
- ✓ 体重、肌肉量、基础代谢
- ✓ 睡眠时长、深睡、REM睡眠
- ✓ 静息心率、HRV
- ✓ 内脏脂肪等级
- ✓ 疼痛评分、晨僵时间、疼痛部位
- ✓ 排尿次数

### 运动数据（一天可能多行）
自动合并成 `exercises` JSON列表：
- ✓ 运动项目（Z2跑步、练腿等）
- ✓ 运动时长、距离
- ✓ 平均心率、最大心率
- ✓ 平均配速、训练负荷

### 饮食数据（一天可能多行）
自动合并成 `meals` JSON列表：
- ✓ 食物名称（从"类别"列）
- ✓ 热量
- ✓ 数量

## 字段映射

CSV列名会自动映射到数据库字段：

| CSV列名 | 数据库字段 | 说明 |
|---------|-----------|------|
| 体重(kg) | weight | 直接导入 |
| 肌肉(kg) | muscle_mass | 直接导入 |
| 基代(kcal) | basal_metabolism | 直接导入 |
| 睡眠(h:m) | sleep_duration | **转换为小时**（7:16 → 7.27） |
| 深睡(h:m) | deep_sleep_duration | **转换为小时** |
| REM(h:m) | rem_sleep_duration | **转换为小时** |
| 静息HR | resting_heart_rate | 直接导入 |
| HRV | hrv | 直接导入 |
| 排尿(次) | urination_count | 直接导入 |
| 内脏脂肪等级 | visceral_fat_level | 直接导入 |
| 离心提踵-疼痛评分(0-10) | pain_score | 直接导入 |
| 晨僵持续时间(分钟) | morning_stiffness_duration | 直接导入 |
| 最疼部位 | pain_location | 直接导入 |
| 备注 | health_notes | 合并多个备注 |

## 数据清理

导入工具会自动：

1. **删除空列**：完全没有数据的列
2. **删除Unnamed列**：`Unnamed: 9`, `Unnamed: 10` 等
3. **删除重复列**：`HRV基线偏差(ms)__dup1` 等

## 数据合并逻辑

### 一天多行 → 合并为一行

**示例**：2025-10-22 有3行数据

```csv
2025-10-22,,,,,,,08:00:00,87.5,37.9,1813,7:16,1:10,1:42,49,53,1,8,2,1,跟腱,...
2025-10-22,,,,今日 Z2 跑,,...  （运动行）
2025-10-22,摄入,花生,140,1.0,,,...  （饮食行）
```

**合并后**：

```json
{
  "date": "2025-10-22",
  "weight": 87.5,
  "muscle_mass": 37.9,
  "sleep_duration": 7.27,  // 7:16 转换
  "hrv": 53,
  "exercises": [
    {
      "type": "Z2跑步",
      "duration": 30.1,  // 分钟
      "avg_heart_rate": 129
    }
  ],
  "meals": [
    {
      "description": "花生",
      "calories": 140,
      "quantity": 1.0
    }
  ]
}
```

## 时间格式转换

支持多种时间格式：

| 输入格式 | 含义 | 转换结果 |
|---------|------|---------|
| `7:16` | 7小时16分钟 | 7.27 小时 |
| `1:30` | 1小时30分钟 | 1.5 小时 |
| `0:30:07` | 0小时30分7秒 | 0.502 小时 |
| `30:07` | 30分钟7秒 | 0.502 小时 |

## 冲突处理

### 默认模式（跳过）

```bash
python import_csv.py data.csv
```

- 如果日期已存在：**跳过**
- 输出：`⊙ 跳过: 15 条 (已存在)`

### 更新模式

```bash
python import_csv.py data.csv --update
```

- 如果日期已存在：**更新**（覆盖旧数据）
- 输出：`✓ 更新: 15 条`

## 验证导入结果

导入后，验证数据：

```bash
# 查看最近7天数据
python cli.py show --days 7

# 查看特定日期
python cli.py show --date 2025-02-26

# 查询数据库
sqlite3 data/health.db "SELECT date, weight, hrv, exercises FROM health_records ORDER BY date DESC LIMIT 5"
```

## 常见问题

### Q: 我的CSV有额外的列怎么办？

A: 没关系！导入工具只提取已知的健康字段，其他列会被忽略。

### Q: 一天有多次晨测怎么办？

A: 自动取第一个非空值。建议CSV中一天只保留一行晨测数据。

### Q: 运动数据太多，能否限制？

A: 所有运动记录都会保存到 `exercises` JSON列表中，AI分析时会自动处理。

### Q: 导入后发现数据错误怎么办？

A: 两种方法：
1. 修正CSV后重新导入（使用 `--update` 覆盖）
2. 或者手动编辑：`python cli.py edit --date 2025-10-22`

### Q: 如何查看哪些日期已经存在？

```bash
sqlite3 data/health.db "SELECT date FROM health_records ORDER BY date"
```

## 完整示例

假设你的CSV文件是 `health_2025.csv`：

```bash
# 步骤1: 预览数据（确保解析正确）
python import_csv.py health_2025.csv --dry-run

# 步骤2: 正式导入
python import_csv.py health_2025.csv

# 步骤3: 验证导入
python cli.py show --days 30

# 步骤4: 让AI分析历史趋势
python cli.py chat --days 90
```

## 高级用法

### 指定数据库路径

```bash
python import_csv.py data.csv --db /path/to/custom.db
```

### 导入并立即分析

```bash
python import_csv.py health_2025.csv && \
python cli.py chat "分析我3个月的体重和HRV趋势" --days 90
```

## 注意事项

⚠️ **备份数据**：导入前建议备份数据库
```bash
cp data/health.db data/health.db.backup
```

⚠️ **CSV编码**：确保CSV文件是UTF-8编码

⚠️ **日期格式**：确保日期列格式为 `YYYY-MM-DD`

⚠️ **数值字段**：确保数值字段不含非数字字符（除了时间格式的冒号）

---

需要帮助？请查看 [README.md](README.md) 或提交 issue。

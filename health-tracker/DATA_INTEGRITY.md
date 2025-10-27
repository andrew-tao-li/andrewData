# 数据唯一性保证文档

## 📋 概述

健康追踪系统在三个层面保证数据唯一性，确保不会产生重复记录：

1. **数据库Schema层** - UNIQUE约束
2. **应用程序层** - UPSERT逻辑
3. **批处理层** - 批次内去重

---

## 🔒 第一层：数据库Schema约束

### SQLite数据库

```sql
CREATE TABLE health_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,  -- ← UNIQUE约束，确保日期唯一
    ...
)
```

**保证：**
- ✅ 数据库级别阻止同一日期插入多次
- ✅ 如果尝试插入重复日期会报错（被应用层捕获）

### Google Sheets

虽然Google Sheets本身不支持UNIQUE约束，但通过应用层逻辑保证唯一性。

---

## 🔧 第二层：应用程序UPSERT逻辑

### 1. 本地数据库保存 (`storage/sqlite_storage.py`)

```python
def save_health_record(self, data: Dict[str, Any]) -> bool:
    # 1. 检查记录是否存在
    cursor.execute("SELECT id FROM health_records WHERE date = ?", (date,))
    existing = cursor.fetchone()

    if existing:
        # 2a. 更新现有记录（UPDATE）
        cursor.execute("""
            UPDATE health_records
            SET weight = ?, hrv = ?, ...
            WHERE date = ?
        """)
    else:
        # 2b. 插入新记录（INSERT）
        cursor.execute("""
            INSERT INTO health_records (date, weight, hrv, ...)
            VALUES (?, ?, ?, ...)
        """)
```

**保证：**
- ✅ 同一天多次parse → 只更新数据，不新增记录
- ✅ 运动和饮食记录先删除旧的再插入新的
- ✅ 完全幂等（多次执行结果相同）

**测试场景：**
```bash
# 早上parse一次
python cli.py parse --date 2025-10-27
# → 插入 2025-10-27 记录

# 下午再parse一次（补充了运动）
python cli.py parse --date 2025-10-27
# → 更新 2025-10-27 记录（不是新增）

# 结果：只有1条记录
```

---

### 2. Google Sheets单条保存 (`storage/google_sheets_storage.py`)

```python
def save_health_record(self, record: Dict[str, Any]) -> bool:
    # 1. 查找该日期是否已存在
    dates_column = self.health_sheet.col_values(1)[1:]
    row_num = None
    for i, d in enumerate(dates_column, start=2):
        if d == date_str:
            row_num = i
            break

    if row_num:
        # 2a. 更新现有行（UPDATE）
        self.health_sheet.update(f'A{row_num}', [data_row])
    else:
        # 2b. 添加新行（INSERT）
        self.health_sheet.append_row(data_row)
```

**保证：**
- ✅ 同一天多次push → 只更新同一行，不新增行
- ✅ 完全幂等

**测试场景：**
```bash
# 第一次push
python sync_cli.py push --date 2025-10-27
# → 添加新行（第211行）

# 第二次push（修改了数据）
python sync_cli.py push --date 2025-10-27
# → 更新第211行（不是添加第212行）

# 结果：只有1行
```

---

## 🔀 第三层：批量处理去重

### Google Sheets批量保存 (`storage/google_sheets_storage.py`)

```python
def batch_save_health_records(self, records: List[Dict], batch_size: int = 10):
    # 1. 获取云端已存在的日期
    dates_column = self.health_sheet.col_values(1)[1:]
    existing_dates_map = {d: i+2 for i, d in enumerate(dates_column)}

    for batch_records in batches:
        new_rows = []
        new_row_dates = []  # ← 跟踪本批次已添加的日期
        update_data = []

        for record in batch_records:
            date_str = record.get('date')

            if date_str in existing_dates_map:
                # 2a. 云端已存在 → 准备更新
                update_data.append(...)
            else:
                # 2b. 云端不存在 → 检查本批次是否已添加
                if date_str not in new_row_dates:
                    # 2b-1. 本批次未添加 → 添加到new_rows
                    new_rows.append(row_data)
                    new_row_dates.append(date_str)
                else:
                    # 2b-2. 本批次已添加 → 更新该行数据（不是新增）
                    idx = new_row_dates.index(date_str)
                    new_rows[idx] = row_data

        # 3. 批量执行
        self.health_sheet.append_rows(new_rows)      # 新增
        self.health_sheet.batch_update(update_data)  # 更新
```

**保证：**
- ✅ 云端已存在的日期 → 更新
- ✅ 批次内重复的日期 → 只添加1次，使用最后的数据
- ✅ 防止批量同步时产生重复

**测试场景：**
```python
# 批量数据包含重复
records = [
    {'date': '2025-10-27', 'weight': 70},
    {'date': '2025-10-27', 'weight': 71},  # 重复
    {'date': '2025-10-27', 'weight': 72},  # 重复
    {'date': '2025-10-28', 'weight': 73},
]

# 批量保存
batch_save_health_records(records)

# 结果：
# - 2025-10-27：只添加1行，weight=72（最后一个）
# - 2025-10-28：添加1行，weight=73
# - 总共新增2行
```

---

## 🤖 自动定时同步的安全性

### 定时任务执行流程

```bash
# sync-auto.sh (每天23:00运行)
python cli.py parse --date today   # ← 步骤1：提取数据
python sync_cli.py push             # ← 步骤2：同步数据
```

### 多次运行的安全性

**场景1：同一天多次修改日记**

```
08:00 写晨测 → 23:00定时任务运行
  ↓ parse → 保存到本地数据库（INSERT）
  ↓ push  → 上传到Google Sheets（INSERT）

15:00 补充跑步 → 手动运行 hs
  ↓ parse → 更新本地数据库（UPDATE）
  ↓ push  → 更新Google Sheets（UPDATE）

20:00 补充晚餐 → 23:00定时任务再次运行
  ↓ parse → 更新本地数据库（UPDATE）
  ↓ push  → 更新Google Sheets（UPDATE）

结果：只有1条记录，包含所有内容
```

**场景2：误操作多次同步**

```bash
# 不小心运行了3次
python sync_cli.py push --date 2025-10-27
python sync_cli.py push --date 2025-10-27
python sync_cli.py push --date 2025-10-27

# 结果：只有1行，数据相同
# 因为：UPSERT逻辑保证幂等性
```

**场景3：定时任务+手动同步重叠**

```
22:58 手动运行: hs
  ↓ parse & push 开始

23:00 定时任务启动
  ↓ parse & push 开始

结果：可能两个进程同时运行
  → parse：都是UPDATE，结果相同
  → push：都是UPDATE，最后一个完成的生效
  → 只有1条记录
```

---

## 🧪 测试验证

运行综合测试：

```bash
python test_duplicate_prevention.py
```

**测试内容：**
1. 本地数据库多次保存同一天
2. Google Sheets多次保存同一天
3. 批量保存包含重复日期

**预期结果：**
- ✅ 所有测试通过
- ✅ 无重复记录产生

---

## 📊 数据完整性保证总结

| 场景 | 保护机制 | 结果 |
|------|---------|------|
| 同一天多次parse | SQLite UPSERT | ✅ 只有1条记录（UPDATE） |
| 同一天多次push | Google Sheets UPSERT | ✅ 只有1行（UPDATE） |
| 批量同步包含重复 | 批次内去重 | ✅ 每个日期只添加1次 |
| 定时任务重复运行 | 所有层面的UPSERT | ✅ 幂等，结果相同 |
| 手动+自动同步重叠 | UPSERT逻辑 | ✅ 最后一个生效 |
| 中断后重新同步 | UPSERT逻辑 | ✅ 继续同步，不重复 |

---

## ⚠️ 注意事项

### 已知限制

1. **并发写入**
   - 如果两个进程同时更新同一天的数据
   - 最后完成的会覆盖先完成的
   - **建议**：避免在多台设备同时修改同一天的数据

2. **网络中断**
   - push到一半网络中断
   - 已同步的记录已更新，未同步的保持原状
   - **解决**：重新运行push，会继续同步剩余的

3. **数据丢失风险**
   - 如果删除日记中的内容后重新parse
   - 会覆盖为新的（可能缺失的）数据
   - **建议**：日记中只追加，不删除

### 最佳实践

✅ **推荐做法：**
- 单设备完成当天记录 → 立即同步
- 切换设备前先pull
- 使用定时任务作为兜底

❌ **避免：**
- 在两个设备同时编辑同一天的数据
- 频繁手动运行全量同步（慢且浪费API配额）

---

## 🔍 故障排查

### 如果发现重复数据

1. **立即清理**
   ```bash
   python remove_duplicates.py
   ```

2. **检查版本**
   ```bash
   git log --oneline | head -5
   # 应该包含 "fix: Prevent duplicate records in batch sync"
   ```

3. **验证代码**
   ```bash
   # 检查批量保存逻辑
   grep -A5 "new_row_dates" storage/google_sheets_storage.py
   # 应该有批次内去重检查
   ```

4. **报告问题**
   - 记录复现步骤
   - 提供日志文件 `logs/sync-*.log`
   - 说明操作序列

---

## 📝 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2025-10-27 | 初始版本，包含所有防护机制 |
| 1.1 | 2025-10-27 | 修复批量同步批次内去重bug |

---

**结论：** 系统在所有层面都实现了数据唯一性保护，可以放心使用！✅

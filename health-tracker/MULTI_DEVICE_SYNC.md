# 多设备同步方案

如果你在多台设备间切换工作（PC和Mac），需要确保数据在不同设备间同步。

## 问题说明

**当前架构的问题**：
- SQLite数据库（`data/health.db`）是本地文件
- PC上导入数据后，Mac上看不到
- Mac上添加新记录后，PC上也看不到
- 即使Obsidian vault同步了，数据库文件也不会自动同步

## 🎯 推荐方案：数据库放在云同步文件夹

### 方案1: 数据库放在Obsidian Vault内（最简单）

**优点**：
- ✅ 利用现有的Obsidian同步机制
- ✅ 配置简单，一次设置
- ✅ 自动跨设备同步
- ✅ 数据和笔记在一起，逻辑清晰

**配置步骤**：

#### 在任一设备上（PC或Mac）：

1. **移动数据库到Obsidian vault**：

```bash
# 假设你的Obsidian vault在 C:\Users\taoli\Documents\Hercules（PC）
# 或 /Users/taoli/Documents/Hercules（Mac）

# 创建.health-data目录（隐藏目录）
mkdir "你的Obsidian路径/.health-data"

# 移动现有数据库（如果有）
move data\health.db "你的Obsidian路径\.health-data\health.db"  # Windows
# 或
mv data/health.db "你的Obsidian路径/.health-data/health.db"    # Mac
```

2. **修改配置文件** `config/config.json`：

```json
{
  "database_path": "C:/Users/taoli/Documents/Hercules/.health-data/health.db",  // PC
  // 或
  "database_path": "/Users/taoli/Documents/Hercules/.health-data/health.db",    // Mac

  "obsidian_vault_path": "C:/Users/taoli/Documents/Hercules",  // 或 Mac路径
  // ... 其他配置
}
```

**注意**：
- Windows和Mac的路径不同，每台设备需要调整
- 或者使用相对路径（见方案1B）

#### 方案1B: 使用相对路径（推荐）

更智能的方式是使用相对路径：

**修改 `config/config.json`**：

```json
{
  "database_path": "../.health-data/health.db",  // 相对于health-tracker目录
  "obsidian_vault_path": "../Hercules",          // 相对路径
  // ... 其他配置
}
```

**目录结构**：
```
Documents/
  ├── andrewData/
  │   └── health-tracker/    ← 程序目录
  └── Hercules/              ← Obsidian vault
      ├── .health-data/
      │   └── health.db      ← 数据库（被Obsidian同步）
      └── 2025-10-27.md
```

这样PC和Mac使用相同的配置文件！

---

### 方案2: 数据库放在专用云同步文件夹

如果你使用OneDrive、Dropbox、iCloud等：

#### OneDrive示例（Windows常用）：

```json
{
  "database_path": "C:/Users/taoli/OneDrive/HealthTracker/health.db",  // PC
  "database_path": "/Users/taoli/OneDrive/HealthTracker/health.db",    // Mac
}
```

#### iCloud示例（Mac常用）：

```json
{
  "database_path": "/Users/taoli/Library/Mobile Documents/com~apple~CloudDocs/HealthTracker/health.db"
}
```

---

## 🔄 同步注意事项

### 1. 避免同时在两台设备操作

**最佳实践**：
- ✅ 在一台设备完成操作后，等待几秒让文件同步
- ✅ 切换到另一台设备前，确认同步完成
- ❌ 避免同时在两台设备上运行 `parse` 或 `import` 命令

### 2. SQLite并发限制

SQLite不支持多设备同时写入。如果同时操作：
- ⚠️ 可能导致数据冲突
- ⚠️ 可能导致数据库损坏

**解决方法**：
- 保持操作间隔（推荐）
- 或使用方案3（Google Sheets）

### 3. 同步冲突处理

如果出现冲突（如Obsidian提示"冲突副本"）：

```bash
# 1. 备份两个版本
cp .health-data/health.db .health-data/health.db.backup1
cp .health-data/health.db.conflict .health-data/health.db.backup2

# 2. 选择最新的版本作为主数据库

# 3. 从另一个版本导出缺失数据（如果需要）
```

---

## 📊 方案3: Google Sheets作为中心数据源（高级）

**优点**：
- ✅ 云端存储，多设备实时同步
- ✅ 可以在浏览器中查看数据
- ✅ 支持多设备同时访问
- ✅ 天然的数据备份

**缺点**：
- ❌ 需要配置Google API
- ❌ 需要网络连接

**配置步骤**（见 GOOGLE_SHEETS_SETUP.md）：

1. 创建Google Sheets
2. 启用Google Sheets API
3. 配置 `config/config.json`：

```json
{
  "google_sheets_enabled": true,
  "google_sheet_id": "你的表格ID",
  "google_credentials_file": "config/credentials.json"
}
```

4. 每次操作后自动同步：

```bash
# 导入数据时自动同步到Google Sheets
python cli.py parse --date 2025-10-27 --sync
```

---

## 🎬 快速配置（推荐方案1B）

**步骤1**：在任一设备上配置

```bash
# 1. 进入health-tracker目录
cd health-tracker

# 2. 创建Obsidian vault内的数据目录
mkdir "../Hercules/.health-data"

# 3. 如果已有数据库，移动过去
# Windows:
move data\health.db ..\Hercules\.health-data\health.db
# Mac:
mv data/health.db ../Hercules/.health-data/health.db

# 4. 编辑配置文件
notepad config\config.json  # Windows
# 或
nano config/config.json     # Mac
```

**修改为**：
```json
{
  "database_path": "../Hercules/.health-data/health.db",
  "obsidian_vault_path": "../Hercules",
  // ... 其他配置保持不变
}
```

**步骤2**：在另一台设备上

```bash
# 1. 克隆或更新代码
git pull

# 2. 使用相同的配置文件（因为用的是相对路径）
# 无需修改！

# 3. 测试
python cli.py show --days 7
```

✅ 完成！两台设备现在共享同一个数据库。

---

## 🔍 验证同步

在PC上：
```bash
python cli.py show --date 2025-10-27
```

切换到Mac后：
```bash
# 等待几秒让Obsidian同步
python cli.py show --date 2025-10-27
# 应该看到相同的数据
```

---

## 🆘 常见问题

### Q: Obsidian会同步`.health-data`目录吗？

A: 默认会。但如果Obsidian设置了排除规则，需要检查：
- Obsidian设置 → 文件与链接 → 排除的文件
- 确保 `.health-data` 不在排除列表中

### Q: 同步速度慢怎么办？

A:
- 方案1：压缩数据库（较少使用）
- 方案2：使用Google Sheets
- 方案3：手动导出/导入（不推荐）

### Q: 数据库文件冲突了怎么办？

A:
```bash
# 1. 查看数据库大小和修改时间
ls -lh .health-data/health.db*

# 2. 选择更大或更新的版本

# 3. 备份旧版本
cp health.db health.db.old

# 4. 如果需要，从旧版本导出数据后合并
```

### Q: 能否同时使用本地数据库和Google Sheets？

A: 可以！配置双向同步：
```json
{
  "database_path": "../Hercules/.health-data/health.db",
  "google_sheets_enabled": true,
  "google_sheet_id": "your_sheet_id"
}
```

每次操作都会同步到两处。

---

## 📝 总结

| 方案 | 难度 | 同步速度 | 可靠性 | 推荐指数 |
|------|------|---------|--------|----------|
| **方案1B: 相对路径+Obsidian同步** | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 方案1A: 绝对路径+Obsidian同步 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 方案2: OneDrive/iCloud | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| 方案3: Google Sheets | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

**最推荐：方案1B（相对路径+Obsidian同步）** - 简单、快速、可靠！

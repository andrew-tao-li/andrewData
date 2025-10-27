# Google Sheets 配置指南

使用Google Sheets作为云端数据源，实现多设备实时同步。

---

## 🎯 为什么使用Google Sheets？

✅ **完全避免数据库文件同步问题**
✅ **多设备实时同步**（PC、Mac、手机都能访问）
✅ **自动备份和版本历史**
✅ **可以在浏览器中查看数据**
✅ **支持多设备同时访问**

---

## ⏱️ 配置时间

- **首次配置**: 约20分钟
- **之后使用**: 完全自动，无需手动操作

---

## 📋 配置步骤

### 阶段1: Google Cloud配置（10分钟）

#### 步骤1: 创建Google Cloud项目

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 登录你的Google账号
3. 点击顶部的"选择项目" → "新建项目"
4. 项目名称填写：`Health Tracker`（随意命名）
5. 位置：无组织（默认即可）
6. 点击"创建"

**等待片刻**，项目创建完成后会自动切换到新项目。

---

#### 步骤2: 启用Google Sheets API

1. 在左侧菜单中，点击"API和服务" → "库"
2. 在搜索框中输入：`Google Sheets API`
3. 点击"Google Sheets API"
4. 点击蓝色的"启用"按钮

**等待几秒**，API启用完成。

---

#### 步骤3: 创建服务账号（重要！）

1. 在左侧菜单中，点击"API和服务" → "凭据"
2. 点击顶部的"+ 创建凭据" → "服务账号"
3. 填写服务账号详情：
   - **服务账号名称**: `health-tracker-bot`（随意命名）
   - **服务账号ID**: 自动生成（不用改）
   - **服务账号说明**: `健康追踪系统自动同步服务`（可选）
4. 点击"创建并继续"
5. **角色**：跳过（不需要选择），点击"继续"
6. **授予用户访问权限**：跳过，点击"完成"

---

#### 步骤4: 下载服务账号密钥（关键步骤！）

1. 在"凭据"页面，找到刚刚创建的服务账号
2. 点击服务账号名称（如 `health-tracker-bot@...`）
3. 切换到"密钥"标签页
4. 点击"添加密钥" → "创建新密钥"
5. **密钥类型**: 选择"JSON"（重要！）
6. 点击"创建"

**密钥文件会自动下载**到你的电脑（通常在"下载"文件夹）。

文件名类似：`health-tracker-xxxxx-xxxxxx.json`

---

#### 步骤5: 整理凭据文件

**Windows**:
```powershell
# 将下载的文件移动到项目目录并重命名
move "C:\Users\你的用户名\Downloads\health-tracker-*.json" "D:\claudecode\andrewData\health-tracker\config\credentials.json"
```

**Mac**:
```bash
# 将下载的文件移动到项目目录并重命名
mv ~/Downloads/health-tracker-*.json ~/Documents/andrewData/health-tracker/config/credentials.json
```

---

#### 步骤6: 记录服务账号邮箱（重要！下一步要用）

打开 `config/credentials.json`，找到 `client_email` 字段：

```json
{
  "type": "service_account",
  "project_id": "health-tracker-xxxxx",
  "client_email": "health-tracker-bot@health-tracker-xxxxx.iam.gserviceaccount.com",
  ...
}
```

**复制这个邮箱地址**（`health-tracker-bot@...`），下一步需要用到！

---

### 阶段2: Google Sheets设置（3分钟）

#### 步骤7: 创建Google表格

1. 访问 [Google Sheets](https://sheets.google.com/)
2. 点击"空白"创建新表格
3. 将表格命名为：`健康追踪数据`（点击左上角"无标题表格"修改）

---

#### 步骤8: 共享表格给服务账号（关键步骤！）

**这一步最容易忘记，但非常重要！**

1. 点击右上角的"共享"按钮
2. 在"添加用户和群组"输入框中，粘贴刚才复制的服务账号邮箱：
   ```
   health-tracker-bot@health-tracker-xxxxx.iam.gserviceaccount.com
   ```
3. 权限设置为："编辑者"（允许程序写入数据）
4. **取消勾选** "通知用户"（机器人不需要通知）
5. 点击"共享"

---

#### 步骤9: 获取表格ID

从表格的URL中复制ID：

```
https://docs.google.com/spreadsheets/d/1A2B3C4D5E6F7G8H9I0J1K2L3M4N5O6P7Q8R9S/edit
                                      ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑
                                      这就是表格ID，复制这一段
```

**复制表格ID**（从 `/d/` 后到 `/edit` 前的那一长串字符）

---

### 阶段3: 程序配置（2分钟）

#### 步骤10: 编辑配置文件

打开 `config/config.json`，添加Google Sheets配置：

```json
{
  "database_path": "data/health.db",

  "google_sheets_enabled": true,
  "google_sheet_id": "1A2B3C4D5E6F7G8H9I0J1K2L3M4N5O6P7Q8R9S",
  "google_credentials_file": "config/credentials.json",

  "obsidian_vault_path": "你的Obsidian路径",
  "openrouter_api_key": "你的OpenRouter密钥",
  ...
}
```

**重要**：
- `google_sheets_enabled`: 必须设置为 `true`
- `google_sheet_id`: 粘贴你刚才复制的表格ID
- `google_credentials_file`: 默认 `config/credentials.json`（如果你放在其他位置，修改这里）

---

### 阶段4: 测试连接（2分钟）

#### 步骤11: 运行测试脚本

**Windows**:
```powershell
cd D:\claudecode\andrewData\health-tracker
python test_google_sheets.py
```

**Mac**:
```bash
cd ~/Documents/andrewData/health-tracker
python test_google_sheets.py
```

**如果配置正确**，你会看到：

```
============================================================
Google Sheets 连接测试
============================================================

📋 步骤 1: 检查配置文件
✓ 配置文件存在
✓ Google Sheets已启用

📋 步骤 2: 检查凭据文件
✓ 凭据文件存在: config/credentials.json

📋 步骤 3: 检查表格ID
✓ 表格ID: 1A2B3C4D5E6F7G8H9I0J1K2L3M4N5O6P7Q8R9S

📋 步骤 4: 测试Google Sheets连接
✓ 成功连接到Google Sheets

📋 步骤 5: 获取表格信息

表格信息:
  名称: 健康追踪数据
  URL: https://docs.google.com/spreadsheets/d/...
  工作表: 健康记录, 运动记录, 饮食记录
  记录数: 0

📋 步骤 6: 测试写入数据
✓ 成功写入测试记录

📋 步骤 7: 测试读取数据
✓ 成功读取测试记录

读取到的数据:
  日期: 2025-01-01
  体重: 70.0 kg
  肌肉量: 35.0 kg
  睡眠时长: 7.5 小时
  HRV: 50
  备注: Google Sheets测试记录

📋 步骤 8: 清理测试数据
✓ 成功删除测试记录

============================================================
✅ 所有测试通过！Google Sheets配置正确
============================================================
```

**恭喜！配置成功！**

---

## 🚀 使用方法

### 导入历史数据并同步

```powershell
# 导入CSV数据，自动同步到Google Sheets
python import_csv.py "热量赤字-明细-1026.csv" --sync
```

### 解析笔记并同步

```powershell
# 解析Obsidian笔记，自动同步到Google Sheets
python cli.py parse --date 2025-10-27 --sync
```

### 从云端拉取数据

在另一台设备上（如Mac）：

```bash
# 拉取所有数据
python cli.py sync --pull

# 只拉取最近7天
python cli.py sync --pull --days 7
```

### 查看同步状态

```powershell
python cli.py sync-status
```

输出示例：
```
同步状态:
  ✓ Google Sheets已启用
  本地记录数: 210
  云端记录数: 210
  本地最新日期: 2025-10-26
  云端最新日期: 2025-10-26
  ✓ 数据已同步
```

---

## 🔄 多设备工作流程

### 在公司PC上（早上）

```powershell
# 1. 拉取最新数据
python cli.py sync --pull

# 2. 解析今天的笔记
python cli.py parse --date 2025-10-27 --sync

# 3. 导入历史数据（首次）
python import_csv.py data.csv --sync

# 4. 查询数据
python cli.py show --days 7

# 5. AI分析
python cli.py chat "分析我的健康趋势" --days 30
```

### 在家Mac上（晚上）

```bash
# 1. 拉取最新数据（自动获取白天在PC上添加的数据）
python cli.py sync --pull

# 2. 查看数据（立即看到白天的记录）
python cli.py show --date 2025-10-27

# 3. 继续分析
python cli.py chat "今天的数据怎么样？" --days 1
```

**无需等待文件同步！数据已在云端！**

---

## ⚠️ 常见问题

### Q1: "403 Forbidden" 错误

**原因**: 忘记共享表格给服务账号

**解决**:
1. 打开Google表格
2. 点击"共享"
3. 确认服务账号邮箱（`health-tracker-bot@...`）在共享列表中
4. 权限是"编辑者"

---

### Q2: "404 Not Found" 错误

**原因**: 表格ID错误

**解决**:
1. 从表格URL重新复制ID
2. 确保复制的是 `/d/` 和 `/edit` 之间的部分
3. 更新 `config.json` 中的 `google_sheet_id`

---

### Q3: "Credentials not found" 错误

**原因**: 凭据文件路径错误

**解决**:
1. 确认 `credentials.json` 在 `config/` 目录下
2. 检查 `config.json` 中 `google_credentials_file` 路径是否正确

---

### Q4: 密钥文件下载的是错误类型

**现象**: 下载的文件是 `.p12` 而不是 `.json`

**解决**:
1. 删除旧密钥
2. 重新创建密钥时，确保选择"JSON"类型（不是P12）

---

### Q5: API未启用

**错误信息**: `Google Sheets API has not been used in project...`

**解决**:
1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 进入"API和服务" → "库"
3. 搜索"Google Sheets API"
4. 点击"启用"

---

## 🔒 安全提示

### 保护你的凭据文件

`credentials.json` 包含私钥，**不要分享给他人**，也**不要上传到公开的GitHub仓库**！

如果使用Git，确保 `.gitignore` 包含：

```
config/credentials.json
config/config.json
```

### 服务账号权限

服务账号只能访问你明确共享给它的Google Sheets，**不能访问**你的其他Google文件或邮件。

---

## 📊 数据结构

配置成功后，Google Sheets会自动创建3个工作表：

### 1. 健康记录（主表）

包含所有晨测数据：体重、睡眠、HRV、疼痛等

### 2. 运动记录

包含运动详情：类型、时长、配速、心率等

### 3. 饮食记录

包含饮食记录：食物、热量等

---

## 🎉 配置完成后的优势

✅ **PC导入数据 → 云端自动同步 → Mac立即可见**
✅ **无需等待Obsidian文件同步**
✅ **无需担心数据库文件冲突**
✅ **手机/平板也能查看数据**（打开Google Sheets）
✅ **Google自动备份和版本历史**

---

## 💡 下一步

配置成功后，建议：

1. **导入历史数据**:
   ```powershell
   python import_csv.py "热量赤字-明细-1026.csv" --sync
   ```

2. **在另一台设备测试同步**:
   ```bash
   python cli.py sync --pull
   python cli.py show --days 7
   ```

3. **日常使用**:
   - 早上晨测 → 记录到Obsidian → `parse --sync`
   - 晚上回家 → `sync --pull` → 查看数据

---

## 🆘 需要帮助？

如果遇到问题：

1. 运行测试脚本查看详细错误：
   ```powershell
   python test_google_sheets.py
   ```

2. 检查配置清单：
   - ✅ Google Cloud项目已创建
   - ✅ Google Sheets API已启用
   - ✅ 服务账号已创建
   - ✅ JSON密钥已下载并放到 `config/credentials.json`
   - ✅ Google表格已创建
   - ✅ 表格已共享给服务账号邮箱（编辑者权限）
   - ✅ 表格ID已复制到 `config.json`
   - ✅ `google_sheets_enabled` 设置为 `true`

3. 查看日志输出，根据错误信息调整配置

---

**祝配置顺利！** 🎊

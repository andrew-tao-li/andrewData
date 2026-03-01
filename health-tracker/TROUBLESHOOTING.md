# 故障排查指南

> 🚨 **出问题时的完整排查流程**

---

## 📝 日志文件说明

### 主要日志文件（按重要性排序）

#### 1. **scheduler.log** - 最重要！

```bash
tail -50 /Users/taoli/andrewData/health-tracker/logs/scheduler.log
```

**包含内容：**
- ✅ 调度器启动信息
- ✅ 每日 12:00 同步记录
- ✅ 周报/月报生成记录
- ✅ 成功/失败状态

**什么时候看：**
- 想知道调度器是否正常运行
- 检查数据是否成功同步
- 验证报告是否生成

**示例输出（正常）：**
```
2026-03-01 12:00:00 - INFO - 开始同步 2026-02-28 的 Garmin 数据...
2026-03-01 12:00:15 - INFO - ✓ 2026-02-28 数据同步成功
2026-03-02 08:00:00 - INFO - 开始生成本周健康周报...
2026-03-02 08:00:30 - INFO - ✓ 周报已保存到: /Users/taoli/Documents/hercules/Health/分析/2026-03-02 周健康分析.md
```

**示例输出（失败）：**
```
2026-03-01 12:00:00 - ERROR - 获取 Garmin 数据失败
2026-03-01 12:00:01 - WARNING - 同步失败，将在 13:00 重试
```

---

#### 2. **scheduler-error.log** - 错误专用

```bash
tail -50 /Users/taoli/andrewData/health-tracker/logs/scheduler-error.log
```

**包含内容：**
- ❌ Python 报错信息
- ❌ 调度器崩溃日志
- ❌ 致命错误

**什么时候看：**
- scheduler.log 显示错误时
- 调度器启动失败
- 数据同步持续失败

---

#### 3. **sync-YYYYMMDD.log** - 每日同步详情

```bash
# 查看今天的同步日志
tail -50 /Users/taoli/andrewData/health-tracker/logs/sync-$(date +%Y%m%d).log
```

**包含内容：**
- 详细的同步步骤
- Obsidian 笔记解析
- Google Sheets 同步

---

### 日志位置总览

```
/Users/taoli/andrewData/health-tracker/logs/
├── scheduler.log          ← 主日志（最重要）
├── scheduler-error.log    ← 错误日志
├── sync-20260301.log     ← 每日同步日志
├── sync-20260302.log
└── garmin_scheduler.log   ← Garmin 调度器日志
```

---

## 🔍 快速诊断流程

### 第一步：检查调度器是否运行

```bash
launchctl list | grep health-tracker
```

**正常输出：**
```
1413	0	com.health-tracker.scheduler  ← 有 PID 号，正在运行 ✅
```

**异常输出：**
```
-	1	com.health-tracker.scheduler  ← Exit code 1，已崩溃 ❌
```
或者没有任何输出 → 调度器没有启动

**解决方案：**
```bash
cd /Users/taoli/andrewData/health-tracker
./setup-scheduler.sh
```

---

### 第二步：查看最近的日志

```bash
cd /Users/taoli/andrewData/health-tracker

# 查看最近 50 行主日志
tail -50 logs/scheduler.log

# 如果有错误，查看错误日志
tail -50 logs/scheduler-error.log
```

---

### 第三步：根据错误类型排查

---

## 🚨 常见错误及解决方案

### 错误 1：Garmin 登录失败

**日志特征：**
```
ERROR - Garmin 登录失败: 用户名或密码错误
ERROR - 401 Unauthorized
```

**原因：**
- Garmin 密码修改了
- 账号被锁定

**解决方案：**

1. 检查 Garmin 账号是否正常（浏览器登录 connect.garmin.cn）
2. 更新配置文件：
```bash
nano config/config.json
# 修改 garmin_email 和 garmin_password
```
3. 重启调度器：
```bash
launchctl unload ~/Library/LaunchAgents/com.health-tracker.scheduler.plist
launchctl load ~/Library/LaunchAgents/com.health-tracker.scheduler.plist
```

---

### 错误 2：数据验证失败

**日志特征：**
```
WARNING - 数据验证失败，缺少必需字段
WARNING - 缺少字段: sleep_duration
```

**原因：**
- Garmin 当天数据不完整（睡眠未同步到 Garmin）
- HRV 数据缺失

**解决方案：**
- **无需操作**，系统会自动在下午重试（13:00-18:00）
- 等待手表数据完全同步到 Garmin 服务器（通常需要上午 11 点后）

**手动验证：**
```bash
# 登录 Garmin Connect，检查数据是否完整
# 或手动同步：
python3 cli.py garmin-sync --date yesterday --force
```

---

### 错误 3：网络连接失败

**日志特征：**
```
ERROR - 网络连接超时
ERROR - ConnectionError: Failed to establish connection
```

**原因：**
- 网络断开
- Garmin 服务器维护

**解决方案：**
- **无需操作**，系统会自动重试
- 检查网络连接
- 等待 Garmin 服务器恢复

---

### 错误 4：Google Sheets 同步失败

**日志特征：**
```
ERROR - Google Sheets 同步失败
ERROR - 凭证文件不存在
ERROR - Token has been expired or revoked
```

**原因：**
- Google 凭证过期
- 凭证文件缺失

**解决方案：**

1. 检查凭证文件：
```bash
ls -l config/google-credentials.json
ls -l config/credentials.json
```

2. 重新授权：
```bash
python3 cli.py sync --days 1
# 按照提示在浏览器中完成授权
```

---

### 错误 5：周报/月报生成失败

**日志特征：**
```
ERROR - 生成周报失败: No such file or directory
ERROR - 无法保存报告: Permission denied
```

**原因：**
- Obsidian vault 路径错误
- 没有写入权限
- 分析文件夹不存在

**解决方案：**

1. 检查配置：
```bash
cat config/config.json | grep obsidian_vault_path
cat config/config.json | grep analysis_folder
```

2. 验证路径：
```bash
ls -ld /Users/taoli/Documents/hercules/Health/分析/
```

3. 手动创建文件夹：
```bash
mkdir -p /Users/taoli/Documents/hercules/Health/分析
```

4. 测试生成：
```bash
python3 cli.py report --period week
```

---

### 错误 6：调度器启动失败

**日志特征：**
```
ERROR - ModuleNotFoundError: No module named 'analytics'
ERROR - ImportError: cannot import name 'HealthAnalyzer'
```

**原因：**
- 虚拟环境未激活
- 依赖包缺失

**解决方案：**

1. 检查虚拟环境：
```bash
which python3
# 应该输出: /Users/taoli/andrewData/health-tracker/venv/bin/python3
```

2. 重新安装依赖：
```bash
cd /Users/taoli/andrewData/health-tracker
source venv/bin/activate
pip install -r requirements.txt
```

3. 重启调度器：
```bash
./setup-scheduler.sh
```

---

### 错误 7：数据库锁定

**日志特征：**
```
ERROR - database is locked
ERROR - unable to open database file
```

**原因：**
- 多个进程同时访问数据库
- 数据库文件损坏

**解决方案：**

1. 检查是否有多个调度器运行：
```bash
ps aux | grep scheduler
```

2. 停止所有调度器：
```bash
launchctl unload ~/Library/LaunchAgents/com.health-tracker.scheduler.plist
pkill -f scheduler
```

3. 重启调度器：
```bash
launchctl load ~/Library/LaunchAgents/com.health-tracker.scheduler.plist
```

4. 如果持续失败，备份并重建数据库：
```bash
cp health_data.db health_data.backup.db
sqlite3 health_data.db "PRAGMA integrity_check;"
```

---

## 🔧 高级排查

### 实时监控日志

```bash
# 实时查看所有日志
tail -f logs/scheduler.log logs/scheduler-error.log
```

### 查找特定错误

```bash
# 搜索错误关键词
grep -i "error\|fail\|exception" logs/scheduler.log

# 查看最近的错误
grep -i "error" logs/scheduler.log | tail -20
```

### 测试单个组件

```bash
# 测试 Garmin 连接
python3 cli.py garmin-test

# 测试数据同步
python3 cli.py garmin-sync --date yesterday

# 测试报告生成
python3 cli.py report --period week

# 测试 Google Sheets
python3 cli.py sync --days 1
```

---

## 📊 日志分析速查表

| 问题 | 查看的日志 | 关键词 |
|------|-----------|--------|
| 调度器没有运行 | scheduler-error.log | "ModuleNotFoundError", "ImportError" |
| Garmin 同步失败 | scheduler.log | "Garmin", "登录失败", "401" |
| 数据验证失败 | scheduler.log | "验证失败", "缺少字段" |
| 报告生成失败 | scheduler-error.log | "生成周报失败", "生成月报失败" |
| Google Sheets 失败 | sync-YYYYMMDD.log | "Google Sheets", "凭证" |
| 数据库错误 | scheduler-error.log | "database", "locked" |

---

## 🆘 紧急救援

### 完全重置调度器

```bash
# 1. 停止所有服务
launchctl unload ~/Library/LaunchAgents/com.health-tracker.scheduler.plist

# 2. 杀死所有进程
pkill -f scheduler

# 3. 清理旧日志
rm logs/scheduler*.log

# 4. 重新安装
cd /Users/taoli/andrewData/health-tracker
./setup-scheduler.sh

# 5. 验证
launchctl list | grep health-tracker
tail -f logs/scheduler.log
```

### 数据恢复

```bash
# 如果有备份
cp backups/health_data.backup.db health_data.db

# 从 Google Sheets 重新导入
# (需要手动操作，根据实际情况)
```

---

## 📞 获取帮助

**查看文档：**
- `MAINTENANCE.md` - 日常维护指南
- `AUTOMATION_GUIDE.md` - 自动化详细说明
- `FAQ.md` - 常见问题

**最关键的命令：**
```bash
# 查看日志（99% 的问题都能从这里找到答案）
tail -50 logs/scheduler.log
tail -50 logs/scheduler-error.log
```

**重启大法（解决 80% 的问题）：**
```bash
./setup-scheduler.sh
```

---

记住：**先看日志，再动手！** 📝

# 健康追踪系统 - 维护指南

> 💡 **即使你忘记了所有开发细节，这个文档也能帮你维护整个系统**

---

## 🎯 系统概览

**这个系统做什么？**
- 每天 12:00 自动从 Garmin 拉取健康数据
- 保存到：本地数据库 + Obsidian 笔记 + Google Sheets
- 每周日 08:00 自动生成周报
- 每月最后一天 20:00 自动生成月报

**它是如何自动运行的？**
- macOS LaunchAgent 后台服务（开机自启）
- 调度器：`com.health-tracker.scheduler`

---

## ⚙️ 日常操作

### 查看系统状态

```bash
# 1. 检查调度器是否运行
launchctl list | grep health-tracker

# 应该看到：
# 1413	0	com.health-tracker.scheduler  ← 正在运行
```

### 查看日志（出问题时看这个）

```bash
cd /Users/taoli/andrewData/health-tracker

# 查看最近的日志（最重要！）
tail -50 logs/scheduler.log

# 查看错误日志
tail -50 logs/scheduler-error.log

# 实时监控日志
tail -f logs/scheduler.log
```

### 手动同步数据（不想等自动运行）

```bash
cd /Users/taoli/andrewData/health-tracker
source venv/bin/activate

# 同步今天的数据
python3 cli.py garmin-sync --date today

# 同步昨天的数据
python3 cli.py garmin-sync --date yesterday
```

### 手动生成报告

```bash
# 生成周报
python3 cli.py report --period week

# 生成月报
python3 cli.py report --period month

# 分析最近 30 天并保存
python3 cli.py analyze --days 30 --save
```

---

## 🔧 系统管理

### 重启调度器（出问题时试试这个）

```bash
# 停止
launchctl unload ~/Library/LaunchAgents/com.health-tracker.scheduler.plist

# 启动
launchctl load ~/Library/LaunchAgents/com.health-tracker.scheduler.plist

# 验证
launchctl list | grep health-tracker
```

### 停止自动化（临时关闭）

```bash
launchctl unload ~/Library/LaunchAgents/com.health-tracker.scheduler.plist
```

### 恢复自动化

```bash
launchctl load ~/Library/LaunchAgents/com.health-tracker.scheduler.plist
```

### 完全卸载自动化

```bash
launchctl unload ~/Library/LaunchAgents/com.health-tracker.scheduler.plist
rm ~/Library/LaunchAgents/com.health-tracker.scheduler.plist
```

---

## 🔑 重要文件位置

### 配置文件

```
/Users/taoli/andrewData/health-tracker/config/config.json
```

**需要修改的配置：**
- `garmin_email` / `garmin_password` - Garmin 账号
- `obsidian_vault_path` - Obsidian vault 路径
- `google_sheet_id` - Google Sheets ID
- `garmin_sync_time` - 同步时间（默认 12:00）

### 数据库

```
/Users/taoli/andrewData/health-tracker/health_data.db
```

**备份数据库：**
```bash
cp health_data.db health_data.backup.$(date +%Y%m%d).db
```

### 日志文件

```
logs/scheduler.log         # 主日志（最重要）
logs/scheduler-error.log   # 错误日志
logs/sync-YYYYMMDD.log    # 每日同步日志
logs/garmin_scheduler.log  # Garmin 调度器日志
```

### 报告保存位置

```
/Users/taoli/Documents/hercules/Health/分析/
  ├── 2026-03 健康分析.md         # 月报
  └── 2026-03-01 周健康分析.md    # 周报
```

---

## 📊 自动化时间表

| 时间 | 任务 | 说明 |
|------|------|------|
| 每天 12:00 | Garmin 数据同步 | 获取昨天的数据 |
| 13:00 | 重试（如果失败） | 第1次重试 |
| 14:00 | 重试（如果失败） | 第2次重试 |
| 15:00 | 重试（如果失败） | 第3次重试 |
| 16:00 | 重试（如果失败） | 第4次重试 |
| 17:00 | 重试（如果失败） | 第5次重试 |
| 18:00 | 重试（如果失败） | 第6次重试（最后一次） |
| 每周日 08:00 | 生成周报 | 保存到 Obsidian |
| 每月最后一天 20:00 | 生成月报 | 保存到 Obsidian |

---

## 🚨 常见问题

### 1. 调度器没有运行

**检查：**
```bash
launchctl list | grep health-tracker
```

**解决：**
```bash
cd /Users/taoli/andrewData/health-tracker
./setup-scheduler.sh
```

### 2. Garmin 同步失败

**检查日志：**
```bash
tail -50 logs/scheduler.log | grep -i error
```

**可能原因：**
- Garmin 密码修改了 → 更新 `config/config.json`
- 网络问题 → 等待自动重试
- Garmin 服务器问题 → 等待几小时后自动重试

**手动测试：**
```bash
python3 cli.py garmin-test
```

### 3. 报告没有生成

**检查报告文件夹：**
```bash
ls -lh /Users/taoli/Documents/hercules/Health/分析/
```

**手动生成测试：**
```bash
python3 cli.py report --period week
```

**查看错误日志：**
```bash
tail -50 logs/scheduler-error.log
```

### 4. Google Sheets 同步失败

**检查凭证文件：**
```bash
ls -l config/google-credentials.json
ls -l config/credentials.json
```

**重新授权：**
```bash
python3 cli.py sync --days 1
# 按提示完成授权
```

### 5. 数据库损坏

**先备份：**
```bash
cp health_data.db health_data.backup.$(date +%Y%m%d).db
```

**检查数据库：**
```bash
sqlite3 health_data.db "PRAGMA integrity_check;"
```

---

## 🔄 定期维护任务

### 每周

- [ ] 查看日志：`tail -50 logs/scheduler.log`
- [ ] 检查 Obsidian 周报是否生成
- [ ] 验证 Google Sheets 数据同步

### 每月

- [ ] 查看月报是否生成
- [ ] 备份数据库：`cp health_data.db backups/`
- [ ] 清理旧日志（自动清理 30 天前的日志）

### 每季度

- [ ] 更新依赖：`pip install --upgrade -r requirements.txt`
- [ ] 检查 API 余额（Claude API）
- [ ] 验证 Garmin 账号状态

---

## 📞 紧急联系

**查看完整文档：**
- `README.md` - 系统概述
- `AUTOMATION_GUIDE.md` - 自动化详细指南
- `TROUBLESHOOTING.md` - 故障排查详细指南
- `FAQ.md` - 常见问题

**查看日志：**
```bash
cd /Users/taoli/andrewData/health-tracker
tail -50 logs/scheduler.log
```

**重启系统：**
```bash
./setup-scheduler.sh
```

---

## 🎓 快速命令参考

```bash
# === 系统状态 ===
launchctl list | grep health-tracker      # 查看调度器状态
tail -f logs/scheduler.log                # 实时查看日志

# === 手动操作 ===
python3 cli.py garmin-sync --date today   # 手动同步
python3 cli.py report --period week       # 生成周报
python3 cli.py analyze --days 30 --save   # 分析并保存

# === 管理调度器 ===
launchctl unload ~/Library/LaunchAgents/com.health-tracker.scheduler.plist  # 停止
launchctl load ~/Library/LaunchAgents/com.health-tracker.scheduler.plist    # 启动

# === 备份 ===
cp health_data.db health_data.backup.$(date +%Y%m%d).db  # 备份数据库
```

---

**记住这一条：**
**出问题先看日志：** `tail -50 logs/scheduler.log`

祝你健康追踪顺利！ 🎉

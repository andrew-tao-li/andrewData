# 自动化系统使用指南

## 🎯 自动化功能概览

Health Tracker 提供了完整的自动化健康数据管理系统，包括：

### ✅ 自动同步（每天 12:00）
- 从 Garmin 获取健康数据
- 保存到本地数据库
- 写入 Obsidian 日记
- 同步到 Google Sheets
- **智能重试**：如果失败，在 13:00, 14:00, 15:00, 16:00, 17:00, 18:00 自动重试

### 📊 自动报告
- **周报**：每周日 08:00 自动生成，保存到 `Health/分析/YYYY-MM-DD 周健康分析.md`
- **月报**：每月最后一天 20:00 自动生成，保存到 `Health/分析/YYYY-MM 健康分析.md`

---

## 🚀 快速开始

### 方法 1：使用 LaunchAgent（推荐，开机自启）

```bash
cd /Users/taoli/andrewData/health-tracker

# 运行安装脚本
./setup-scheduler.sh
```

安装后，调度器会：
- ✅ 开机自动启动
- ✅ 崩溃后自动重启
- ✅ 后台持续运行

### 方法 2：手动启动调度器

```bash
cd /Users/taoli/andrewData/health-tracker
source venv/bin/activate

# 启动调度器（前台运行）
python3 cli.py start-scheduler
```

---

## 📝 手动命令

除了自动化，你还可以手动执行以下操作：

### 1. 手动同步 Garmin 数据

```bash
# 同步今天的数据
python3 cli.py garmin-sync --date today

# 同步昨天的数据
python3 cli.py garmin-sync --date yesterday

# 同步特定日期
python3 cli.py garmin-sync --date 2026-02-28
```

### 2. 手动生成报告

```bash
# 生成周报
python3 cli.py report --period week

# 生成月报
python3 cli.py report --period month

# 生成日报
python3 cli.py report --period day --date today
```

### 3. **新功能！手动分析任意天数**

```bash
# 分析最近 7 天（默认）
python3 cli.py analyze

# 分析最近 14 天
python3 cli.py analyze --days 14

# 分析最近 30 天并保存到 Obsidian
python3 cli.py analyze --days 30 --save
```

### 4. 向 AI 提问

```bash
# 询问健康问题
python3 cli.py chat "我的睡眠质量如何？" --days 30

# 询问趋势
python3 cli.py chat "最近体重有什么变化？" --days 14
```

---

## 🔧 管理调度器

### 查看调度器状态

```bash
launchctl list | grep health-tracker
```

### 查看日志

```bash
# 查看实时日志
tail -f logs/scheduler.log

# 查看错误日志
tail -f logs/scheduler-error.log

# 查看 Garmin 同步日志
tail -f logs/garmin_scheduler.log
```

### 停止调度器

```bash
launchctl unload ~/Library/LaunchAgents/com.health-tracker.scheduler.plist
```

### 重启调度器

```bash
launchctl unload ~/Library/LaunchAgents/com.health-tracker.scheduler.plist
launchctl load ~/Library/LaunchAgents/com.health-tracker.scheduler.plist
```

### 卸载调度器

```bash
launchctl unload ~/Library/LaunchAgents/com.health-tracker.scheduler.plist
rm ~/Library/LaunchAgents/com.health-tracker.scheduler.plist
```

---

## ⚙️ 配置选项

编辑 `config/config.json` 调整自动化设置：

```json
{
  "garmin_sync_time": "12:00",              // 每日同步时间
  "garmin_retry_hours": [13, 14, 15, 16, 17, 18],  // 重试时间
  "garmin_required_fields": ["sleep_duration", "hrv"],  // 必需字段
  "analysis_folder": "Health/分析",          // 报告保存位置
  "create_daily_note_if_missing": true      // 自动创建日记
}
```

---

## 🎯 完整自动化时间表

| 时间 | 任务 | 说明 |
|------|------|------|
| 每天 12:00 | Garmin 数据同步 | 获取昨天的数据 |
| 13:00-18:00 | 自动重试 | 如果 12:00 失败 |
| 每周日 08:00 | 生成周报 | 分析过去 7 天 |
| 每月最后一天 20:00 | 生成月报 | 分析整个月 |

---

## 🐛 故障排查

### 调度器没有启动

```bash
# 检查 plist 文件
plutil -lint ~/Library/LaunchAgents/com.health-tracker.scheduler.plist

# 查看错误日志
cat logs/scheduler-error.log
```

### Garmin 同步失败

```bash
# 测试 Garmin 连接
python3 cli.py garmin-test

# 手动同步查看详细错误
python3 cli.py garmin-sync --date yesterday
```

### 周报/月报没有生成

```bash
# 手动测试生成
python3 cli.py report --period week
python3 cli.py report --period month

# 检查调度器日志
grep "周报\|月报" logs/scheduler.log
```

---

## 💡 最佳实践

1. **定期查看日志**：每周检查一次 `logs/scheduler.log` 确保同步正常
2. **验证数据**：每周查看一次 Google Sheets 和 Obsidian，确保数据同步
3. **备份数据库**：定期备份 `health_data.db`
4. **更新凭证**：Garmin 密码修改后记得更新 `config/config.json`

---

## 📞 获取帮助

如果遇到问题：

1. 查看日志文件：`logs/scheduler.log`
2. 运行测试命令：`python3 cli.py garmin-test`
3. 查看文档：`README.md`, `FAQ.md`

祝你健康管理顺利！ 🎉

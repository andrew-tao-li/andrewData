# 🔍 自动化验证检查清单

## 📋 安装后立即验证（今天）

在 macOS 终端运行完 `setup-and-verify-automation.sh` 后，执行以下检查：

### ✅ 1. 调度器进程正在运行

```bash
ps aux | grep "cli.py start-scheduler" | grep -v grep
```

**预期结果：**
```
taoli    12345   0.0  0.5  ... python3 cli.py start-scheduler
```

如果没有输出 → **失败** ❌

---

### ✅ 2. LaunchAgent 服务已加载

```bash
launchctl list | grep health-tracker
```

**预期结果：**
```
12345  0  com.health-tracker.scheduler
```

如果没有输出 → **失败** ❌

---

### ✅ 3. 日志文件已创建

```bash
ls -lh /Users/taoli/andrewData/health-tracker/logs/
```

**预期结果：**
```
scheduler.log       (调度器主日志)
garmin_scheduler.log  (Garmin 同步日志)
```

如果日志目录为空 → **失败** ❌

---

### ✅ 4. 调度器日志显示任务已调度

```bash
cat /Users/taoli/andrewData/health-tracker/logs/scheduler.log
```

**预期结果（必须包含这些内容）：**
```
✓ 每日同步: 每天 12:00 (Asia/Shanghai) 自动同步 Garmin 数据
✓ 周报生成: 每周日 08:00 自动生成周报
✓ 月报生成: 每月最后一天 20:00 自动生成月报
调度器已启动！
```

如果没有这些输出 → **失败** ❌

---

### ✅ 5. 数据库中有昨天的数据

```bash
cd /Users/taoli/andrewData/health-tracker
source venv/bin/activate
python3 -c "
from storage import HealthDatabase
from datetime import datetime, timedelta
db = HealthDatabase()
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
record = db.get_record_by_date(yesterday)
if record:
    print(f'✓ 找到 {yesterday} 的数据')
    print(f'  睡眠: {record.get(\"sleep_duration\")} 分钟')
    print(f'  HRV: {record.get(\"hrv\")}')
else:
    print(f'✗ 没有 {yesterday} 的数据')
"
```

**预期结果：**
```
✓ 找到 2026-03-02 的数据
  睡眠: 420 分钟
  HRV: 65
```

如果显示"没有数据" → **失败** ❌

---

## 📅 明天（3月4日）12:10 验证自动同步

### ✅ 1. 同步日志文件已创建

```bash
ls -lh /Users/taoli/andrewData/health-tracker/logs/sync-20260304.log
```

**预期结果：**
```
-rw-r--r--  1 taoli  staff  2.1K  3  4 12:00 sync-20260304.log
```

文件不存在或时间不对 → **失败** ❌

---

### ✅ 2. 调度器日志显示成功

```bash
tail -20 /Users/taoli/andrewData/health-tracker/logs/scheduler.log
```

**预期结果（必须包含）：**
```
2026-03-04 12:00:00 - GarminScheduler - INFO - 开始同步 2026-03-03 的 Garmin 数据...
2026-03-04 12:00:15 - GarminScheduler - INFO - ✓ 2026-03-03 数据同步成功
```

如果没有这两行 → **失败** ❌

---

### ✅ 3. 数据库中有今天（3月3日）的数据

```bash
cd /Users/taoli/andrewData/health-tracker
source venv/bin/activate
python3 -c "
from storage import HealthDatabase
db = HealthDatabase()
record = db.get_record_by_date('2026-03-03')
if record:
    print('✓ 2026-03-03 数据同步成功')
    print(f'  睡眠: {record.get(\"sleep_duration\")} 分钟')
    print(f'  HRV: {record.get(\"hrv\")}')
else:
    print('✗ 2026-03-03 数据同步失败')
"
```

**预期结果：**
```
✓ 2026-03-03 数据同步成功
  睡眠: 435 分钟
  HRV: 68
```

如果显示"同步失败" → **失败** ❌

---

### ✅ 4. Obsidian 日记已更新

```bash
cat /Users/taoli/Documents/hercules/Health/2026-03-03.md
```

**预期结果（文件中应包含）：**
```markdown
（健康日志）

## 📊 Garmin 健康数据

### 😴 睡眠
- **总时长**: 7h 15m (435分钟)
- **深睡眠**: ...
...

（健康日志结束）
```

如果文件不存在或没有健康日志 → **失败** ❌

---

## 🎯 成功标准

**所有 9 个检查都通过 = 自动化完全成功** ✅

如果任何一项失败，请：
1. 查看日志: `tail -50 /Users/taoli/andrewData/health-tracker/logs/scheduler.log`
2. 检查错误: `tail -50 /Users/taoli/andrewData/health-tracker/logs/scheduler-error.log`
3. 重启调度器:
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.health-tracker.scheduler.plist
   launchctl load ~/Library/LaunchAgents/com.health-tracker.scheduler.plist
   ```

---

## 📞 故障排除

### 问题 1: 调度器进程没有运行

**解决方法：**
```bash
# 查看错误日志
cat /Users/taoli/andrewData/health-tracker/logs/scheduler-error.log

# 手动启动测试
cd /Users/taoli/andrewData/health-tracker
source venv/bin/activate
python3 cli.py start-scheduler
```

### 问题 2: 同步失败（12:00 没有执行）

**解决方法：**
```bash
# 手动测试同步
python3 cli.py garmin-sync --date yesterday

# 如果手动成功但自动失败，检查调度器日志
grep "ERROR\|WARN" logs/scheduler.log
```

### 问题 3: Garmin 连接失败

**解决方法：**
```bash
# 测试 Garmin 连接
python3 cli.py garmin-test

# 如果失败，检查：
# 1. 网络连接
# 2. Garmin 账号密码（config/config.json）
# 3. 是否开启了双因素认证
```

---

## 📄 日志文件位置

- **调度器主日志**: `/Users/taoli/andrewData/health-tracker/logs/scheduler.log`
- **调度器错误日志**: `/Users/taoli/andrewData/health-tracker/logs/scheduler-error.log`
- **每日同步日志**: `/Users/taoli/andrewData/health-tracker/logs/sync-YYYYMMDD.log`
- **Garmin 同步日志**: `/Users/taoli/andrewData/health-tracker/logs/garmin_scheduler.log`

---

**最后更新**: 2026-03-03

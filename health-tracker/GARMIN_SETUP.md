# Garmin 集成配置指南

> 2026-07-29 更新：当前日常自动化以 `CURRENT_AUTOMATION_STATUS.md` 为准。
> Garmin 自动同步应使用 `com.health-tracker.garmin-guard`，不要重新启用旧
> `com.health-tracker.scheduler`。

本指南将帮助你配置 Garmin 健康数据自动同步功能。

## 📋 前置要求

1. ✅ Garmin 中国账号（garmin.com.cn）
2. ✅ Garmin 手表（支持睡眠和 HRV 监测）
3. ✅ Python 3.10+ 环境
4. ✅ 已完成基础配置（Obsidian、Claude API）

---

## 🚀 快速开始

### 步骤 1: 安装依赖

```bash
cd /Users/taoli/andrewData/health-tracker
source venv/bin/activate
pip install -r requirements.txt
```

新增的依赖包括：
- `garth>=0.6.0` - Garmin 认证
- `garminconnect>=0.2.0` - Garmin API 客户端
- `APScheduler>=3.10.0` - 定时任务调度

### 步骤 2: 配置 Garmin 账号

编辑 `config/config.json`：

```json
{
  // ... 其他配置 ...

  "garmin_email": "your-garmin-email@example.com",
  "garmin_password": "your-garmin-password",
  "garmin_is_china": true,
  "garmin_sync_time": "12:00",
  "garmin_retry_hours": [13, 14, 15, 16],
  "garmin_required_fields": ["sleep_duration", "hrv"],

  "create_daily_note_if_missing": true,
  "health_log_section_start": "（健康日志）",
  "health_log_section_end": "（健康日志结束）",
  "analysis_folder": "Health/分析"
}
```

**配置说明：**
- `garmin_email`: Garmin 账号邮箱
- `garmin_password`: Garmin 密码
- `garmin_is_china`: 是否使用 Garmin 中国（通常为 true）
- `garmin_sync_time`: 每天自动同步时间（格式：HH:MM）
- `garmin_retry_hours`: 失败后重试的小时数列表
- `garmin_required_fields`: 必需的数据字段（缺失会报错）

### 步骤 3: 测试连接

```bash
python cli.py garmin-test
```

如果看到 "✓ Garmin 认证成功"，说明配置正确。

### 步骤 4: 手动同步测试

```bash
# 同步昨天的数据（默认）
python cli.py garmin-sync

# 同步指定日期
python cli.py garmin-sync --date 2026-02-27

# 同步今天的数据
python cli.py garmin-sync --date today
```

### 步骤 5: 启动自动调度器

#### 方式 A: 临时运行（测试）

```bash
python cli.py start-scheduler
```

按 `Ctrl+C` 停止。

#### 方式 B: 后台持续运行（推荐）

**macOS 使用 launchd：**

1. 创建配置文件 `~/Library/LaunchAgents/com.health-tracker.garmin.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.health-tracker.garmin</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/taoli/andrewData/health-tracker/venv/bin/python</string>
        <string>/Users/taoli/andrewData/health-tracker/cli.py</string>
        <string>start-scheduler</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/taoli/andrewData/health-tracker</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/Users/taoli/andrewData/health-tracker/logs/scheduler-out.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/taoli/andrewData/health-tracker/logs/scheduler-err.log</string>
</dict>
</plist>
```

2. 加载并启动：

```bash
launchctl load ~/Library/LaunchAgents/com.health-tracker.garmin.plist
launchctl start com.health-tracker.garmin
```

3. 检查状态：

```bash
launchctl list | grep health-tracker
tail -f logs/scheduler-out.log
```

4. 停止和卸载：

```bash
launchctl stop com.health-tracker.garmin
launchctl unload ~/Library/LaunchAgents/com.health-tracker.garmin.plist
```

---

## 📊 获取的数据

### 睡眠数据
- 总睡眠时长
- 深度睡眠时长
- REM 睡眠时长
- 浅睡眠时长
- 清醒时长
- 睡眠评分
- 入睡/醒来时间

### HRV 数据
- 昨晚 HRV 值
- 7天平均 HRV
- HRV 状态（balanced/unbalanced）

### 心率数据
- 静息心率
- 平均心率
- 最大心率

### 运动数据
- 运动类型（跑步、骑行、椭圆机等）
- 运动时长（分钟）
- 距离（公里）
- 卡路里消耗
- 平均/最大心率
- 开始时间

---

## 🔄 工作流程

### 每日自动流程

```
凌晨：手表上传数据到 Garmin 云端
  ↓
12:00：调度器触发
  ↓
1. Garmin 认证
  ↓
2. 获取昨晚睡眠、HRV、心率、运动数据
  ↓
3. 验证必需字段（睡眠 + HRV）
  ├─ 成功 → 继续
  └─ 失败 → 每小时重试（13:00-18:00）
  ↓
4. 保存到 SQLite 数据库
  ├─ health_records 表：睡眠、HRV、心率
  └─ exercises 表：运动记录
  ↓
5. 写入/更新当天的 Obsidian 日记
  ├─ Garmin 数据：自动填充（带 ✓ 标记）
  └─ 手动数据：保留占位符或已有内容
  ↓
6. 生成健康分析
  ├─ 7天简要分析 → 日记末尾
  └─ 30天详细分析 → 单独笔记（每周日）
  ↓
7. 同步到 Google Sheets（可选）
  ↓
8. 完成并记录日志
```

### Obsidian 日志示例

```markdown
# 2026-02-28

（健康日志）
日期：2026-02-28 时间：12:05
**晚餐与睡前**：
体重_kg：_（待填写）_
肌肉_kg：_（待填写）_
基础代谢：_（待填写）_
内脏脂肪等级：_（待填写）_
睡眠时长：8时 29分 ✓
深度睡眠：2时 14分 ✓
REM睡眠：1时 34分 ✓
静息心率_bpm：58 ✓
夜间平均心率_bpm：63 ✓
HRV_ms：39 ✓
夜间平均HRV_ms：41 ✓
夜间排尿次数：_（待填写）_
跟腱疼痛评分：_（待填写）_
晨僵时长_min：_（待填写）_
最疼部位：_（待填写）_
眼部不适：_（待填写）_

**运动记录**：
- 跑步 5.2km 30分钟 (平均心率 145bpm)
- 椭圆机 25分钟 (卡路里 280kcal)
（健康日志结束）

---

## 📊 健康趋势分析

### 近7天概况
- 睡眠质量：平均8.2小时
- HRV趋势：平均40ms（范围 38-42ms）
- 心率状态：静息58 bpm

详细分析：[[Health/分析/2026-02 健康分析]]
```

---

## ⚠️ 常见问题

### Q1: 数据获取失败怎么办？

**可能原因：**
1. Garmin 账号密码错误
2. 手表数据尚未上传到云端
3. 网络连接问题

**解决方法：**
1. 检查配置文件中的账号密码
2. 等待手表同步（通常在凌晨自动同步）
3. 手动在手表上触发同步
4. 系统会自动重试（12:00-18:00 每小时一次）

### Q2: 必需字段验证失败？

**错误信息：** "数据验证失败：缺少 睡眠时长, HRV"

**原因：** Garmin 云端暂时没有这些数据

**解决：**
- 等待手表上传数据（通常需要佩戴过夜）
- 系统会自动重试
- 或临时修改配置，移除必需字段检查：
  ```json
  "garmin_required_fields": []
  ```

### Q3: Obsidian 日记被覆盖了？

**不会的！** 系统只会更新健康日志部分：
- 查找 `（健康日志）...（健康日志结束）` 标记
- 只替换这部分内容
- 其他内容完全保留

### Q4: 可以手动填写体重等数据吗？

**可以！** 系统支持智能合并：
- **Garmin 数据**：睡眠、HRV、心率、运动 → 自动填充
- **手动数据**：体重、肌肉量、内脏脂肪等 → 你手动填写
- 两者互不干扰

### Q5: 如何查看同步日志？

```bash
# 实时查看日志
tail -f logs/garmin_scheduler.log

# 或查看最近的日志
cat logs/scheduler-out.log
```

### Q6: 能否同步多天的数据？

可以，但需要手动：

```bash
# 循环同步过去7天
for i in {1..7}; do
  date=$(date -v-${i}d +%Y-%m-%d)  # macOS
  python cli.py garmin-sync --date $date
  sleep 5
done
```

### Q7: 如何暂停自动同步？

```bash
# 临时停止（重启后恢复）
launchctl stop com.health-tracker.garmin

# 完全卸载
launchctl unload ~/Library/LaunchAgents/com.health-tracker.garmin.plist
```

---

## 🔐 安全建议

1. **保护配置文件**
   ```bash
   chmod 600 config/config.json
   ```

2. **不要提交敏感信息到 Git**
   - 已添加 `config/config.json` 到 `.gitignore`
   - 已添加 `data/garmin_tokens/` 到 `.gitignore`

3. **定期更换密码**
   - 更改 Garmin 密码后，更新配置文件
   - 删除 `data/garmin_tokens/` 下的旧令牌

---

## 📞 获取帮助

如有问题：
1. 查看 [FAQ.md](FAQ.md)
2. 检查日志文件 `logs/garmin_scheduler.log`
3. 提交 GitHub Issue

---

**开始享受自动化健康追踪吧！** 🎉

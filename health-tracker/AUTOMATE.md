# 自动定时同步配置指南

## 概述

设置每天自动执行 `parse + push`，无需手动操作。

**工作原理：**
1. 您在Obsidian写日记
2. Obsidian自动同步日记文件（iCloud/云盘）
3. 定时任务每天自动运行 `parse + push`
4. 数据自动提取并上传到Google Sheets

---

## 🍎 Mac配置（每天23:00自动运行）

### 步骤1：修改plist文件路径

编辑 `com.health-tracker.sync.plist`，确认路径正确：

```bash
# 找到这行，改成您的实际路径
<string>/Users/taoli/Documents/Hercules/health-tracker/sync-auto.sh</string>

# 同样修改日志路径
<string>/Users/taoli/Documents/Hercules/health-tracker/logs/launchd-out.log</string>
```

### 步骤2：安装定时任务

```bash
# 进入项目目录
cd ~/Documents/Hercules/health-tracker

# 赋予脚本执行权限
chmod +x sync-auto.sh

# 复制plist到系统目录
cp com.health-tracker.sync.plist ~/Library/LaunchAgents/

# 加载定时任务
launchctl load ~/Library/LaunchAgents/com.health-tracker.sync.plist

# 验证是否加载成功
launchctl list | grep health-tracker
```

### 步骤3：测试运行

```bash
# 手动触发一次测试
launchctl start com.health-tracker.sync

# 查看日志
tail -f logs/sync-$(date +%Y%m%d).log
```

### 卸载定时任务（如需要）

```bash
launchctl unload ~/Library/LaunchAgents/com.health-tracker.sync.plist
rm ~/Library/LaunchAgents/com.health-tracker.sync.plist
```

---

## 🪟 Windows配置（每天23:00自动运行）

### 步骤1：打开任务计划程序

1. 按 `Win + R`，输入 `taskschd.msc`，回车
2. 右侧点击 **"创建基本任务"**

### 步骤2：创建任务

**常规：**
- 名称：`健康数据自动同步`
- 描述：`每天自动解析健康日志并同步到云端`
- 勾选：**"不管用户是否登录都要运行"**
- 勾选：**"使用最高权限运行"**

**触发器：**
- 点击 **"新建"**
- 开始任务：**每天**
- 时间：**23:00**
- 启用：**勾选**

**操作：**
- 点击 **"新建"**
- 操作：**启动程序**
- 程序或脚本：`D:\claudecode\andrewData\health-tracker\sync-auto.bat`
- 起始于：`D:\claudecode\andrewData\health-tracker`

**条件：**
- 取消勾选：**"只有在计算机使用交流电源时才启动此任务"**
- 勾选：**"唤醒计算机运行此任务"**

**设置：**
- 勾选：**"允许按需运行任务"**
- 勾选：**"如果过了计划开始时间，立即启动任务"**

### 步骤3：测试运行

1. 在任务列表中找到 `健康数据自动同步`
2. 右键 → **运行**
3. 查看日志：`D:\claudecode\andrewData\health-tracker\logs\sync-YYYYMMDD.log`

---

## ⏰ 运行时间建议

| 时间 | 优点 | 缺点 |
|------|------|------|
| **23:00（推荐）** | 一天结束，数据完整 | 如果睡前还写日记会漏掉 |
| **00:30** | 确保当天数据完整 | 可能电脑已关机 |
| **每4小时** | 实时性好 | 占用资源，不必要 |

**推荐：23:00 + 手动同步**
- 定时任务：每天23:00自动同步
- 特殊情况：需要立即同步时运行 `hs`

---

## 📊 查看同步日志

**Mac：**
```bash
# 查看今天的日志
tail -f logs/sync-$(date +%Y%m%d).log

# 查看最近的日志
ls -lt logs/sync-*.log | head -5
```

**Windows：**
```powershell
# 查看今天的日志
Get-Content logs\sync-$(Get-Date -Format 'yyyyMMdd').log -Tail 20

# 查看所有日志
Get-ChildItem logs\sync-*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 5
```

---

## ⚠️ 注意事项

### 1. Obsidian同步延迟

如果您在PC上写日记，Mac上的Obsidian可能还没同步到最新文件：

```
PC上23:00写完日记
  → iCloud需要5-10分钟同步
  → Mac上23:00定时任务可能读取的是旧文件
```

**解决方案：**
- **方案A：** 定时任务设在00:30，给足同步时间
- **方案B：** 写完日记手动运行 `hs`（推荐）
- **方案C：** 在PC上也设置定时任务

### 2. 两个设备都设置定时任务

如果Mac和PC都设置了定时任务：

```
✅ 安全：
- PC上23:00运行 → push PC的数据
- Mac上23:05运行 → pull PC的数据 → push Mac的数据（如果有）

❌ 问题：
- 如果同一天在两个设备都写了不同内容
- 后运行的会覆盖先运行的
```

**解决方案：**
- 推荐只在主力设备设置定时任务
- 其他设备手动同步 `hsf`

### 3. 网络问题

定时任务需要网络连接才能推送到Google Sheets。

**建议：**
- 定时任务失败会记录在日志中
- 定期检查日志：`tail logs/sync-*.log`
- 网络恢复后手动运行 `hs` 补同步

---

## 🎯 推荐配置

### 主力设备（经常写日记的那台）

✅ 设置定时任务（23:00）
✅ 设置手动快捷命令 `hs`

**使用方式：**
- 平时写完日记：`hs`（立即同步）
- 忘记同步：定时任务兜底

### 次要设备

✅ 只设置手动快捷命令 `hsf`

**使用方式：**
- 切换到这个设备：先 `hsf`（拉取最新）
- 写完日记：`hs`（推送）

---

## 🔧 故障排查

### Mac: 定时任务没运行

```bash
# 检查是否加载
launchctl list | grep health-tracker

# 查看系统日志
tail -f logs/launchd-err.log

# 手动测试
launchctl start com.health-tracker.sync
```

### Windows: 定时任务失败

1. 打开任务计划程序
2. 找到任务 → 右键 → **属性**
3. 点击 **历史记录** 标签查看错误
4. 检查路径是否正确

### Python环境问题

确保虚拟环境路径正确：

```bash
# Mac
which python   # 应该显示 .../health-tracker/venv/bin/python

# Windows
where python   # 应该显示 ...\health-tracker\venv\Scripts\python.exe
```

---

## 总结

**配置后的工作流：**

```
您：写Obsidian日记 ✍️
  ↓
Obsidian：自动同步文件 🔄
  ↓
定时任务：23:00自动 parse + push 🤖
  ↓
Google Sheets：数据自动更新 ☁️
  ↓
您：随时随地查看数据 📊
```

**您只需要：写日记！** 🎉

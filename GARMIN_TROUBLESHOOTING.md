# Garmin 同步配置故障排除指南

## 问题诊断

您遇到的错误 `Error: No such command 'garmin-test'` 可能由以下原因导致：

### 1. 缺少依赖包

虽然您已安装了 Garmin 相关的包（garth, garminconnect, APScheduler），但 CLI 还需要其他依赖。

**解决方案：安装所有依赖**

```bash
cd /Users/taoli/andrewData/health-tracker
source venv/bin/activate
pip install -r requirements.txt
```

这将安装所有必需的包，包括：
- click（CLI 框架）
- rich（美化输出）
- anthropic（Claude API）
- 以及其他所有依赖

### 2. 工作目录错误

命令必须在 `health-tracker` 目录下运行。

**解决方案：确保在正确的目录**

```bash
cd /Users/taoli/andrewData/health-tracker
python cli.py --help
```

应该能看到所有可用命令的列表。

### 3. Python 路径问题

**解决方案：使用虚拟环境的 Python**

```bash
cd /Users/taoli/andrewData/health-tracker
source venv/bin/activate
python cli.py --help
```

## 完整的验证步骤

### 步骤 1：安装所有依赖

```bash
cd /Users/taoli/andrewData/health-tracker
source venv/bin/activate
pip install -r requirements.txt
```

### 步骤 2：验证安装

```bash
pip list | grep -E "click|rich|garth|garminconnect|APScheduler|anthropic"
```

应该看到：
- click >= 8.1.0
- rich >= 13.0.0
- garth >= 0.6.0
- garminconnect >= 0.2.0
- APScheduler >= 3.10.0
- anthropic >= 0.39.0

### 步骤 3：查看可用命令

```bash
python cli.py --help
```

应该能看到以下 Garmin 相关命令：
- `garmin-test` - 测试 Garmin 连接
- `garmin-sync` - 同步 Garmin 数据
- `start-scheduler` - 启动自动同步调度器

### 步骤 4：测试 Garmin 连接

```bash
python cli.py garmin-test
```

### 步骤 5：手动同步测试

```bash
python cli.py garmin-sync --date yesterday
```

## 常见错误及解决方案

### 错误 1：ModuleNotFoundError
```
ModuleNotFoundError: No module named 'xxx'
```

**解决：** 安装缺少的模块
```bash
pip install xxx
# 或者重新安装所有依赖
pip install -r requirements.txt
```

### 错误 2：配置文件错误
```
KeyError: 'garmin_email'
```

**解决：** 检查 `config/config.json` 包含以下配置：
```json
{
  "garmin_email": "your_email@example.com",
  "garmin_password": "your_password",
  "garmin_is_china": true,
  "garmin_sync_time": "09:00",
  "garmin_retry_hours": 3,
  "garmin_required_fields": ["sleep_duration", "hrv"],
  "obsidian_vault_path": "/path/to/vault",
  "health_log_section_start": "（健康日志）",
  "health_log_section_end": "（健康日志结束）",
  "create_daily_note_if_missing": true
}
```

### 错误 3：Garmin 认证失败
```
✗ Garmin 认证失败
```

**可能原因：**
1. 用户名或密码错误
2. 网络问题
3. Garmin 服务器问题
4. is_china 参数设置错误（国内用户应设为 true，国外用户设为 false）

**解决步骤：**
1. 检查 config.json 中的 garmin_email 和 garmin_password
2. 确认 garmin_is_china 设置正确
3. 尝试在 Garmin Connect 网站上登录验证账号
4. 检查网络连接

### 错误 4：数据不完整
```
⚠️  数据不完整，但仍会保存
```

**说明：** Garmin 可能还未同步完所有数据（通常发生在设备刚上传数据后）

**解决：**
1. 等待几小时后重试
2. 调整 `garmin_retry_hours` 配置
3. 或者接受不完整的数据

## 配置文件示例

### config/config.json 最小配置

```json
{
  "garmin_email": "your_email@example.com",
  "garmin_password": "your_password",
  "garmin_is_china": true,
  "garmin_sync_time": "09:00",
  "garmin_retry_hours": 3,
  "garmin_required_fields": ["sleep_duration", "hrv"],
  "obsidian_vault_path": "/Users/taoli/Documents/Obsidian/MyVault",
  "health_log_section_start": "（健康日志）",
  "health_log_section_end": "（健康日志结束）",
  "create_daily_note_if_missing": true,
  "database_path": "data/health_data.db",
  "claude_api_key": "your_api_key_here",
  "claude_model": "claude-3-5-sonnet-20241022"
}
```

## 下一步：设置自动同步

当手动测试成功后，可以设置自动同步：

### 方法 1：使用内置调度器（推荐）

```bash
# 启动调度器（会一直运行）
python cli.py start-scheduler
```

### 方法 2：使用 launchd（macOS 系统服务）

1. 创建 plist 文件：
```bash
nano ~/Library/LaunchAgents/com.health-tracker.garmin.plist
```

2. 粘贴以下内容：
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

3. 加载服务：
```bash
launchctl load ~/Library/LaunchAgents/com.health-tracker.garmin.plist
```

4. 管理命令：
```bash
# 启动
launchctl start com.health-tracker.garmin

# 停止
launchctl stop com.health-tracker.garmin

# 卸载
launchctl unload ~/Library/LaunchAgents/com.health-tracker.garmin.plist
```

## 检查日志

```bash
# 查看调度器输出日志
tail -f logs/scheduler-out.log

# 查看调度器错误日志
tail -f logs/scheduler-err.log

# 查看 Garmin 同步日志
tail -f logs/garmin_sync.log
```

## 需要帮助？

如果以上步骤都无法解决问题，请提供以下信息：

1. 完整的错误信息
2. `pip list` 的输出
3. `python cli.py --help` 的输出
4. config.json 的内容（隐藏敏感信息）

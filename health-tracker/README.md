# Health Tracking System

基于 Claude AI 的智能健康数据追踪系统

> 💡 **跨平台支持**: macOS、Windows、Linux 完全兼容

## ✨ 功能特点

- 📝 **自动解析 Obsidian 笔记** - 支持自然语言描述和图片截图
- 🏃 **Garmin 数据自动同步** - 每天自动获取睡眠、HRV、心率、运动数据
- 🧠 **Claude AI 智能提取** - 理解上下文，提取结构化数据
- 📸 **图片智能识别** - 自动识别体重秤、健身 APP 截图
- 💾 **本地 SQLite 存储** - 快速查询，离线可用
- ☁️ **Google Sheets 云同步** - 跨设备访问，数据备份
- 📊 **智能分析建议** - Claude 生成个性化健康洞察（7天/30天趋势）
- 💬 **智能问答** - 随时询问健康数据相关问题
- 🖥️ **跨平台** - macOS、Windows、Linux 全支持

## 🏗️ 系统架构

```
┌─────────────────────┐     ┌─────────────────────┐
│  Obsidian 笔记      │     │   Garmin 手表       │
│  (文本 + 图片)      │     │   (睡眠/HRV/运动)   │
└──────────┬──────────┘     └──────────┬──────────┘
           │                           │
           │  手动记录                 │  自动同步
           │                           │
           ▼                           ▼
    ┌──────────────────────────────────────┐
    │        Python 解析器 + AI 提取        │
    │  • Claude AI 智能理解                │
    │  • Garmin Client 数据获取            │
    └──────────────┬───────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────┐
    │      本地 SQLite 数据库               │
    │  • health_records (睡眠/HRV/心率)    │
    │  • exercises (运动记录)              │
    └──────────────┬───────────────────────┘
                   │
           ┌───────┴───────┐
           │               │
           ▼               ▼
    ┌─────────────┐  ┌──────────────┐
    │  Obsidian   │  │Google Sheets │
    │  自动写入    │  │  云端同步    │
    │  + AI 分析  │  │  跨设备访问  │
    └─────────────┘  └──────────────┘
```

## 🚀 快速开始

### 一键安装

#### macOS / Linux

```bash
# 1. 下载项目
git clone <repo-url>
cd health-tracker

# 2. 运行安装脚本
chmod +x install.sh
./install.sh

# 3. 编辑配置
nano config/config.json
# 填写 Claude API Key 和 Obsidian Vault 路径
```

#### Windows

```cmd
# 1. 下载项目
git clone <repo-url>
cd health-tracker

# 2. 运行安装脚本（双击）
install.bat

# 3. 编辑配置
notepad config\config.json
# 填写 Claude API Key 和 Obsidian Vault 路径
```

### 最小配置

只需在 `config/config.json` 中填写两项：

```json
{
  "claude_api_key": "sk-ant-你的API密钥",
  "obsidian_vault_path": "你的Obsidian笔记路径"
}
```

**获取 Claude API Key**: https://console.anthropic.com/

### 开始使用

```bash
# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 解析今天的笔记
python cli.py parse --date today

# 查看统计
python cli.py stats

# 生成周报
python cli.py report --period week

# 智能问答
python cli.py chat "为什么我这周体重没变化？"

# 获取个性化建议
python cli.py recommend --goal "减重5kg"

# 同步到 Google Sheets
python cli.py sync
```

### 使用快捷脚本

```bash
# macOS/Linux
./run.sh parse --date today

# Windows
run.bat parse --date today
```

## 项目结构

```
health-tracker/
├── parsers/          # Obsidian 笔记解析
├── extractors/       # Claude 数据提取
├── storage/          # SQLite 数据库操作
├── sync/             # Google Sheets 同步
├── garmin/           # Garmin 集成模块
│   ├── garmin_client.py     # Garmin 数据获取
│   ├── obsidian_writer.py   # Obsidian 自动写入
│   ├── health_analyzer.py   # 健康分析
│   └── scheduler.py         # 定时调度器
├── analytics/        # 数据分析和洞察
├── config/           # 配置文件
├── tests/            # 测试文件
├── cli.py            # 命令行接口
└── README.md         # 项目文档
```

## 数据结构

系统追踪以下健康指标：

- 体重、体脂率、肌肉量
- 睡眠时长、睡眠质量
- 运动类型、时长、强度
- 饮食记录
- 主观感受和备注

## 📖 文档

- **[QUICKSTART.md](QUICKSTART.md)** - 5 分钟快速上手
- **[INSTALLATION.md](INSTALLATION.md)** - 详细的跨平台安装指南
- **[SETUP.md](SETUP.md)** - 完整配置说明
- **[GARMIN_SETUP.md](GARMIN_SETUP.md)** - 🆕 Garmin 自动同步配置指南
- **[EXAMPLES.md](EXAMPLES.md)** - 10 个实际使用场景
- **[FAQ.md](FAQ.md)** - 常见问题解答
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - 贡献指南

## 💡 使用示例

### 在 Obsidian 中随意记录

```markdown
# 今天的健康

早上称重 68.5kg，体脂 23%，还不错！

昨晚睡得很好，11 点睡到早上 6:30，大概 7.5 小时。

下午跑步 5 公里，30 分钟，感觉很爽！

![体重秤](weight.jpg)
```

### Claude 自动提取数据

```json
{
  "date": "2025-10-25",
  "weight": 68.5,
  "body_fat_percentage": 23,
  "sleep_duration": 7.5,
  "exercises": [{
    "type": "跑步",
    "distance": 5,
    "duration": 30
  }]
}
```

### 获取智能分析

```markdown
# 本周健康报告

## 总体表现 ⭐⭐⭐⭐

这周做得很不错！体重稳步下降，运动频率保持良好...

## 关键指标
- 体重: 69.2kg → 68.5kg (-0.7kg) 📉
- 平均睡眠: 7.4 小时
- 运动次数: 5 次

## 建议
1. 保持当前的运动频率
2. 增加蛋白质摄入
3. 继续坚持！
```

## 🌟 特色功能

### 1. 自然语言理解

不需要严格格式，随意用自然语言描述：

```
今天 68.5 公斤，感觉轻了点
睡了大概 7 小时左右吧
晚上跑步 5 公里，累但很爽
```

Claude 都能理解并提取正确的数据！

### 2. 图片识别

支持识别各种健康相关截图：
- 体重秤显示
- 健身 APP 数据
- 睡眠监测报告
- 饮食热量统计

### 3. 智能分析

- **趋势分析**: 体重、睡眠、运动的变化趋势
- **相关性发现**: 睡眠和运动的关系、饮食和体重的关系
- **异常检测**: 自动发现健康风险
- **个性化建议**: 基于你的数据生成定制化建议

### 4. 跨设备同步

- 手机上用 Obsidian 记录
- 电脑上自动解析
- Google Sheets 云端查看
- 随时随地访问数据

## 🛠️ 技术栈

- **Python 3.8+** - 核心语言
- **Anthropic Claude API** - AI 智能提取和分析
- **SQLite** - 本地数据存储
- **Google Sheets API** - 云端同步
- **Rich** - 美化命令行输出
- **Click** - CLI 框架

## 🔒 隐私和安全

- ✅ **本地优先**: 数据首先存储在本地
- ✅ **加密传输**: API 调用使用 HTTPS
- ✅ **可选云端**: Google Sheets 同步完全可选
- ✅ **开源透明**: 所有代码可审查
- ✅ **无追踪**: 没有任何统计或追踪代码

## 💰 成本

- **Claude API**: 约 $1.5-3/月（日常使用）
- **Google Sheets**: 免费
- **其他**: 全部开源免费

## 🗺️ 开发计划

- [x] Obsidian 笔记解析
- [x] Claude 智能数据提取
- [x] 本地 SQLite 存储
- [x] Google Sheets 云同步
- [x] 智能分析和建议
- [x] 命令行接口
- [x] 跨平台支持
- [ ] 移动端 APP
- [ ] Web 界面
- [ ] Apple Health / Google Fit 集成
- [ ] 数据可视化仪表板

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 License

MIT License - 详见 [LICENSE](LICENSE)

## 🙏 致谢

- [Anthropic Claude](https://anthropic.com) - 强大的 AI 能力
- [Obsidian](https://obsidian.md) - 优秀的笔记工具
- 所有贡献者和使用者

---

**开始你的健康追踪之旅吧！** 🎉

有任何问题？查看 [FAQ](FAQ.md) 或提交 Issue。

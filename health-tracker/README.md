# Health Tracking System

基于 Claude AI 的智能健康数据追踪系统

## 功能特点

- 📝 **自动解析 Obsidian 笔记** - 支持自然语言描述和图片截图
- 🧠 **Claude AI 智能提取** - 理解上下文，提取结构化数据
- 💾 **本地 SQLite 存储** - 快速查询，离线可用
- ☁️ **Google Sheets 云同步** - 跨设备访问，数据备份
- 📊 **智能分析建议** - Claude 生成个性化健康洞察

## 系统架构

```
Obsidian笔记 → Python解析器 → Claude提取 → 本地SQLite → Google Sheets
                                    ↓
                               分析&建议生成
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

复制配置文件并填写必要信息：

```bash
cp config/config.example.json config/config.json
```

编辑 `config/config.json`：

```json
{
  "claude_api_key": "your-api-key",
  "obsidian_vault_path": "/path/to/your/vault",
  "google_sheets_credentials": "config/google-credentials.json",
  "google_sheet_id": "your-sheet-id"
}
```

### 3. 使用

```bash
# 解析今天的笔记
python cli.py parse --date today

# 解析指定日期
python cli.py parse --date 2025-10-25

# 同步到 Google Sheets
python cli.py sync

# 生成周报
python cli.py analyze --period week

# 交互式问答
python cli.py chat "为什么我这周体重没变化？"
```

## 项目结构

```
health-tracker/
├── parsers/          # Obsidian 笔记解析
├── extractors/       # Claude 数据提取
├── storage/          # SQLite 数据库操作
├── sync/             # Google Sheets 同步
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

## 开发计划

- [x] 项目架构设计
- [ ] Obsidian 解析器
- [ ] Claude 数据提取
- [ ] SQLite 存储
- [ ] Google Sheets 同步
- [ ] 分析和建议生成
- [ ] CLI 接口
- [ ] 单元测试

## License

MIT

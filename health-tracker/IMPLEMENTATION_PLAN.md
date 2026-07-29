# Garmin 健康助手集成实施计划

## 📋 项目概述

将 [garmin-health-assistant](https://github.com/andrew-tao-li/garmin-health-assistant) 项目功能集成到现有的健康追踪系统中，实现自动从 Garmin 中国云端获取数据并写入 Obsidian 和 Google Sheets。

## 🎯 核心需求

### 1. 自动数据同步
- **时间**：每天中午 12:00 自动执行
- **来源**：Garmin 中国云端 (garmin.com.cn)
- **数据**：
  - 睡眠报告（深度睡眠、REM、睡眠时长、睡眠评分）
  - HRV（心率变异性、周平均值、状态）
  - 心率（静息心率、夜间平均心率）
  - 运动记录（跑步、椭圆机、骑行等活动类型、时长、距离、卡路里、平均心率）
- **必需字段**：睡眠数据和 HRV（缺失必须报错）
- **可选字段**：运动数据（如当天无运动则为空）

### 2. 数据存储
- **SQLite**：本地数据库（主存储）
- **Google Sheets**：云端备份（按现有字段）
- **Obsidian 日记**：自动生成健康日志（如果日记不存在则创建）

### 3. 健康分析
- **7天趋势**：短期健康变化
- **30天趋势**：长期健康趋势
- **双重展示**：
  - 当天日记末尾：简要分析
  - 单独笔记：详细分析报告

### 4. 数据优先级
- **Garmin 数据优先**：睡眠、HRV、心率、运动记录
- **手动输入保留**：体重、肌肉量、内脏脂肪等身体成分
- **智能合并**：Garmin + 手动数据组合成完整记录
- **运动数据处理**：获取前一天的所有运动记录，自动写入数据库 exercises 表

### 5. 错误处理
- 12:00 首次尝试获取数据
- 如果失败，每小时重试一次（13:00, 14:00, ..., 18:00）
- 18:00 后仍失败则发送错误通知并停止重试
- 记录详细错误日志

---

## 🏗️ 架构设计

### 新增目录结构

```
health-tracker/
├── garmin/                    # 新增：Garmin 集成模块
│   ├── __init__.py
│   ├── garmin_client.py      # Garmin 数据获取客户端
│   ├── obsidian_writer.py    # Obsidian 写入功能
│   ├── health_analyzer.py    # 7天/30天健康分析
│   └── scheduler.py          # 定时任务调度器
├── config/
│   └── config.json           # 更新：添加 Garmin 配置
├── data/
│   └── garmin_tokens/        # 新增：Garmin 认证令牌
├── logs/
│   └── garmin-sync-*.log     # 新增：Garmin 同步日志
└── cli.py                    # 更新：添加 Garmin 命令
```

### 数据流图

```
                    ┌─────────────────┐
                    │  Garmin 中国云   │
                    │  (garmin.com.cn)│
                    └────────┬────────┘
                             │ 12:00 自动拉取
                             │ (每小时重试)
                    ┌────────▼────────┐
                    │ Garmin Client   │
                    │ (garth + API)   │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
    ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
    │   SQLite    │  │  Obsidian   │  │   Google    │
    │  Database   │  │   日记文件   │  │   Sheets    │
    └──────┬──────┘  └─────────────┘  └─────────────┘
           │
           │ 读取历史数据
           │
    ┌──────▼──────┐
    │Health       │
    │Analyzer     │
    │(AI 分析)    │
    └──────┬──────┘
           │
           │ 7天/30天趋势
           │
    ┌──────▼──────┐
    │  Obsidian   │
    │ 日记 + 分析  │
    └─────────────┘
```

---

## 🔧 实施步骤

### Phase 1: 环境准备

#### 1.1 依赖安装

**新增到 `requirements.txt`：**
```
# Garmin 集成
garth>=0.6.0
garminconnect>=0.2.0
APScheduler>=3.10.0
```

#### 1.2 配置文件更新

**更新 `config/config.example.json`：**
```json
{
  // ... 现有配置 ...

  "_comment_garmin": "Garmin 配置",
  "garmin_email": "your-garmin-email@example.com",
  "garmin_password": "your-garmin-password",
  "garmin_sync_time": "12:00",
  "garmin_retry_hours": [13, 14, 15, 16],
  "garmin_required_fields": ["sleep_duration", "hrv"],

  "_comment_obsidian_write": "Obsidian 写入配置",
  "obsidian_health_log_template": "templates/health_log_template.md",
  "obsidian_analysis_folder": "Health/分析",
  "create_daily_note_if_missing": true
}
```

### Phase 2: 核心模块开发

#### 2.1 Garmin 数据获取 (`garmin/garmin_client.py`)

**功能：**
- 使用 `garth` 进行身份认证（支持 Garmin 中国）
- 使用 `garminconnect` 获取健康数据
- 数据字段提取和格式化

**关键方法：**
```python
class GarminClient:
    def __init__(self, email, password)
    def authenticate()
    def get_sleep_data(date) -> dict
        # 返回：sleep_duration, deep_sleep, rem_sleep, sleep_score
    def get_hrv_data(date) -> dict
        # 返回：hrv, weekly_average, status
    def get_heart_rate_data(date) -> dict
        # 返回：resting_hr, average_hr, night_avg_hr
    def get_activities(date) -> list
        # 返回：运动记录列表
        # 每条记录：{type, duration, distance, calories, avg_hr, start_time}
    def get_today_summary(date) -> dict
        # 合并所有数据（睡眠 + HRV + 心率 + 运动）
    def validate_data(data) -> bool
        # 检查必需字段（睡眠和HRV）
```

#### 2.2 Obsidian 写入器 (`garmin/obsidian_writer.py`)

**功能：**
- 创建或更新 Obsidian 日记文件
- 生成健康日志内容（按用户模板格式）
- 添加健康分析内容

**关键方法：**
```python
class ObsidianWriter:
    def __init__(self, vault_path)
    def get_or_create_daily_note(date) -> Path
        # 获取或创建当天日记
    def write_health_log(date, data, mode='replace')
        # 写入健康日志（替换或合并）
    def append_analysis(date, analysis_text)
        # 在日记末尾添加分析
    def create_analysis_note(period, analysis_text)
        # 创建单独的分析笔记
```

**日志模板格式：**
```markdown
（健康日志）
日期：{date} 时间：{time}
**晚餐与睡前**：
体重_kg：{weight}
肌肉_kg：{muscle_mass}
基础代谢：{basal_metabolism}
内脏脂肪等级：{visceral_fat_level}
睡眠时长：{sleep_duration}
深度睡眠：{deep_sleep}
REM睡眠：{rem_sleep}
静息心率_bpm：{resting_hr}
夜间平均心率_bpm：{avg_hr}
HRV_ms：{hrv}
夜间平均HRV_ms：{avg_hrv}
夜间排尿次数：{urination_count}
跟腱疼痛评分：{pain_score}
晨僵时长_min：{stiffness_duration}
最疼部位：{pain_location}
眼部不适：{eye_symptoms}

**运动记录**：
{exercise_list}
（健康日志结束）
```

**运动记录格式：**
- 如有运动：显示列表，如 "跑步 5.2km 30分钟 (平均心率 145bpm)"
- 无运动：显示 "今日无运动记录"

#### 2.3 健康分析器 (`garmin/health_analyzer.py`)

**功能：**
- 读取数据库中的历史数据
- 使用 Claude AI 生成健康分析
- 生成简要和详细两种分析

**关键方法：**
```python
class HealthAnalyzer:
    def __init__(self, db, ai_client)
    def analyze_trends(days=7) -> dict
        # 分析 N 天趋势
    def generate_brief_summary(days) -> str
        # 生成简要分析（日记末尾）
    def generate_detailed_analysis(days) -> str
        # 生成详细分析（单独笔记）
    def identify_issues() -> list
        # 识别健康问题
```

#### 2.4 定时调度器 (`garmin/scheduler.py`)

**功能：**
- 使用 APScheduler 管理定时任务
- 实现重试逻辑
- 错误通知

**关键方法：**
```python
class GarminScheduler:
    def __init__(self, config)
    def start()
        # 启动调度器
    def schedule_daily_sync()
        # 每天 12:00 执行
    def sync_with_retry()
        # 同步数据（带重试）
    def handle_sync_failure(error)
        # 处理失败情况
```

### Phase 3: 数据库更新

#### 3.1 Schema 扩展

**新增字段到 `health_records` 表：**
```sql
ALTER TABLE health_records ADD COLUMN avg_heart_rate_night INTEGER;
ALTER TABLE health_records ADD COLUMN avg_hrv_night INTEGER;
ALTER TABLE health_records ADD COLUMN sleep_score INTEGER;
ALTER TABLE health_records ADD COLUMN garmin_synced BOOLEAN DEFAULT FALSE;
ALTER TABLE health_records ADD COLUMN garmin_sync_at TIMESTAMP;
```

#### 3.2 迁移脚本

创建 `migrations/add_garmin_fields.py`

### Phase 4: CLI 集成

#### 4.1 新增命令

**`cli.py` 添加：**
```python
@cli.command()
@click.option('--date', default='today', help='同步指定日期')
@click.option('--force', is_flag=True, help='强制重新同步')
def garmin_sync(date, force):
    """从 Garmin 同步健康数据"""
    # 实现同步逻辑

@cli.command()
def start_scheduler():
    """启动 Garmin 自动同步调度器"""
    # 启动后台调度任务

@cli.command()
def garmin_test():
    """测试 Garmin 连接"""
    # 测试认证和数据获取
```

### Phase 5: 自动化配置

#### 5.1 macOS 定时任务

**更新 `com.health-tracker.sync.plist`：**
```xml
<!-- 启动调度器（始终运行） -->
<key>KeepAlive</key>
<true/>
<key>RunAtLoad</key>
<true/>
```

#### 5.2 Windows 任务计划

创建 `install-scheduler.bat`

---

## 🔄 完整工作流程

### 每日自动流程

```
12:00 → 定时器触发
  ↓
1. Garmin 认证
  ↓
2. 获取昨晚睡眠数据
  ↓
3. 获取 HRV 数据
  ↓
4. 获取心率数据（静息心率、夜间平均心率）
  ↓
5. 获取运动记录（跑步、椭圆机等）
  ↓
6. 验证必需字段（睡眠 + HRV）
  ├─ 成功 → 继续
  └─ 失败 → 等待1小时重试
  ↓
7. 保存到 SQLite
  ├─ health_records 表：睡眠、HRV、心率
  └─ exercises 表：运动记录
  ↓
8. 检查当天 Obsidian 日记
  ├─ 存在 → 读取现有内容
  └─ 不存在 → 创建新日记
  ↓
9. 写入健康日志
  ├─ Garmin 数据：睡眠、HRV、心率、运动
  └─ 手动数据：体重等（保留或占位）
  ↓
10. 生成 7天/30天 分析
  ↓
11. 在日记末尾添加简要分析
  ↓
12. 创建/更新详细分析笔记
  ↓
13. 同步到 Google Sheets
  ├─ health_records 数据
  └─ exercises 数据
  ↓
14. 记录成功日志
```

### 错误重试流程

```
12:00 首次尝试
  ↓ 失败
13:00 第1次重试
  ↓ 失败
14:00 第2次重试
  ↓ 失败
...
18:00 最后一次重试
  ↓ 仍失败
发送错误通知 + 记录日志
```

---

## 📝 Obsidian 日志示例

### 当天日记 (2026-02-28.md)

```markdown
# 2026-02-28

... 用户的其他内容 ...

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
（健康日志结束）

---

## 📊 健康趋势分析

### 近7天概况
- 睡眠质量：优秀（平均8.2小时，深睡占比26%）
- HRV趋势：稳定（38-42ms）
- 心率状态：正常（静息58-60 bpm）

⚠️ **需要关注**：过去3天深度睡眠有下降趋势

详细分析：[[Health/分析/2026-02 健康分析]]
```

### 详细分析笔记 (Health/分析/2026-02 健康分析.md)

```markdown
# 2026年2月 健康分析报告

生成时间：2026-02-28 12:05

## 📈 7天趋势分析

### 睡眠质量
- **总时长**：平均 8.2 小时（目标 ✓）
- **深度睡眠**：平均 2.1 小时（占比 25.6%）
- **REM 睡眠**：平均 1.7 小时（占比 20.7%）
- **趋势**：深度睡眠在过去3天下降 12%

### HRV 分析
- **平均值**：40 ms
- **变化范围**：38-42 ms
- **状态**：稳定，处于正常范围

### 心率监测
- **静息心率**：58-60 bpm（优秀）
- **夜间心率**：62-65 bpm
- **趋势**：稳定

## 📊 30天趋势对比

（详细图表和分析）

## 💡 AI 建议

基于你的数据，Claude 建议：
1. 深度睡眠下降可能与...
2. 建议调整...

---

*本报告由 Health Tracker AI 自动生成*
```

---

## 🧪 测试计划

### 单元测试
- [ ] `garmin_client.py` - 数据获取
- [ ] `obsidian_writer.py` - 文件写入
- [ ] `health_analyzer.py` - 分析生成
- [ ] `scheduler.py` - 调度逻辑

### 集成测试
- [ ] Garmin 认证流程
- [ ] 完整同步流程
- [ ] 错误重试机制
- [ ] Obsidian 写入正确性

### 端到端测试
- [ ] 手动触发同步
- [ ] 自动定时同步
- [ ] 数据冲突处理
- [ ] Google Sheets 同步

---

## 📚 文档更新

### 新增文档
- [ ] `GARMIN_SETUP.md` - Garmin 配置指南
- [ ] `OBSIDIAN_TEMPLATE.md` - 日志模板说明

### 更新文档
- [ ] `README.md` - 添加 Garmin 功能介绍
- [ ] `AUTOMATE.md` - 更新自动化配置
- [ ] `FAQ.md` - 添加 Garmin 相关问答

---

## ✅ 验收标准

### 功能验收
- [x] 用户需求确认
- [ ] Garmin 数据成功获取
- [ ] Obsidian 日志正确生成
- [ ] Google Sheets 同步无误
- [ ] 健康分析准确生成
- [ ] 错误重试机制工作正常

### 质量验收
- [ ] 代码覆盖率 > 80%
- [ ] 无已知 Bug
- [ ] 文档完整
- [ ] 用户测试通过

---

## 🚀 部署计划

### 本地开发环境
1. 克隆项目
2. 安装新依赖
3. 配置 Garmin 账号
4. 运行测试

### 生产环境（Mac）
1. 更新代码
2. 安装依赖
3. 配置定时任务
4. 启动调度器

---

## ⏱️ 预计时间

| 任务 | 预计时间 |
|------|---------|
| Phase 1: 环境准备 | 30分钟 |
| Phase 2: 核心模块开发 | 3-4小时 |
| Phase 3: 数据库更新 | 30分钟 |
| Phase 4: CLI 集成 | 1小时 |
| Phase 5: 自动化配置 | 1小时 |
| 测试和调试 | 2小时 |
| 文档编写 | 1小时 |
| **总计** | **8-10小时** |

---

## 🔐 安全考虑

1. **Garmin 凭证**：
   - 不提交到 Git
   - 使用环境变量或加密存储
   - `.gitignore` 添加 `config/config.json` 和 `data/garmin_tokens/`

2. **数据隐私**：
   - 本地优先存储
   - Google Sheets 使用服务账号
   - 不上传敏感数据到公开仓库

---

## 📞 支持和反馈

如有任何问题或建议，请：
1. 提交 GitHub Issue
2. 查看 FAQ 文档
3. 联系维护者

---

**计划制定时间**：2026-02-28
**计划状态**：待审核
**下一步**：等待用户确认后开始实施

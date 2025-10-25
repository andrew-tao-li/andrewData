# 同步快速指南

## 🎯 5 分钟理解同步机制

### 核心概念（一句话）

**本地 SQLite 是你的主要工作空间，Google Sheets 是云端备份和查看工具。**

## 📊 简单对比

```
本地数据库 (SQLite)        Google Sheets
─────────────────────      ─────────────────
💾 存储在你的电脑上         ☁️  存储在 Google 云端
🚀 极快查询                🐌 需要网络，较慢
✍️  可以修改数据            👀 只用来查看
🏠 只能在本机访问           🌍 随处可访问
📱 手机不方便查看           📱 手机很方便

用途：                      用途：
- 日常数据存储              - 数据备份
- 快速查询统计              - 跨设备查看
- 离线使用                  - 创建图表
- Claude 分析               - 分享给他人
```

## 🔄 数据流向（简化版）

```
1. 写笔记 → 2. 解析 → 3. 保存本地 → 4. 同步云端
   ↓           ↓          ↓            ↓
Obsidian   Claude AI   SQLite      Google
  .md                   .db         Sheets
                                      ↓
                                   在手机上
                                    查看
```

## 💼 实际使用场景

### 场景 1: 每天晚上记录（最常见）

```bash
# 1. 在 Obsidian 写今天的笔记 (2分钟)
# 2. 解析到本地
python cli.py parse --date today    # ← 数据进入 SQLite

# 3. 查看统计
python cli.py stats                 # ← 从 SQLite 读取（快）

# 4. 不需要每天同步！
# Google Sheets 可以一周同步一次
```

### 场景 2: 周末回顾

```bash
# 1. 生成周报
python cli.py report --period week  # ← 从 SQLite 查询

# 2. 同步到云端（一周一次）
python cli.py sync --days 7         # ← 上传到 Google Sheets

# 3. 在手机上打开 Google Sheets
# 查看图表和数据
```

### 场景 3: 出差在外（离线）

```bash
# 情况：在飞机上，没有网络

# ✅ 可以做：
python cli.py show --date yesterday  # 查看本地数据
python cli.py stats                  # 查看统计
python cli.py report                 # 生成报告

# ❌ 不能做：
python cli.py sync                   # 需要网络

# 回家后：
python cli.py sync --all             # 补充同步
```

### 场景 4: 想在手机上快速查看

```
1. 在电脑上运行过至少一次: python cli.py sync
2. 在手机上打开 Google Sheets APP
3. 查看健康数据
4. 无需电脑，随时随地
```

## ❓ 常见疑问

### Q: 我需要每次都同步吗？

**A: 不需要！**

- ✅ 推荐：一周同步一次
- ✅ 或者：有重要数据时同步
- ❌ 不要：每次解析后都同步（浪费）

```bash
# 好的做法
python cli.py parse --date today    # 每天
python cli.py sync --days 7         # 每周日

# 不好的做法
python cli.py parse --date today
python cli.py sync                  # 立即同步（没必要）
```

### Q: 如果我在 Google Sheets 中改了数据会怎样？

**A: 会被覆盖！**

- Google Sheets 只是展示层
- 下次同步时本地数据会覆盖云端
- **所有修改都应该在本地进行**

```bash
# 正确的修改方式:
# 1. 修改 Obsidian 笔记
# 2. 重新解析
python cli.py parse --date 2025-10-25 --force

# 3. 重新同步
python cli.py sync --days 1
```

### Q: Google Sheets 可以完全不用吗？

**A: 可以！**

如果你：
- ✅ 只在一台电脑上使用
- ✅ 不需要在手机上查看
- ✅ 不需要分享数据
- ✅ 定期手动备份数据库文件

那么完全可以不用 Google Sheets。

### Q: 数据会丢吗？

**A: 三重保护！**

```
1. Obsidian 笔记（原始数据）
   └─ 可以用 Obsidian 自己的同步

2. SQLite 数据库（结构化数据）
   └─ 在你的电脑上
   └─ 可以手动复制备份

3. Google Sheets（云端备份）
   └─ Google 云端，自动备份
```

只要有任何一个，数据就不会丢。

## 🎨 Google Sheets 能做什么？

### 1. 查看数据

在手机或其他设备上查看最新的健康数据。

### 2. 创建图表

```
1. 选择 Date 和 Weight 列
2. 插入 → 图表 → 折线图
3. 得到体重趋势图
```

### 3. 自定义分析

```
// 计算平均值
=AVERAGE(B2:B30)

// 计算 BMI
=B2/(1.75^2)

// 条件格式
睡眠<7小时 → 红色
睡眠7-8小时 → 黄色
睡眠>8小时 → 绿色
```

### 4. 分享

```
1. 点击"分享"
2. 输入医生/教练的邮箱
3. 选择"查看者"权限
4. 发送
```

## 🔧 常用命令速查

```bash
# 解析笔记到本地
python cli.py parse --date today

# 查看本地数据（不需要网络）
python cli.py show --date today
python cli.py stats --days 30

# 生成报告（不需要网络）
python cli.py report --period week

# 同步到云端（需要网络）
python cli.py sync --days 7        # 同步最近7天
python cli.py sync --all           # 同步所有未同步的

# 备份本地数据库（可选）
cp health_data.db backup_$(date +%Y%m%d).db
```

## 💡 最佳实践

### 推荐工作流

**平日晚上** (5 分钟):
```
1. 在 Obsidian 写笔记
2. python cli.py parse --date today
```

**周末** (10 分钟):
```
1. python cli.py report --period week   # 看周报
2. python cli.py sync --days 7          # 同步到云端
3. 在手机上查看 Google Sheets
```

**每月** (可选):
```
1. 备份数据库: cp health_data.db backup.db
2. python cli.py sync --all  # 全量同步
```

## 🎯 记住这些要点

1. **本地是主力**: 所有数据先保存到 SQLite
2. **云端是备份**: Google Sheets 用于备份和查看
3. **不要频繁同步**: 一周一次足够
4. **不要在 Sheets 改数据**: 会被覆盖
5. **离线也能用**: 大部分功能不需要网络

## 📚 更多信息

- 详细说明: [docs/SYNC_EXPLAINED.md](SYNC_EXPLAINED.md)
- 演示脚本: `python examples/sync_example.py`
- 完整文档: [README.md](../README.md)

---

**还有疑问？** 查看 [FAQ.md](../FAQ.md) 或直接问我！

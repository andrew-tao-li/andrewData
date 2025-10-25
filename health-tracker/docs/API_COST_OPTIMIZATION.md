# Claude API 成本优化指南

## 💰 降低成本的策略

### 1. 批量处理

不要每次修改笔记都重新解析，而是一天解析一次：

```bash
# ❌ 不推荐：每次修改都解析
python cli.py parse --date today  # 第1次
# 修改笔记...
python cli.py parse --date today  # 第2次（重复调用）

# ✅ 推荐：一天结束时解析一次
# 晚上 11 点自动解析
```

### 2. 缓存机制

系统已经内置了缓存：
- 相同日期的记录不会重复解析（除非使用 `--force`）
- 分析结果保存在数据库中，可以直接查看

```bash
# 首次解析（调用 API）
python cli.py parse --date 2025-10-25

# 再次查看（不调用 API，从数据库读取）
python cli.py show --date 2025-10-25
```

### 3. 本地统计优先

使用本地统计而不是每次都问 Claude：

```bash
# ✅ 使用本地统计（免费）
python cli.py stats --days 30

# ❌ 不要频繁问 Claude 简单问题
python cli.py chat "我的平均体重是多少？"  # 浪费
```

### 4. 智能提问

只在需要深度分析时使用 `chat` 和 `report`：

```bash
# ✅ 有价值的问题
python cli.py chat "为什么我睡眠充足但白天还是困？分析睡眠质量和其他因素的关系"

# ❌ 简单问题（可以用 stats 查看）
python cli.py chat "我这周平均睡几小时？"
```

### 5. 图片处理

图片会增加成本（约 3-5 倍），优化策略：

```bash
# 选项 1：只在有重要图片时解析
# 如果笔记只有文字，暂时不附加图片

# 选项 2：定期批量处理图片
# 平时只解析文本，周末统一处理图片
```

### 6. 使用更便宜的模型

对于简单提取，可以使用 Claude 3 Haiku（便宜 20 倍）：

编辑 `config/config.json`：

```json
{
  "claude_model": "claude-3-haiku-20240307"
}
```

**Haiku 定价：**
- 输入：$0.25 / 百万 tokens
- 输出：$1.25 / 百万 tokens

**对比 Sonnet：**
- Sonnet：$3/$15
- Haiku：$0.25/$1.25（便宜 12-20 倍）

**建议：**
- 日常解析：用 Haiku（便宜）
- 深度分析：用 Sonnet（准确）

### 7. 定时任务控制

避免重复运行：

```bash
# ✅ 每天只运行一次
crontab -e
0 23 * * * cd /path/to/health-tracker && ./run.sh parse --date today

# ❌ 不要设置频繁的定时任务
# */30 * * * * ...  # 每 30 分钟（浪费）
```

## 📊 成本监控

### 1. 设置预算警报

在 Anthropic Console 中：
```
Settings → Billing → Set Budget Alert
设置：$5/月
```

达到阈值会收到邮件提醒。

### 2. 查看使用情况

```
https://console.anthropic.com/settings/usage
```

可以看到：
- 每日使用量
- 按 API Key 分组
- Token 使用明细

### 3. 本地使用日志

创建一个使用追踪脚本：

```python
# scripts/usage_tracker.py
import json
from datetime import datetime

def log_api_call(endpoint, tokens_in, tokens_out, cost):
    log_file = "api_usage.json"

    try:
        with open(log_file, 'r') as f:
            logs = json.load(f)
    except:
        logs = []

    logs.append({
        'timestamp': datetime.now().isoformat(),
        'endpoint': endpoint,
        'tokens_in': tokens_in,
        'tokens_out': tokens_out,
        'cost': cost
    })

    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2)
```

## 🎯 推荐配置

### 低成本配置（$0.5-1/月）

```json
{
  "claude_model": "claude-3-haiku-20240307",
  "parse_images": false,
  "daily_parse_only": true
}
```

使用方式：
- 只解析文本，不解析图片
- 每天解析一次
- 少用 `chat` 命令
- 每周生成一次报告

### 平衡配置（$1-2/月）

```json
{
  "claude_model": "claude-3-5-sonnet-20241022",
  "parse_images": true,
  "weekly_analysis": true
}
```

使用方式：
- 每天解析文本 + 图片
- 每周生成报告
- 偶尔使用 `chat`

### 重度使用（$3-5/月）

```json
{
  "claude_model": "claude-3-5-sonnet-20241022",
  "parse_images": true,
  "daily_reports": true
}
```

使用方式：
- 每天解析所有内容
- 频繁生成报告
- 经常使用 `chat`
- 仍然比 Pro 便宜！

## 💡 实用技巧

### 技巧 1：混合模型

不同任务用不同模型：

```python
# extractors/health_extractor.py 中修改

# 数据提取用 Haiku（便宜）
def extract_from_note(self, ...):
    self.model = "claude-3-haiku-20240307"
    ...

# 深度分析用 Sonnet（准确）
def analyze_trends(self, ...):
    self.model = "claude-3-5-sonnet-20241022"
    ...
```

### 技巧 2：离线模式

大部分功能都不需要 API：

```bash
# 不调用 API 的命令（完全免费）
python cli.py show --date today      # 查看数据
python cli.py stats --days 30        # 查看统计
python cli.py sync                   # 同步到 Sheets

# 调用 API 的命令（消耗 tokens）
python cli.py parse --date today     # 解析笔记
python cli.py report --period week   # 生成报告
python cli.py chat "..."             # 问答
```

### 技巧 3：预处理数据

如果笔记很长，先提取相关部分：

```bash
# ❌ 直接解析整个笔记（可能包含无关内容）
python cli.py parse --date today

# ✅ 在 Obsidian 中用标签标记
## 健康 #health
体重 68.5kg
睡眠 7.5 小时
...

## 其他内容
...
```

然后只提取 `#health` 部分，减少 token 使用。

## 📈 成本估算工具

创建一个估算器：

```python
# scripts/cost_estimator.py

def estimate_monthly_cost():
    """估算每月成本"""

    # 你的使用习惯
    daily_parses = 1          # 每天解析次数
    avg_note_length = 500     # 平均笔记字数
    images_per_day = 1        # 每天图片数
    weekly_reports = 1        # 每周报告次数
    chat_queries_per_week = 2 # 每周问答次数

    # Token 估算（粗略）
    tokens_per_parse = avg_note_length * 1.5  # 中文约 1.5 token/字
    tokens_per_image = 1000
    tokens_per_report = 5000
    tokens_per_chat = 3000

    # 每月 token 使用
    monthly_parse_tokens = daily_parses * tokens_per_parse * 30
    monthly_image_tokens = images_per_day * tokens_per_image * 30
    monthly_report_tokens = weekly_reports * tokens_per_report * 4
    monthly_chat_tokens = chat_queries_per_week * tokens_per_chat * 4

    total_input_tokens = (monthly_parse_tokens + monthly_image_tokens +
                          monthly_report_tokens + monthly_chat_tokens)

    # 假设输出是输入的 1/3
    total_output_tokens = total_input_tokens / 3

    # 成本计算（Sonnet）
    input_cost = (total_input_tokens / 1_000_000) * 3
    output_cost = (total_output_tokens / 1_000_000) * 15
    total_cost = input_cost + output_cost

    print(f"估算每月成本：${total_cost:.2f}")
    print(f"  输入 tokens: {total_input_tokens:,.0f}")
    print(f"  输出 tokens: {total_output_tokens:,.0f}")
    print(f"  输入成本: ${input_cost:.2f}")
    print(f"  输出成本: ${output_cost:.2f}")

if __name__ == '__main__':
    estimate_monthly_cost()
```

运行：
```bash
python scripts/cost_estimator.py
```

## 🎁 节省更多

### 1. 利用免费额度

Anthropic 有时会提供：
- 新用户注册奖励
- 促销活动
- 教育/研究折扣

### 2. 批量充值

充值更多可能有折扣（需确认最新政策）。

### 3. 共享账号

如果家人朋友也想用，可以共享一个 API Key（注意设置总预算）。

## 📌 总结

**最省钱的方式：**

1. 使用 Haiku 模型（日常）+ Sonnet 模型（分析）
2. 每天只解析一次
3. 多用本地统计，少问 Claude
4. 设置预算限制
5. 定期检查使用情况

**预期成本：**
- 极简使用：$0.30-0.50/月
- 正常使用：$1-2/月
- 重度使用：$3-5/月

都远低于 Claude Pro 的 $20/月！

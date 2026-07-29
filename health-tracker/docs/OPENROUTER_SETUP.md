# 使用 OpenRouter 的配置指南

## 什么是 OpenRouter？

[OpenRouter](https://openrouter.ai/) 是一个 AI API 聚合服务，提供：

- 🌐 统一接口访问多个 AI 模型（包括 Claude）
- 💰 可能更优惠的价格
- 📊 统一的计费和使用追踪
- 🔄 轻松切换不同模型

## ✅ 优点

### 与直接使用 Anthropic API 相比

| 特性 | Anthropic API | OpenRouter |
|------|--------------|-----------|
| **价格** | 官方价格 | 可能更便宜或有优惠 |
| **计费** | 单独账单 | 统一计费（如果用多个模型） |
| **访问速度** | 直连 | 经过代理（可能略慢） |
| **稳定性** | 官方支持 | 第三方服务 |
| **模型选择** | 仅 Claude | 多个模型可选 |

### OpenRouter 适合你如果：

- ✅ 已经有 OpenRouter 账号
- ✅ 希望统一管理多个 AI 服务
- ✅ 想要更灵活的模型选择
- ✅ 可能需要切换到其他模型

## 🔧 配置步骤

### 1. 获取 OpenRouter API Key

1. 访问 https://openrouter.ai/
2. 注册/登录账号
3. 进入 "Keys" 页面
4. 创建新的 API Key
5. 复制 API Key（格式：`sk-or-...`）

### 2. 修改配置文件

编辑 `config/config.json`，添加 OpenRouter 配置：

```json
{
  "use_openrouter": true,
  "openrouter_api_key": "sk-or-你的OpenRouter密钥",
  "openrouter_model": "anthropic/claude-sonnet-5",

  "obsidian_vault_path": "/path/to/vault",
  "database_path": "health_data.db"
}
```

**注意：** 如果设置了 `use_openrouter: true`，将忽略 `claude_api_key` 配置。

### 3. 修改代码支持 OpenRouter

我们需要修改提取器以支持 OpenRouter。

## 📝 代码修改

### 方法 1: 自动支持（推荐）

代码已经支持通过配置自动切换，只需更新配置文件即可。

### 方法 2: 手动修改

如果需要手动修改，编辑 `extractors/health_extractor.py`：

```python
# 在文件开头添加
import os

class HealthDataExtractor:
    def __init__(self, api_key: str, model: str = "claude-sonnet-5",
                 use_openrouter: bool = False):
        """
        初始化提取器

        Args:
            api_key: API密钥（Anthropic 或 OpenRouter）
            model: 模型名称
            use_openrouter: 是否使用 OpenRouter
        """
        self.model = model
        self.use_openrouter = use_openrouter

        if use_openrouter:
            # OpenRouter 配置
            from anthropic import Anthropic
            self.client = Anthropic(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
            # OpenRouter 模型名称格式
            if not model.startswith("anthropic/"):
                self.model = f"anthropic/{model}"
        else:
            # 原生 Anthropic API
            from anthropic import Anthropic
            self.client = Anthropic(api_key=api_key)
```

### CLI 适配

编辑 `cli.py`，修改提取器初始化部分：

```python
def load_config() -> dict:
    """加载配置文件"""
    config_path = Path(__file__).parent / "config" / "config.json"

    if not config_path.exists():
        console.print("[red]配置文件不存在[/red]")
        sys.exit(1)

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# 在需要创建 extractor 的地方：
config = load_config()

if config.get('use_openrouter', False):
    # 使用 OpenRouter
    api_key = config['openrouter_api_key']
    model = config.get('openrouter_model', 'anthropic/claude-sonnet-5')
    extractor = HealthDataExtractor(
        api_key=api_key,
        model=model,
        use_openrouter=True
    )
else:
    # 使用原生 Anthropic API
    api_key = config['claude_api_key']
    model = config.get('claude_model', 'claude-sonnet-5')
    extractor = HealthDataExtractor(
        api_key=api_key,
        model=model,
        use_openrouter=False
    )
```

## 🎯 OpenRouter 模型名称

OpenRouter 使用不同的模型命名格式：

| Anthropic 官方名称 | OpenRouter 名称 |
|-------------------|----------------|
| claude-sonnet-5 | anthropic/claude-sonnet-5 |
| claude-3-opus-20240229 | anthropic/claude-3-opus |
| claude-3-haiku-20240307 | anthropic/claude-3-haiku |

**配置示例：**

```json
{
  "use_openrouter": true,
  "openrouter_api_key": "sk-or-...",
  "openrouter_model": "anthropic/claude-sonnet-5"
}
```

## 💰 价格对比

### Anthropic 官方价格

**Claude Sonnet 4.6:**
- 输入: $3/百万 tokens
- 输出: $15/百万 tokens

**Claude 3 Haiku:**
- 输入: $0.25/百万 tokens
- 输出: $1.25/百万 tokens

### OpenRouter 价格

价格可能会变动，请访问 https://openrouter.ai/models 查看最新价格。

OpenRouter 的优势：
- 有时有促销活动
- 积分系统
- 批量使用折扣

## 🔍 验证配置

### 1. 测试 API 连接

创建测试脚本 `test_openrouter.py`：

```python
import json
from anthropic import Anthropic

# 加载配置
with open('config/config.json') as f:
    config = json.load(f)

# 测试 OpenRouter
client = Anthropic(
    api_key=config['openrouter_api_key'],
    base_url="https://openrouter.ai/api/v1"
)

try:
    response = client.messages.create(
        model=config['openrouter_model'],
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": "Hello, this is a test."
        }]
    )

    print("✅ OpenRouter 连接成功！")
    print(f"响应: {response.content[0].text}")

except Exception as e:
    print(f"❌ 连接失败: {e}")
```

运行测试：

```bash
python test_openrouter.py
```

### 2. 测试健康数据提取

```bash
# 使用 OpenRouter 解析笔记
python cli.py parse --date today
```

如果成功，说明 OpenRouter 配置正确！

## 🔄 切换回 Anthropic API

如果想切换回原生 Anthropic API：

```json
{
  "use_openrouter": false,
  "claude_api_key": "sk-ant-你的Anthropic密钥",
  "claude_model": "claude-sonnet-5"
}
```

或者直接删除 `use_openrouter` 字段（默认为 false）。

## 📊 使用监控

### OpenRouter 控制台

1. 访问 https://openrouter.ai/activity
2. 查看 API 使用情况
3. 追踪成本
4. 查看请求历史

### 本地记录

使用日志追踪：

```python
# 在 health_extractor.py 中添加
import logging

logging.basicConfig(filename='api_usage.log', level=logging.INFO)

def extract_from_note(self, ...):
    logging.info(f"API call: {self.model}, OpenRouter: {self.use_openrouter}")
    # ... 现有代码
```

## ⚠️ 注意事项

### 1. API 限制

OpenRouter 可能有不同的速率限制：
- 每分钟请求数
- 每天请求数
- 并发连接数

查看文档: https://openrouter.ai/docs

### 2. 响应格式

OpenRouter 返回的响应格式应该与 Anthropic 兼容，但如果遇到问题：

```python
# 添加错误处理
try:
    response = self.client.messages.create(...)
    result_text = response.content[0].text
except Exception as e:
    print(f"OpenRouter 错误: {e}")
    # 回退或重试逻辑
```

### 3. 图片处理

确认 OpenRouter 是否支持 Claude 的 Vision 功能：
- 某些 API 聚合服务可能不支持所有功能
- 测试图片识别是否正常工作

### 4. 延迟

OpenRouter 增加了一层代理，可能会有额外延迟：
- 通常在 100-300ms 范围内
- 对于批量处理影响不大

## 🎁 额外功能

### 切换到其他模型

OpenRouter 的优势是可以轻松切换模型：

```json
{
  "use_openrouter": true,
  "openrouter_api_key": "sk-or-...",
  "openrouter_model": "openai/gpt-4"
}
```

支持的模型：
- `anthropic/claude-sonnet-5`
- `anthropic/claude-3-opus`
- `openai/gpt-4-turbo`
- `openai/gpt-3.5-turbo`
- `google/gemini-pro`
- 等等...

### A/B 测试

可以创建两个配置对比效果：

```bash
# config_anthropic.json
{
  "use_openrouter": false,
  "claude_api_key": "sk-ant-..."
}

# config_openrouter.json
{
  "use_openrouter": true,
  "openrouter_api_key": "sk-or-..."
}
```

## 📚 参考资源

- OpenRouter 官网: https://openrouter.ai/
- OpenRouter 文档: https://openrouter.ai/docs
- 模型价格: https://openrouter.ai/models
- API 密钥管理: https://openrouter.ai/keys

## 🆘 故障排除

### 问题 1: "Invalid API Key"

**解决：**
```bash
# 检查 API Key 格式
# OpenRouter: sk-or-...
# Anthropic: sk-ant-...

# 确认配置文件中使用了正确的 key
cat config/config.json | grep api_key
```

### 问题 2: "Model not found"

**解决：**
```json
// 确保使用 OpenRouter 的模型名称格式
{
  "openrouter_model": "anthropic/claude-sonnet-5"  // ✅
  // 不是: "claude-sonnet-5"  // ❌
}
```

### 问题 3: 响应格式错误

**解决：**
```python
# 添加调试输出
print(f"Response type: {type(response)}")
print(f"Response content: {response}")
```

### 问题 4: 图片上传失败

**解决：**
- 检查 OpenRouter 是否支持 Vision API
- 尝试减小图片大小
- 查看 OpenRouter 文档的图片限制

## ✅ 总结

使用 OpenRouter：

**优点：**
- ✅ 统一管理多个 AI 服务
- ✅ 可能更优惠的价格
- ✅ 灵活切换模型
- ✅ 统一计费

**缺点：**
- ⚠️ 增加一层代理
- ⚠️ 可能有额外延迟
- ⚠️ 依赖第三方服务

**推荐：**
如果你已经有 OpenRouter 账号，完全可以使用！只需要简单的配置修改即可。

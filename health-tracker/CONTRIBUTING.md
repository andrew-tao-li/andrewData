# 贡献指南

感谢你对 Health Tracker 项目的兴趣！我们欢迎各种形式的贡献。

## 如何贡献

### 报告 Bug

如果你发现了 bug，请创建一个 Issue，包含：

1. **问题描述**：清晰描述问题
2. **重现步骤**：如何重现这个问题
3. **期望行为**：你期望发生什么
4. **实际行为**：实际发生了什么
5. **环境信息**：
   - Python 版本
   - 操作系统
   - 相关依赖版本

### 提出新功能

如果你有新功能的想法：

1. 先创建一个 Issue 讨论
2. 描述功能的用途和价值
3. 如果可能，提供设计方案
4. 等待社区反馈

### 提交代码

#### 1. Fork 项目

```bash
# Fork 项目到你的 GitHub 账号
# 然后克隆
git clone https://github.com/your-username/health-tracker.git
cd health-tracker
```

#### 2. 创建分支

```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

#### 3. 开发

- 遵循现有代码风格
- 添加必要的注释
- 编写或更新测试
- 更新文档

#### 4. 提交

```bash
git add .
git commit -m "描述你的更改"
```

提交信息格式：
- `feat: 添加新功能`
- `fix: 修复bug`
- `docs: 更新文档`
- `style: 代码格式调整`
- `refactor: 重构代码`
- `test: 添加测试`
- `chore: 其他更改`

#### 5. 推送并创建 Pull Request

```bash
git push origin feature/your-feature-name
```

然后在 GitHub 上创建 Pull Request。

## 代码规范

### Python 风格

遵循 PEP 8：

```python
# 好的例子
def parse_note(date: str) -> Optional[Dict[str, Any]]:
    """解析笔记文件

    Args:
        date: 日期字符串

    Returns:
        解析后的数据字典
    """
    pass

# 避免
def parse_note(date):
    pass
```

### 类型提示

尽可能使用类型提示：

```python
from typing import List, Dict, Optional, Any

def get_records(days: int) -> List[Dict[str, Any]]:
    pass
```

### 文档字符串

使用 Google 风格的文档字符串：

```python
def example_function(param1: str, param2: int) -> bool:
    """简短描述

    详细描述（如果需要）

    Args:
        param1: 参数1的描述
        param2: 参数2的描述

    Returns:
        返回值的描述

    Raises:
        ValueError: 什么情况下抛出
    """
    pass
```

### 测试

为新功能添加测试：

```python
def test_parse_note():
    """测试笔记解析"""
    parser = ObsidianParser("/path/to/vault")
    result = parser.parse_note(datetime.now())

    assert result is not None
    assert 'content' in result
    assert 'date' in result
```

## 开发环境设置

```bash
# 克隆项目
git clone https://github.com/your-username/health-tracker.git
cd health-tracker

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install pytest black flake8 mypy

# 运行测试
pytest tests/

# 代码格式化
black .

# 代码检查
flake8 .
mypy .
```

## 项目结构

```
health-tracker/
├── parsers/          # 数据解析模块
├── extractors/       # Claude 提取模块
├── storage/          # 数据存储模块
├── sync/             # 云同步模块
├── analytics/        # 数据分析模块
├── tests/            # 测试文件
├── config/           # 配置文件
├── cli.py            # 命令行接口
└── docs/             # 文档
```

## 贡献领域

### 优先级高的改进

1. **数据源扩展**
   - Apple Health 导入
   - Google Fit 集成
   - Fitbit 同步
   - 小米健康对接

2. **数据可视化**
   - 生成趋势图表
   - 交互式仪表板
   - 导出图表为图片

3. **移动端支持**
   - React Native 应用
   - 简化的移动 Web 界面

4. **自动化增强**
   - 自动识别笔记更新
   - 实时同步
   - 智能提醒

### 中等优先级

1. **多语言支持**
   - 英语界面
   - 其他语言

2. **高级分析**
   - 机器学习预测
   - 异常检测算法
   - 个性化建议引擎

3. **社交功能**
   - 数据分享
   - 好友对比
   - 社区挑战

### 长期目标

1. **Web 应用**
   - 完整的 Web 界面
   - 用户认证
   - 多租户支持

2. **企业版**
   - 团队健康管理
   - 企业仪表板
   - 健康报告生成

## 行为准则

- 尊重所有贡献者
- 友善、包容的沟通
- 接受建设性批评
- 关注对项目最有利的事

## 获取帮助

如有疑问：

1. 查看现有文档
2. 搜索类似的 Issues
3. 创建新 Issue 提问
4. 在讨论区交流

## 许可证

贡献的代码将在 MIT 许可证下发布。

## 致谢

感谢所有贡献者！你们的努力让这个项目变得更好。

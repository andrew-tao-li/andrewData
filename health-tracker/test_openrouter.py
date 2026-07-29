#!/usr/bin/env python3
"""
OpenRouter API 连接测试脚本

用于验证 OpenRouter 配置是否正确
"""

import json
import sys
from pathlib import Path
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from anthropic import Anthropic


def test_openrouter():
    """测试 OpenRouter API 连接"""

    print("=" * 60)
    print("OpenRouter API 连接测试")
    print("=" * 60)
    print()

    # 加载配置
    config_path = Path(__file__).parent / "config" / "config.json"

    if not config_path.exists():
        print("❌ 错误: 配置文件不存在")
        print(f"   请先创建: {config_path}")
        print("   可以从 config.example.json 复制")
        return False

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ 错误: 无法读取配置文件: {e}")
        return False

    # 检查配置
    if not config.get('use_openrouter'):
        print("⚠️  注意: use_openrouter 未设置为 true")
        print("   当前将测试 Anthropic API")
        print()

        if not config.get('claude_api_key'):
            print("❌ 错误: claude_api_key 未配置")
            return False

        api_key = config['claude_api_key']
        model = config.get('claude_model', 'claude-sonnet-5')
        base_url = None
        service_name = "Anthropic API"

    else:
        print("✓ 检测到 OpenRouter 配置")
        print()

        if not config.get('openrouter_api_key'):
            print("❌ 错误: openrouter_api_key 未配置")
            return False

        api_key = config['openrouter_api_key']
        model = config.get('openrouter_model', 'anthropic/claude-sonnet-5')
        base_url = "https://openrouter.ai/api/v1"
        service_name = "OpenRouter"

    # 显示配置信息
    print(f"服务: {service_name}")
    print(f"模型: {model}")
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
    if base_url:
        print(f"Base URL: {base_url}")
    print()

    # 测试连接
    print("正在测试 API 连接...")
    print()

    try:
        if base_url:
            # OpenRouter 使用 OpenAI SDK
            if not OPENAI_AVAILABLE:
                print("❌ 错误: 使用 OpenRouter 需要安装 openai 包")
                print("   请运行: pip install openai")
                return False

            client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                default_headers={
                    "HTTP-Referer": "https://github.com/health-tracker",
                    "X-Title": "Health Tracker"
                }
            )

            response = client.chat.completions.create(
                model=model,
                max_tokens=100,
                messages=[{
                    "role": "user",
                    "content": "Hello, please respond with '测试成功' in Chinese."
                }]
            )

            result_text = response.choices[0].message.content

        else:
            # Anthropic API
            client = Anthropic(api_key=api_key)

            response = client.messages.create(
                model=model,
                max_tokens=100,
                messages=[{
                    "role": "user",
                    "content": "Hello, please respond with '测试成功' in Chinese."
                }]
            )

            result_text = response.content[0].text

        print("✅ 连接成功！")
        print()
        print("测试响应:")
        print(f"  {result_text}")
        print()
        print("=" * 60)
        print("✓ OpenRouter 配置正确，可以正常使用！")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print()
        print("可能的原因:")
        print("  1. API Key 不正确")
        print("  2. 模型名称错误")
        print("  3. 网络连接问题")
        print("  4. API 余额不足")
        print()
        print("OpenRouter 模型名称格式:")
        print("  - anthropic/claude-sonnet-5")
        print("  - anthropic/claude-sonnet-4.6")
        print("  - anthropic/claude-sonnet-4.5")
        print("  - anthropic/claude-3-opus")
        print("  - anthropic/claude-3-haiku")
        print()
        print("查看更多信息:")
        print("  https://openrouter.ai/docs")
        print("  https://openrouter.ai/models")
        print()

        return False


def test_extraction():
    """测试健康数据提取"""

    print()
    print("=" * 60)
    print("测试健康数据提取")
    print("=" * 60)
    print()

    # 加载配置
    config_path = Path(__file__).parent / "config" / "config.json"

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 导入提取器
    sys.path.insert(0, str(Path(__file__).parent))
    from extractors import HealthDataExtractor

    # 创建提取器
    use_openrouter = config.get('use_openrouter', False)

    if use_openrouter:
        api_key = config['openrouter_api_key']
        model = config.get('openrouter_model', 'anthropic/claude-sonnet-5')
        fallback_models = config.get('openrouter_fallback_models', [])
        extractor = HealthDataExtractor(
            api_key=api_key,
            model=model,
            use_openrouter=True,
            fallback_models=fallback_models
        )
    else:
        api_key = config['claude_api_key']
        model = config.get('claude_model', 'claude-sonnet-5')
        extractor = HealthDataExtractor(
            api_key=api_key,
            model=model,
            use_openrouter=False
        )

    # 测试数据
    test_text = """
    今天早上体重 68.5kg，感觉不错！
    昨晚睡了 7.5 小时，质量挺好。
    下午跑步 5 公里，用了 30 分钟。
    """

    print("测试文本:")
    print(test_text)
    print()
    print("正在提取数据...")
    print()

    try:
        result = extractor.extract_from_note(
            text=test_text,
            date="2025-10-25"
        )

        if 'error' in result:
            print(f"❌ 提取失败: {result['error']}")
            return False

        print("✅ 提取成功！")
        print()
        print("提取的数据:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print()
        print("=" * 60)
        print("✓ 健康数据提取功能正常！")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"❌ 提取失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print()

    # 测试 API 连接
    if not test_openrouter():
        print()
        print("请修复上述问题后重试。")
        sys.exit(1)

    # 询问是否继续测试提取功能
    print()
    response = input("是否测试健康数据提取功能? (y/n): ").strip().lower()

    if response == 'y':
        if not test_extraction():
            sys.exit(1)

    print()
    print("所有测试完成！✨")
    print()

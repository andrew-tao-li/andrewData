#!/usr/bin/env python3
"""
调试数据提取脚本
查看实际提取到的内容
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from parsers import ObsidianParser
from extractors import HealthDataExtractor

def main():
    print("=" * 60)
    print("健康数据提取调试")
    print("=" * 60)
    print()

    # 加载配置
    config_path = Path(__file__).parent / "config" / "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 初始化 parser
    parser = ObsidianParser(
        config['obsidian_vault_path'],
        config.get('obsidian_health_folder', ''),
        health_section_start=config.get('health_section_start'),
        health_section_end=config.get('health_section_end')
    )

    # 解析今天的笔记
    today = datetime.now()
    note_data = parser.parse_note(today)

    if not note_data:
        print("❌ 未找到今天的笔记")
        return

    print(f"✓ 找到笔记: {note_data['file_path']}")
    print()

    # 显示提取的内容
    print("-" * 60)
    print("提取的内容（用于发送给 Claude）:")
    print("-" * 60)
    print(note_data['content'])
    print("-" * 60)
    print()

    print(f"内容长度: {len(note_data['content'])} 字符")
    print(f"是否有标记设置: start='{config.get('health_section_start')}', end='{config.get('health_section_end')}'")
    print()

    # 显示原始内容（前500字符）
    print("-" * 60)
    print("原始笔记内容（前500字符）:")
    print("-" * 60)
    original = note_data.get('original_content', '')
    print(original[:500])
    print("-" * 60)
    print()

    # 询问是否继续调用 API
    response = input("是否继续调用 Claude API 提取数据? (y/n): ").strip().lower()
    if response != 'y':
        print("调试结束")
        return

    # 创建 extractor
    use_openrouter = config.get('use_openrouter', False)
    if use_openrouter:
        api_key = config['openrouter_api_key']
        model = config.get('openrouter_model', 'anthropic/claude-3.5-sonnet')
        extractor = HealthDataExtractor(api_key=api_key, model=model, use_openrouter=True)
    else:
        api_key = config['claude_api_key']
        model = config.get('claude_model', 'claude-3-5-sonnet-20241022')
        extractor = HealthDataExtractor(api_key=api_key, model=model, use_openrouter=False)

    # 提取数据
    print()
    print("正在调用 Claude API...")
    print()

    result = extractor.extract_from_note(
        text=note_data['content'],
        images=[img['path'] for img in note_data.get('images', [])],
        date=note_data.get('date')
    )

    # 显示结果
    print("=" * 60)
    print("Claude 返回的原始结果:")
    print("=" * 60)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("=" * 60)
    print()

    # 检查是否有错误
    if 'error' in result:
        print(f"❌ 提取出错: {result['error']}")
    elif 'parsing_error' in result:
        print(f"❌ JSON 解析出错: {result['parsing_error']}")
        print(f"原始响应: {result.get('raw_response', 'N/A')}")
    else:
        print("✓ 提取成功")

        # 显示提取到的关键字段
        print()
        print("提取到的关键数据:")
        for key in ['weight', 'sleep_duration', 'heart_rate', 'mood', 'exercises', 'meals']:
            if key in result and result[key]:
                print(f"  - {key}: {result[key]}")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
测试图片数据提取功能

用于验证 Claude Vision API 是否正确识别健康数据截图
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from parsers import ObsidianParser
from extractors import HealthDataExtractor


def test_image_extraction():
    """测试图片数据提取"""

    print("=" * 60)
    print("图片数据提取测试")
    print("=" * 60)
    print()

    # 加载配置
    config_path = Path(__file__).parent / "config" / "config.json"

    if not config_path.exists():
        print("❌ 错误: 配置文件不存在")
        print(f"   请先创建: {config_path}")
        return False

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 初始化 parser
    parser = ObsidianParser(
        config['obsidian_vault_path'],
        config.get('obsidian_health_folder', ''),
        health_section_start=config.get('health_section_start'),
        health_section_end=config.get('health_section_end')
    )

    # 获取日期
    date_input = input("请输入要测试的日期 (YYYY-MM-DD) 或直接回车使用今天: ").strip()
    if date_input:
        try:
            test_date = datetime.strptime(date_input, "%Y-%m-%d")
        except ValueError:
            print("❌ 日期格式错误，使用今天")
            test_date = datetime.now()
    else:
        test_date = datetime.now()

    # 解析笔记
    print(f"\n正在解析 {test_date.strftime('%Y-%m-%d')} 的笔记...")
    note_data = parser.parse_note(test_date)

    if not note_data:
        print(f"❌ 未找到 {test_date.strftime('%Y-%m-%d')} 的笔记")
        print()
        print("💡 提示:")
        print("   1. 检查日期是否正确")
        print("   2. 检查 Obsidian vault 路径是否正确")
        print("   3. 检查笔记文件是否存在")
        return False

    print(f"✓ 找到笔记: {note_data['file_path']}")
    print()

    # 检查是否有图片
    if not note_data.get('images'):
        print("⚠️  笔记中没有找到图片")
        print()
        print("💡 如何在笔记中添加图片:")
        print("   方法1: ![描述](图片文件名.png)")
        print("   方法2: ![[图片文件名.png]]")
        print()
        print("支持的图片位置:")
        print("   - 与笔记同目录")
        print("   - Vault 根目录")
        print("   - attachments/ 文件夹")
        print("   - assets/ 文件夹")
        print("   - images/ 文件夹")
        return False

    # 显示找到的图片
    print(f"✓ 找到 {len(note_data['images'])} 张图片:")
    for i, img in enumerate(note_data['images'], 1):
        print(f"   {i}. {img['path']}")
        if img.get('alt_text'):
            print(f"      描述: {img['alt_text']}")
    print()

    # 验证图片文件是否存在
    missing_images = []
    for img in note_data['images']:
        img_path = Path(img['path'])
        if not img_path.exists():
            missing_images.append(img['path'])

    if missing_images:
        print("❌ 以下图片文件不存在:")
        for img in missing_images:
            print(f"   - {img}")
        print()
        print("💡 请检查图片路径是否正确")
        return False

    print("✓ 所有图片文件都存在")
    print()

    # 询问是否继续调用 API
    response = input("是否调用 Claude Vision API 识别图片? (y/n): ").strip().lower()
    if response != 'y':
        print("测试取消")
        return False

    # 创建 extractor
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
        extractor = HealthDataExtractor(api_key=api_key, model=model, use_openrouter=False)

    # 提取数据
    print()
    print("正在调用 Claude Vision API...")
    print(f"文本内容: {len(note_data['content'])} 字符")
    print(f"图片数量: {len(note_data['images'])} 张")
    print()

    result = extractor.extract_from_note(
        text=note_data['content'],
        images=[img['path'] for img in note_data.get('images', [])],
        date=note_data.get('date')
    )

    # 显示结果
    print("=" * 60)
    print("Claude Vision API 返回结果:")
    print("=" * 60)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("=" * 60)
    print()

    # 分析结果
    if 'error' in result:
        print(f"❌ 提取出错: {result['error']}")
        return False

    if 'parsing_error' in result:
        print(f"❌ JSON 解析出错: {result['parsing_error']}")
        print(f"原始响应: {result.get('raw_response', 'N/A')}")
        return False

    # 统计提取到的字段
    extracted_fields = [k for k, v in result.items() if v and k not in ['raw_text', 'processed_date', 'has_images', 'image_count']]

    print("✅ 提取成功!")
    print()
    print(f"提取到 {len(extracted_fields)} 个健康数据字段:")
    for field in extracted_fields:
        value = result[field]
        if isinstance(value, (list, dict)):
            print(f"  - {field}: {json.dumps(value, ensure_ascii=False)}")
        else:
            print(f"  - {field}: {value}")
    print()

    # 提供反馈
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"✓ 笔记解析: 成功")
    print(f"✓ 图片识别: {len(note_data['images'])} 张")
    print(f"✓ 数据提取: {len(extracted_fields)} 个字段")
    print()
    print("💡 如果数据提取不准确:")
    print("   1. 确保图片清晰可读")
    print("   2. 尝试裁剪图片只保留数据部分")
    print("   3. 可以同时提供文字说明")
    print()

    return True


if __name__ == '__main__':
    try:
        test_image_extraction()
    except KeyboardInterrupt:
        print("\n\n测试中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

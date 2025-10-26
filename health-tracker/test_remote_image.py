#!/usr/bin/env python3
"""
测试远程图片URL支持
"""

import json
from parsers.obsidian_parser import ObsidianParser

def test_remote_image():
    """测试远程图片识别"""

    # 加载配置
    with open('config/config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 创建解析器
    parser = ObsidianParser(
        vault_path=config['obsidian_vault_path'],
        health_folder=config.get('obsidian_health_folder', ''),
        health_section_start=config.get('health_section_start'),
        health_section_end=config.get('health_section_end')
    )

    # 解析笔记
    test_date = '2025-10-26'
    print(f"正在解析 {test_date} 的笔记...\n")

    note_data = parser.parse_note(test_date)

    # 显示结果
    print(f"笔记路径: {note_data.get('file_path', 'N/A')}")
    print(f"日期: {note_data.get('date', 'N/A')}")
    print(f"\n内容预览:")
    print("-" * 60)
    content = note_data.get('content', '')
    print(content[:300] + '...' if len(content) > 300 else content)
    print("-" * 60)

    print(f"\n找到的图片:")
    if note_data.get('images'):
        for i, img in enumerate(note_data['images'], 1):
            img_path = img['path']
            print(f"\n图片 {i}:")
            print(f"  路径: {img_path}")
            print(f"  Alt文本: {img.get('alt', 'N/A')}")

            # 检测是否为远程URL
            if img_path.startswith(('http://', 'https://')):
                print(f"  类型: ✓ 远程URL (将会下载)")
            else:
                print(f"  类型: 本地文件")
    else:
        print("  ⚠️  没有找到图片")
        print("\n请检查:")
        print("  1. 笔记中是否包含图片链接")
        print("  2. 图片是否在健康日志标记范围内")
        print("  3. 图片链接格式是否正确: ![alt text](图片URL)")

    return note_data

if __name__ == "__main__":
    test_remote_image()

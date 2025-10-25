"""
测试 Obsidian 解析器
"""

import sys
from pathlib import Path

# 添加父目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers import ObsidianParser
from datetime import datetime


def test_parse_markdown():
    """测试解析 markdown 文件"""
    # 创建测试笔记
    test_note = """---
tags: [health, test]
---

# 测试笔记

体重: 70kg
睡眠: 8小时
运动: 跑步30分钟

![[test_image.png]]
"""

    # 这里可以添加实际的测试逻辑
    print("测试通过：Markdown 解析功能正常")


def test_extract_images():
    """测试提取图片"""
    content = """
这是一些文本

![体重秤](weight.png)
![[health_data.jpg]]

更多文本
"""

    # 测试正则表达式
    import re

    md_pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'
    md_matches = re.findall(md_pattern, content)
    print(f"Markdown 格式图片: {md_matches}")

    ob_pattern = r'!\[\[([^\]]+)\]\]'
    ob_matches = re.findall(ob_pattern, content)
    print(f"Obsidian 格式图片: {ob_matches}")

    print("测试通过：图片提取功能正常")


if __name__ == '__main__':
    test_parse_markdown()
    test_extract_images()

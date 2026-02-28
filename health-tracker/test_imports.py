#!/usr/bin/env python3
"""
测试 Garmin 模块导入
"""

import sys

print("正在测试模块导入...")
print()

# 测试基本依赖
try:
    import click
    print("✓ click 导入成功")
except ImportError as e:
    print(f"✗ click 导入失败: {e}")
    sys.exit(1)

try:
    import rich
    print("✓ rich 导入成功")
except ImportError as e:
    print(f"✗ rich 导入失败: {e}")
    sys.exit(1)

# 测试 Garmin 模块
try:
    from garmin.garmin_client import GarminClient
    print("✓ garmin.garmin_client 导入成功")
except ImportError as e:
    print(f"✗ garmin.garmin_client 导入失败: {e}")
    print("   这可能导致 garmin-test 和 garmin-sync 命令无法加载")

try:
    from garmin.obsidian_writer import ObsidianWriter
    print("✓ garmin.obsidian_writer 导入成功")
except ImportError as e:
    print(f"✗ garmin.obsidian_writer 导入失败: {e}")

try:
    from garmin.health_analyzer import HealthAnalyzer
    print("✓ garmin.health_analyzer 导入成功")
except ImportError as e:
    print(f"✗ garmin.health_analyzer 导入失败: {e}")

try:
    from garmin.scheduler import GarminScheduler
    print("✓ garmin.scheduler 导入成功")
except ImportError as e:
    print(f"✗ garmin.scheduler 导入失败: {e}")
    print("   这可能导致 start-scheduler 命令无法加载")

print()
print("如果看到任何 ✗ 标记，说明存在导入问题")
print("这会导致相关的 CLI 命令无法注册")

#!/usr/bin/env python3
"""
同步机制演示示例

这个脚本演示本地数据库和 Google Sheets 的同步过程
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage import HealthDatabase


def demo_local_database():
    """演示本地数据库操作"""
    print("=" * 70)
    print("第 1 步: 本地数据库操作演示")
    print("=" * 70)
    print()

    db = HealthDatabase("demo_health_data.db")

    # 1. 添加一些示例数据
    print("📝 添加示例数据到本地数据库...")
    print()

    sample_data = [
        {
            "date": "2025-10-23",
            "weight": 70.0,
            "sleep_duration": 7.0,
            "exercises": [
                {"type": "跑步", "duration": 30, "distance": 5}
            ]
        },
        {
            "date": "2025-10-24",
            "weight": 69.5,
            "sleep_duration": 7.5,
            "exercises": [
                {"type": "游泳", "duration": 45}
            ]
        },
        {
            "date": "2025-10-25",
            "weight": 69.0,
            "sleep_duration": 8.0,
            "exercises": [
                {"type": "跑步", "duration": 35, "distance": 6},
                {"type": "力量训练", "duration": 30}
            ]
        }
    ]

    for data in sample_data:
        db.save_health_record(data)
        print(f"  ✓ 保存了 {data['date']} 的数据")

    print()
    print("💾 本地数据库状态:")
    print(f"  位置: demo_health_data.db")
    print(f"  记录数: {len(sample_data)}")
    print()

    # 2. 查询数据
    print("🔍 从本地数据库查询数据...")
    print()

    for data in sample_data:
        record = db.get_record_by_date(data['date'])
        print(f"  {record['date']}:")
        print(f"    体重: {record['weight']} kg")
        print(f"    睡眠: {record['sleep_duration']} 小时")
        print(f"    运动: {len(record['exercises'])} 项")

    print()

    # 3. 查看统计
    print("📊 本地统计数据:")
    stats = db.get_statistics(days=3)
    print(f"  平均体重: {stats['weight']['average']:.1f} kg")
    print(f"  体重变化: {stats['weight']['change']:+.1f} kg")
    print(f"  平均睡眠: {stats['sleep']['average_duration']:.1f} 小时")
    print(f"  总运动时长: {stats['exercise']['total_minutes']} 分钟")
    print()

    return db


def demo_sync_status(db):
    """演示同步状态"""
    print("=" * 70)
    print("第 2 步: 同步状态演示")
    print("=" * 70)
    print()

    # 查看未同步的记录
    unsynced = db.get_unsynced_records()

    print(f"📋 未同步到 Google Sheets 的记录: {len(unsynced)} 条")
    print()

    for record in unsynced:
        print(f"  ⏳ {record['date']}")
        print(f"     体重: {record['weight']} kg")
        print(f"     同步状态: 未同步")

    print()


def demo_sync_process():
    """演示同步过程（模拟）"""
    print("=" * 70)
    print("第 3 步: 同步过程演示（模拟）")
    print("=" * 70)
    print()

    print("🔄 模拟同步到 Google Sheets...")
    print()

    steps = [
        "1. 连接到 Google Sheets API",
        "2. 检查工作表是否存在",
        "3. 读取本地未同步的数据",
        "4. 对于每条记录:",
        "   - 检查 Sheets 中是否已存在该日期",
        "   - 如果存在，更新该行",
        "   - 如果不存在，添加新行",
        "5. 同步运动数据到 Exercises 工作表",
        "6. 同步饮食数据到 Meals 工作表",
        "7. 更新 Statistics 工作表",
        "8. 标记本地记录为已同步",
        "9. 同步完成！"
    ]

    import time
    for step in steps:
        print(f"  {step}")
        time.sleep(0.3)

    print()
    print("✅ 同步完成！数据已上传到 Google Sheets")
    print()


def demo_google_sheets_view():
    """演示 Google Sheets 视图"""
    print("=" * 70)
    print("第 4 步: Google Sheets 中的数据展示")
    print("=" * 70)
    print()

    print("📊 在 Google Sheets 中，你会看到：")
    print()

    # 工作表 1: Health Data
    print("工作表 1: Health Data")
    print("-" * 70)
    print(f"{'Date':<12} {'Weight':<10} {'Sleep':<10} {'Last Updated':<20}")
    print("-" * 70)
    print(f"{'2025-10-23':<12} {'70.0 kg':<10} {'7.0 h':<10} {'2025-10-25 23:00':<20}")
    print(f"{'2025-10-24':<12} {'69.5 kg':<10} {'7.5 h':<10} {'2025-10-25 23:00':<20}")
    print(f"{'2025-10-25':<12} {'69.0 kg':<10} {'8.0 h':<10} {'2025-10-25 23:00':<20}")
    print()

    # 工作表 2: Exercises
    print("工作表 2: Exercises")
    print("-" * 70)
    print(f"{'Date':<12} {'Type':<12} {'Duration':<12} {'Distance':<12}")
    print("-" * 70)
    print(f"{'2025-10-23':<12} {'跑步':<12} {'30 min':<12} {'5 km':<12}")
    print(f"{'2025-10-24':<12} {'游泳':<12} {'45 min':<12} {'-':<12}")
    print(f"{'2025-10-25':<12} {'跑步':<12} {'35 min':<12} {'6 km':<12}")
    print(f"{'2025-10-25':<12} {'力量训练':<12} {'30 min':<12} {'-':<12}")
    print()

    # 工作表 3: Statistics
    print("工作表 3: Statistics")
    print("-" * 70)
    print(f"{'Metric':<25} {'Value':<15} {'Period':<15}")
    print("-" * 70)
    print(f"{'Average Weight':<25} {'69.5 kg':<15} {'3 days':<15}")
    print(f"{'Weight Change':<25} {'-1.0 kg':<15} {'3 days':<15}")
    print(f"{'Average Sleep':<25} {'7.5 hours':<15} {'3 days':<15}")
    print(f"{'Total Exercise':<25} {'140 min':<15} {'3 days':<15}")
    print()


def demo_data_flow():
    """演示完整的数据流"""
    print("=" * 70)
    print("第 5 步: 完整数据流演示")
    print("=" * 70)
    print()

    flow = """
┌──────────────────────────────────────────────────────────────┐
│                    完整的数据流                                │
└──────────────────────────────────────────────────────────────┘

📝 你在 Obsidian 中写笔记
   ↓
   "今天体重 69kg，睡了 8 小时，跑步 6 公里"
   ↓

🤖 运行: python cli.py parse --date today
   ↓
   Claude AI 提取数据
   ↓
   {
     "date": "2025-10-25",
     "weight": 69.0,
     "sleep_duration": 8.0,
     "exercises": [{"type": "跑步", "distance": 6}]
   }
   ↓

💾 保存到本地 SQLite 数据库
   ↓
   health_data.db (在你的电脑上)
   ├── health_records 表
   ├── exercises 表
   └── meals 表
   ↓

📊 本地查询和分析 (离线可用)
   ├── python cli.py show --date today
   ├── python cli.py stats
   └── python cli.py report --period week
   ↓

🔄 运行: python cli.py sync
   ↓
   连接到 Google Sheets API
   ↓

☁️ 上传到 Google Sheets
   ↓
   https://docs.google.com/spreadsheets/d/你的ID
   ├── Health Data 工作表
   ├── Exercises 工作表
   ├── Meals 工作表
   └── Statistics 工作表
   ↓

📱 随时随地查看
   ├── 在电脑上打开 Google Sheets
   ├── 在手机上查看
   ├── 创建自定义图表
   └── 分享给他人

┌──────────────────────────────────────────────────────────────┐
│  关键点: 本地数据库是主数据源，Google Sheets 是备份和展示     │
└──────────────────────────────────────────────────────────────┘
    """

    print(flow)
    print()


def demo_comparison():
    """对比本地和云端"""
    print("=" * 70)
    print("第 6 步: 本地数据库 vs Google Sheets")
    print("=" * 70)
    print()

    comparison = """
┌─────────────────────┬────────────────────┬────────────────────┐
│      特性           │   本地 SQLite      │  Google Sheets     │
├─────────────────────┼────────────────────┼────────────────────┤
│  存储位置           │  你的电脑          │  Google 云端       │
│  访问速度           │  极快 (毫秒级)     │  较慢 (需要网络)   │
│  离线使用           │  ✅ 完全支持       │  ❌ 需要网络       │
│  数据修改           │  ✅ 主数据源       │  ⚠️ 仅供查看      │
│  跨设备访问         │  ❌ 仅当前电脑     │  ✅ 随处访问       │
│  手机查看           │  ❌ 不方便         │  ✅ 非常方便       │
│  数据备份           │  ⚠️ 需手动备份    │  ✅ 自动云备份     │
│  可视化             │  ❌ 需要代码       │  ✅ 内置图表       │
│  分享               │  ❌ 不方便         │  ✅ 一键分享       │
│  成本               │  免费              │  免费              │
│  数据安全           │  本地存储          │  Google 加密       │
├─────────────────────┼────────────────────┼────────────────────┤
│  推荐用途           │  主要工作空间      │  备份+展示层       │
│                     │  日常查询分析      │  跨设备查看        │
│                     │  离线使用          │  创建图表          │
│                     │                    │  分享数据          │
└─────────────────────┴────────────────────┴────────────────────┘

💡 最佳实践: 两者配合使用
   - 本地数据库: 存储和分析 (主力)
   - Google Sheets: 备份和展示 (辅助)
    """

    print(comparison)
    print()


def demo_cleanup():
    """清理演示数据"""
    import os
    if os.path.exists("demo_health_data.db"):
        os.remove("demo_health_data.db")
        print("🧹 已清理演示数据")
        print()


if __name__ == '__main__':
    print()
    print("=" * 70)
    print("  本地数据库与 Google Sheets 同步机制演示")
    print("=" * 70)
    print()
    print("这个演示将帮助你理解数据如何在本地和云端之间流动")
    print()

    input("按 Enter 键开始演示...")
    print()

    try:
        # 1. 本地数据库操作
        db = demo_local_database()

        input("\n按 Enter 键继续...")
        print()

        # 2. 同步状态
        demo_sync_status(db)

        input("\n按 Enter 键继续...")
        print()

        # 3. 同步过程
        demo_sync_process()

        input("\n按 Enter 键继续...")
        print()

        # 4. Google Sheets 视图
        demo_google_sheets_view()

        input("\n按 Enter 键继续...")
        print()

        # 5. 数据流
        demo_data_flow()

        input("\n按 Enter 键继续...")
        print()

        # 6. 对比
        demo_comparison()

        print()
        print("=" * 70)
        print("  演示完成！")
        print("=" * 70)
        print()
        print("📚 更多信息请查看: docs/SYNC_EXPLAINED.md")
        print()

    finally:
        # 清理
        demo_cleanup()

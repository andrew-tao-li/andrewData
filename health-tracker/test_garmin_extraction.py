#!/usr/bin/env python3
"""
测试 Garmin 数据提取
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from garmin.garmin_client import GarminClient


def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent / "config" / "config.json"

    if not config_path.exists():
        print(f"配置文件不存在: {config_path}")
        sys.exit(1)

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    # 加载配置
    config = load_config()

    # 创建客户端
    client = GarminClient(
        email=config.get('garmin_email'),
        password=config.get('garmin_password'),
        is_china=config.get('garmin_is_china', True)
    )

    # 认证
    if not client.authenticate():
        print("认证失败")
        return

    # 测试日期 - 今天
    test_date = datetime.now()
    print(f"\n{'='*80}")
    print(f"🧪 测试数据提取 - {test_date.strftime('%Y-%m-%d')}")
    print(f"{'='*80}\n")

    # 获取完整数据
    data = client.get_daily_summary(test_date)

    if not data:
        print("❌ 获取数据失败")
        return

    # 打印结果
    print("\n" + "="*80)
    print("📊 数据提取结果")
    print("="*80)

    print(f"\n日期: {data['date']}")

    # 睡眠数据
    if data.get('sleep'):
        sleep = data['sleep']
        print(f"\n😴 睡眠数据:")
        print(f"  总时长: {sleep.get('sleep_duration')} 小时")
        print(f"  深度睡眠: {sleep.get('deep_sleep_duration')} 小时")
        print(f"  浅睡眠: {sleep.get('light_sleep_duration')} 小时")
        print(f"  REM 睡眠: {sleep.get('rem_sleep_duration')} 小时")
        print(f"  清醒时间: {sleep.get('awake_duration')} 小时")
        print(f"  睡眠评分: {sleep.get('sleep_score')}")
        print(f"  平均血氧: {sleep.get('avg_spo2')}%")
        print(f"  平均呼吸率: {sleep.get('avg_respiration')} 次/分钟")
        print(f"  静息心率: {sleep.get('resting_heart_rate')} bpm")
    else:
        print(f"\n😴 睡眠数据: 无")

    # HRV 数据
    if data.get('hrv'):
        hrv = data['hrv']
        print(f"\n❤️  HRV 数据:")
        print(f"  昨晚 HRV: {hrv.get('hrv')}")
        print(f"  7天平均: {hrv.get('weekly_avg')}")
        print(f"  状态: {hrv.get('status')}")
    else:
        print(f"\n❤️  HRV 数据: 无")

    # 心率数据
    if data.get('heart_rate'):
        hr = data['heart_rate']
        print(f"\n💓 心率数据:")
        print(f"  静息心率: {hr.get('resting_heart_rate')} bpm")
    else:
        print(f"\n💓 心率数据: 无")

    # 运动数据
    if data.get('activities'):
        print(f"\n🏃 运动数据 ({len(data['activities'])} 条):")
        for i, activity in enumerate(data['activities'], 1):
            print(f"  {i}. {activity.get('type')} - {activity.get('duration')} 分钟")
            print(f"     距离: {activity.get('distance')} km")
            print(f"     卡路里: {activity.get('calories')}")
            print(f"     平均心率: {activity.get('avg_hr')} bpm")
    else:
        print(f"\n🏃 运动数据: 无")

    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    main()

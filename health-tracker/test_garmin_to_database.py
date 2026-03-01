#!/usr/bin/env python3
"""
测试 Garmin 数据提取并保存到数据库
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from garmin.garmin_client import GarminClient
from storage.sqlite_storage import HealthDatabase


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

    # 创建 Garmin 客户端
    try:
        client = GarminClient(
            email=config.get('garmin_email'),
            password=config.get('garmin_password'),
            is_china=config.get('garmin_is_china', True)
        )
    except ValueError as e:
        print(f"配置错误: {e}")
        return

    # 认证
    if not client.authenticate():
        print("认证失败")
        return

    # 测试日期 - 昨天
    test_date = datetime.now() - timedelta(days=1)
    print(f"\n{'='*80}")
    print(f"🧪 测试 Garmin → 数据库 - {test_date.strftime('%Y-%m-%d')}")
    print(f"{'='*80}\n")

    # 获取完整数据
    data = client.get_daily_summary(test_date)

    if not data:
        print("❌ 获取 Garmin 数据失败")
        return

    # 显示获取的数据
    print("\n" + "="*80)
    print("📊 从 Garmin 获取的数据")
    print("="*80)
    print(f"日期: {data['date']}")
    if data.get('sleep'):
        print(f"睡眠: {data['sleep'].get('sleep_duration')} 小时")
    if data.get('hrv'):
        print(f"HRV: {data['hrv'].get('hrv')}")
    if data.get('heart_rate'):
        print(f"静息心率: {data['heart_rate'].get('resting_heart_rate')} bpm")
    print()

    # 保存到数据库
    print("💾 保存到数据库...")
    db = HealthDatabase(config.get('database_path', 'health_data.db'))

    # 构造健康记录
    health_record = {
        'date': data['date'],
        'sleep_duration': data['sleep'].get('sleep_duration') if data.get('sleep') else None,
        'deep_sleep_duration': data['sleep'].get('deep_sleep_duration') if data.get('sleep') else None,
        'light_sleep_duration': data['sleep'].get('light_sleep_duration') if data.get('sleep') else None,
        'rem_sleep_duration': data['sleep'].get('rem_sleep_duration') if data.get('sleep') else None,
        'awake_duration': data['sleep'].get('awake_duration') if data.get('sleep') else None,
        'sleep_quality': data['sleep'].get('sleep_score') if data.get('sleep') else None,
        'hrv': data['hrv'].get('hrv') if data.get('hrv') else None,
        'resting_heart_rate': data['heart_rate'].get('resting_heart_rate') if data.get('heart_rate') else None,
    }

    # 保存健康记录
    if db.save_health_record(health_record):
        print("✅ 健康数据保存成功！")
    else:
        print("❌ 健康数据保存失败")
        return

    # 保存运动记录
    if data.get('activities'):
        print(f"\n保存 {len(data['activities'])} 条运动记录...")
        for activity in data['activities']:
            exercise_data = {
                'date': data['date'],
                'type': activity.get('type'),
                'duration': int(activity.get('duration', 0)),
                'distance': activity.get('distance'),
                'calories': activity.get('calories'),
            }
            db.save_exercise(exercise_data)
        print("✅ 运动记录保存成功！")
    else:
        print("\nℹ️  无运动记录")

    # 从数据库读取验证
    print("\n" + "="*80)
    print("🔍 从数据库读取验证")
    print("="*80)

    record = db.get_record_by_date(data['date'])
    if record:
        print(f"\n日期: {record.get('date')}")
        print(f"睡眠时长: {record.get('sleep_duration')} 小时")
        print(f"深度睡眠: {record.get('deep_sleep_duration')} 小时")
        print(f"浅睡眠: {record.get('light_sleep_duration')} 小时")
        print(f"REM 睡眠: {record.get('rem_sleep_duration')} 小时")
        print(f"清醒时间: {record.get('awake_duration')} 小时")
        print(f"睡眠质量: {record.get('sleep_quality')}")
        print(f"HRV: {record.get('hrv')}")
        print(f"静息心率: {record.get('resting_heart_rate')} bpm")
    else:
        print("❌ 从数据库读取失败")
        return

    print("\n" + "="*80)
    print("✅ Garmin → 数据库集成测试完成！")
    print("="*80)


if __name__ == "__main__":
    main()

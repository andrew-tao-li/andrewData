#!/usr/bin/env python3
"""
调试脚本 - 查看 Garmin API 返回的原始睡眠数据
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from garmin.garmin_client import GarminClient


def load_config():
    config_path = Path(__file__).parent / "config" / "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    config = load_config()

    client = GarminClient(
        email=config.get('garmin_email'),
        password=config.get('garmin_password'),
        is_china=config.get('garmin_is_china', True)
    )

    if not client.authenticate():
        print("认证失败")
        return

    # 获取昨天的原始睡眠数据
    test_date = datetime.now() - timedelta(days=1)
    date_str = test_date.strftime('%Y-%m-%d')

    print(f"\n{'='*80}")
    print(f"🔍 查看 {date_str} 的原始睡眠数据")
    print(f"{'='*80}\n")

    try:
        # 直接调用 API
        sleep_data = client.garmin.get_sleep_data(date_str)

        if sleep_data and 'dailySleepDTO' in sleep_data:
            daily_sleep = sleep_data['dailySleepDTO']

            print("📊 dailySleepDTO 中的睡眠相关字段：\n")

            # 检查所有睡眠阶段字段
            fields_to_check = [
                'sleepTimeSeconds',      # 总睡眠时间
                'deepSleepSeconds',      # 深度睡眠
                'lightSleepSeconds',     # 浅睡眠
                'remSleepSeconds',       # REM 睡眠
                'awakeSleepSeconds',     # 清醒时间
            ]

            for field in fields_to_check:
                value = daily_sleep.get(field)
                if value is not None:
                    hours = round(value / 3600, 2)
                    print(f"✓ {field:25} = {value:8} 秒 ({hours} 小时)")
                else:
                    print(f"✗ {field:25} = None (字段不存在)")

            # 显示所有可用字段
            print(f"\n\n📋 dailySleepDTO 中的所有字段：\n")
            for key in sorted(daily_sleep.keys()):
                value = daily_sleep[key]
                if isinstance(value, (int, float)):
                    print(f"  {key}: {value}")
                elif isinstance(value, str):
                    print(f"  {key}: {value[:50]}")
                elif isinstance(value, dict):
                    print(f"  {key}: {{...}} (字典)")
                else:
                    print(f"  {key}: {type(value).__name__}")

            # 保存完整 JSON 以供检查
            output_file = Path(__file__).parent / "debug_sleep_raw.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(sleep_data, f, indent=2, ensure_ascii=False)

            print(f"\n\n💾 完整的原始数据已保存到: {output_file}")

        else:
            print("❌ 未获取到睡眠数据")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

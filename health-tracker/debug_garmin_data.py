#!/usr/bin/env python3
"""
调试脚本：查看 Garmin API 返回的完整数据结构
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config.config import load_config
from garmin.garmin_client import GarminClient


def print_json(data, title):
    """漂亮地打印 JSON 数据"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main():
    # 加载配置
    config = load_config()
    garmin_config = config.get('garmin', {})

    # 创建客户端
    client = GarminClient(
        email=garmin_config['email'],
        password=garmin_config['password'],
        is_china=garmin_config.get('is_china', True)
    )

    # 认证
    if not client.authenticate():
        print("认证失败")
        return

    # 获取今天的日期
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")

    print(f"\n🔍 查看 {date_str} 的完整数据结构...\n")

    # 1. 睡眠数据完整结构
    try:
        sleep_raw = client.garmin.get_sleep_data(date_str)
        print_json(sleep_raw, "1️⃣  睡眠数据完整结构 (get_sleep_data)")
    except Exception as e:
        print(f"获取睡眠数据失败: {e}")

    # 2. 心率数据完整结构
    try:
        hr_raw = client.garmin.get_rhr_day(date_str)
        print_json(hr_raw, "2️⃣  心率数据完整结构 (get_rhr_day)")
    except Exception as e:
        print(f"获取心率数据失败: {e}")

    # 3. 活动数据完整结构
    try:
        activities_raw = client.garmin.get_activities_by_date(date_str, date_str, None)
        if activities_raw:
            print_json(activities_raw[0], "3️⃣  活动数据完整结构 (第一条活动)")
        else:
            print("\n⚠️  今天没有活动记录")
    except Exception as e:
        print(f"获取活动数据失败: {e}")

    # 4. HRV 数据完整结构
    try:
        hrv_raw = client.garmin.get_hrv_data(date_str)
        print_json(hrv_raw, "4️⃣  HRV 数据完整结构 (get_hrv_data)")
    except Exception as e:
        print(f"获取 HRV 数据失败: {e}")

    print(f"\n{'='*80}")
    print("✅ 数据结构查看完成！")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()

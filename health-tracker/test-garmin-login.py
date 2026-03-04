#!/usr/bin/env python3
"""
测试 Garmin 登录和数据获取
用于诊断调度器无法同步数据的问题
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from garmin.garmin_client import GarminClient


def test_garmin_connection():
    """测试 Garmin 连接"""
    print("=" * 80)
    print("🧪 Garmin 连接测试")
    print("=" * 80)
    print()

    # 1. 加载配置
    print("1️⃣ 加载配置...")
    try:
        config_path = Path(__file__).parent / "config" / "config.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"   ✅ 配置加载成功: {config_path}")
        print(f"   • Garmin账号: {config.get('garmin_email', 'N/A')}")
        print(f"   • 中国区: {config.get('garmin_is_china', True)}")
    except Exception as e:
        print(f"   ❌ 配置加载失败: {e}")
        return False
    print()

    # 2. 创建客户端
    print("2️⃣ 创建 Garmin 客户端...")
    try:
        client = GarminClient(
            email=config['garmin_email'],
            password=config['garmin_password'],
            is_china=config.get('garmin_is_china', True)
        )
        print("   ✅ 客户端创建成功")
    except Exception as e:
        print(f"   ❌ 客户端创建失败: {e}")
        return False
    print()

    # 3. 测试登录
    print("3️⃣ 测试登录...")
    try:
        user_info = client.get_user_info()
        if user_info:
            print("   ✅ 登录成功！")
            print(f"   • 用户信息: {user_info}")
        else:
            print("   ❌ 登录失败：未获取到用户信息")
            return False
    except Exception as e:
        print(f"   ❌ 登录失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    print()

    # 4. 测试获取昨天的数据
    print("4️⃣ 测试获取数据...")
    yesterday = datetime.now() - timedelta(days=1)
    date_str = yesterday.strftime('%Y-%m-%d')
    print(f"   目标日期: {date_str} (昨天)")
    try:
        data = client.get_daily_summary(yesterday)
        if data:
            print("   ✅ 数据获取成功！")
            print()
            print("   📊 数据摘要:")
            print(f"   • 日期: {data.get('date', 'N/A')}")

            # 睡眠数据
            if data.get('sleep'):
                sleep = data['sleep']
                print(f"   • 睡眠时长: {sleep.get('sleep_duration', 'N/A')} 分钟")
                print(f"   • 深睡时长: {sleep.get('deep_sleep_duration', 'N/A')} 分钟")
                print(f"   • REM睡眠: {sleep.get('rem_sleep_duration', 'N/A')} 分钟")
            else:
                print("   ⚠️  无睡眠数据")

            # HRV数据
            if data.get('hrv'):
                hrv = data['hrv']
                print(f"   • HRV (7天平均): {hrv.get('weekly_avg', 'N/A')}")
                print(f"   • HRV (昨晚): {hrv.get('hrv', 'N/A')}")
            else:
                print("   ⚠️  无HRV数据")

            # 心率数据
            if data.get('heart_rate'):
                hr = data['heart_rate']
                print(f"   • 静息心率: {hr.get('resting_heart_rate', 'N/A')}")
            else:
                print("   ⚠️  无心率数据")

            # 活动数据
            if data.get('activities'):
                print(f"   • 活动记录: {len(data['activities'])} 条")
                for activity in data['activities'][:3]:  # 只显示前3条
                    print(f"     - {activity.get('type', 'N/A')}: {activity.get('duration', 'N/A')}分钟")
            else:
                print("   • 活动记录: 0 条")

            # 5. 验证必需字段
            print()
            print("5️⃣ 验证数据完整性...")
            required_fields = config.get('garmin_required_fields', ['sleep_duration', 'hrv'])
            print(f"   必需字段: {required_fields}")

            is_valid = client.validate_data(data, required_fields)
            if is_valid:
                print("   ✅ 数据验证通过")
            else:
                print("   ❌ 数据验证失败：缺少必需字段")
                return False

        else:
            print("   ❌ 数据获取失败：未获取到数据")
            return False

    except Exception as e:
        print(f"   ❌ 数据获取失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    print()

    # 总结
    print("=" * 80)
    print("🎉 所有测试通过！")
    print("=" * 80)
    print()
    print("✅ Garmin 连接正常")
    print("✅ 数据获取正常")
    print("✅ 数据验证通过")
    print()
    print("💡 结论：Garmin 功能本身没有问题。")
    print("   如果调度器没有同步数据，问题可能出在：")
    print("   1. APScheduler 没有触发任务")
    print("   2. 任务被 misfire 跳过")
    print("   3. 异常被静默处理")
    print()
    return True


if __name__ == '__main__':
    try:
        success = test_garmin_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ 测试过程中出现未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

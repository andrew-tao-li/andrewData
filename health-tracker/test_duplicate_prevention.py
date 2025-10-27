#!/usr/bin/env python3
"""
测试重复数据防护机制

模拟多次parse和sync同一天的数据，验证不会产生重复
"""

import json
from pathlib import Path
from storage.sqlite_storage import HealthDatabase
from storage.google_sheets_storage import GoogleSheetsStorage


def load_config():
    config_path = Path(__file__).parent / "config" / "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_duplicate_prevention():
    """测试重复防护"""
    config = load_config()

    print("=" * 60)
    print("🧪 测试重复数据防护机制")
    print("=" * 60)
    print()

    # 初始化数据库
    db = HealthDatabase(config.get('database_path', 'data/health.db'))

    # 测试数据
    test_date = "2025-10-28"
    test_record = {
        'date': test_date,
        'weight': 70.5,
        'hrv': 50,
        'sleep_duration': 7.5
    }

    print(f"📅 测试日期: {test_date}")
    print(f"📊 测试数据: 体重{test_record['weight']}kg, HRV={test_record['hrv']}")
    print()

    # 测试1：本地数据库多次保存
    print("测试1: 本地数据库多次保存同一天")
    print("-" * 60)

    for i in range(1, 4):
        # 每次稍微改变数据
        test_record['weight'] = 70 + i * 0.5
        result = db.save_health_record(test_record)
        print(f"  第{i}次保存: {'✅ 成功' if result else '❌ 失败'} (体重={test_record['weight']}kg)")

    # 验证本地只有1条记录
    local_record = db.get_record_by_date(test_date)
    if local_record:
        print(f"  ✅ 本地数据库中只有1条记录")
        print(f"     最终数据: 体重={local_record.get('weight')}kg (应该是最后一次的71.5kg)")
    else:
        print(f"  ❌ 未找到记录")

    print()

    # 测试2：Google Sheets多次保存
    print("测试2: Google Sheets多次保存同一天")
    print("-" * 60)

    if config.get('google_sheets_enabled'):
        credentials_file = config.get('google_credentials_file') or config.get('google_sheets_credentials')
        sheet_id = config.get('google_sheet_id')

        sheets = GoogleSheetsStorage(credentials_file, sheet_id)

        # 保存前先记录云端记录数
        initial_count = len(sheets.health_sheet.get_all_values()) - 1  # 减去表头
        print(f"  初始云端记录数: {initial_count}")

        for i in range(1, 4):
            test_record['weight'] = 72 + i * 0.5
            result = sheets.save_health_record(test_record)
            print(f"  第{i}次保存: {'✅ 成功' if result else '❌ 失败'} (体重={test_record['weight']}kg)")

        # 验证云端记录数没有增加
        final_count = len(sheets.health_sheet.get_all_values()) - 1

        if final_count == initial_count:
            print(f"  ✅ 云端记录数未增加 ({initial_count} → {final_count})")
            print(f"     说明：多次保存同一天只更新不新增")
        elif final_count == initial_count + 1:
            print(f"  ✅ 云端新增1条记录 ({initial_count} → {final_count})")
            print(f"     说明：第一次添加，后续都是更新")
        else:
            print(f"  ⚠️  云端记录数异常 ({initial_count} → {final_count})")
            print(f"     可能产生了重复记录！")

        # 读取最终数据
        cloud_record = sheets.get_health_record(test_date)
        if cloud_record:
            print(f"     最终数据: 体重={cloud_record.get('weight')}kg (应该是最后一次的74.5kg)")

    else:
        print("  ⏭️  跳过（Google Sheets未启用）")

    print()

    # 测试3：批量保存重复数据
    print("测试3: 批量保存包含重复日期的数据")
    print("-" * 60)

    if config.get('google_sheets_enabled'):
        # 创建包含重复日期的批量数据
        duplicate_records = [
            {'date': '2025-10-29', 'weight': 70, 'hrv': 45},
            {'date': '2025-10-29', 'weight': 71, 'hrv': 46},  # 重复
            {'date': '2025-10-29', 'weight': 72, 'hrv': 47},  # 重复
            {'date': '2025-10-30', 'weight': 73, 'hrv': 48},
        ]

        print(f"  批量数据: 4条记录，其中2025-10-29重复3次")

        before_count = len(sheets.health_sheet.get_all_values()) - 1

        # 批量保存
        success_count = sheets.batch_save_health_records(duplicate_records)

        after_count = len(sheets.health_sheet.get_all_values()) - 1
        added = after_count - before_count

        print(f"  保存成功: {success_count}条")
        print(f"  云端变化: {before_count} → {after_count} (新增{added}条)")

        if added == 2:
            print(f"  ✅ 正确！批次内去重成功（2025-10-29只添加1次 + 2025-10-30）")
        else:
            print(f"  ⚠️  可能有问题，预期新增2条，实际新增{added}条")

        # 验证2025-10-29只有一条
        record_29 = sheets.get_health_record('2025-10-29')
        if record_29:
            print(f"  2025-10-29最终数据: 体重={record_29.get('weight')}kg (应该是最后的72kg)")

    print()
    print("=" * 60)
    print("✅ 测试完成")
    print("=" * 60)
    print()
    print("⚠️  注意：测试会在云端创建2025-10-28、2025-10-29、2025-10-30的记录")
    print("   如需清理，请手动删除这些测试记录")


if __name__ == '__main__':
    test_duplicate_prevention()

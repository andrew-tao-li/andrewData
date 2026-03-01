#!/usr/bin/env python3
"""
检查 Google Sheets 表头和数据行的字段对齐问题
"""

import sqlite3
from datetime import datetime

# 从 sheets_sync.py 中复制的表头定义
EXPECTED_HEADERS = [
    'date', 'weight', 'muscle_mass', 'body_fat_percentage', 'bmi',
    'basal_metabolism', 'visceral_fat_level', 'weight_feeling',
    'sleep_duration', 'sleep_start', 'sleep_end', 'sleep_quality',
    'deep_sleep_duration', 'light_sleep_duration', 'rem_sleep_duration', 'awake_duration', 'sleep_notes',
    'urination_count',
    'resting_heart_rate', 'heart_rate', 'hrv', 'blood_pressure', 'vo2_max',
    'rhr_baseline', 'hrv_baseline',
    'pain_score', 'pain_location', 'morning_stiffness_duration', 'symptoms',
    'mood', 'energy_level', 'overall_feeling',
    'steps', 'water_intake', 'health_notes',
    'created_at', 'updated_at'
]

# 从 sheets_sync.py 中复制的数据行字段顺序（第 149-187 行）
DATA_ROW_FIELDS = [
    'date', 'weight', 'muscle_mass', 'body_fat_percentage', 'bmi',
    'basal_metabolism', 'visceral_fat_level', 'weight_feeling',
    'sleep_duration', 'sleep_start', 'sleep_end', 'sleep_quality',
    'deep_sleep_duration', 'light_sleep_duration', 'rem_sleep_duration', 'awake_duration', 'sleep_notes',
    'urination_count',
    'resting_heart_rate', 'heart_rate', 'hrv', 'blood_pressure', 'vo2_max',
    'rhr_baseline', 'hrv_baseline',
    'pain_score', 'pain_location', 'morning_stiffness_duration', 'symptoms',
    'mood', 'energy_level', 'overall_feeling',
    'steps', 'water_intake', 'health_notes',
    'created_at', 'updated_at'
]

def main():
    print("=" * 100)
    print("检查 Google Sheets 字段对齐")
    print("=" * 100)

    # 检查字段数量
    print(f"\n表头字段数: {len(EXPECTED_HEADERS)}")
    print(f"数据字段数: {len(DATA_ROW_FIELDS)}")

    if len(EXPECTED_HEADERS) != len(DATA_ROW_FIELDS):
        print(f"\n❌ 字段数量不匹配！差异: {abs(len(EXPECTED_HEADERS) - len(DATA_ROW_FIELDS))}")
    else:
        print("\n✅ 字段数量匹配")

    # 检查字段顺序
    print("\n" + "=" * 100)
    print("逐一对比字段:")
    print("=" * 100)

    mismatches = []
    for i, (header, data_field) in enumerate(zip(EXPECTED_HEADERS, DATA_ROW_FIELDS), 1):
        if header != data_field:
            mismatches.append((i, header, data_field))
            print(f"❌ 位置 {i:2d}: 表头='{header}' != 数据='{data_field}'")
        else:
            if i <= 10 or i >= len(EXPECTED_HEADERS) - 5:  # 只显示前10个和后5个
                print(f"✅ 位置 {i:2d}: {header}")

    if mismatches:
        print(f"\n❌ 发现 {len(mismatches)} 个不匹配的字段!")
    else:
        print("\n✅ 所有字段完全匹配!")

    # 获取数据库中实际的一条记录
    print("\n" + "=" * 100)
    print("检查数据库记录:")
    print("=" * 100)

    conn = sqlite3.connect('health_data.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM health_records WHERE date = '2026-03-01' LIMIT 1")
    row = cursor.fetchone()

    if row:
        record = dict(row)
        print(f"找到 2026-03-01 的记录，包含 {len(record)} 个字段")

        # 模拟构建 row_data（和 sheets_sync.py 第 149-187 行一样）
        row_data = [
            record.get('date', ''),
            record.get('weight', ''),
            record.get('muscle_mass', ''),
            record.get('body_fat_percentage', ''),
            record.get('bmi', ''),
            record.get('basal_metabolism', ''),
            record.get('visceral_fat_level', ''),
            record.get('weight_feeling', ''),
            record.get('sleep_duration', ''),
            record.get('sleep_start', ''),
            record.get('sleep_end', ''),
            record.get('sleep_quality', ''),
            record.get('deep_sleep_duration', ''),
            record.get('light_sleep_duration', ''),
            record.get('rem_sleep_duration', ''),
            record.get('awake_duration', ''),
            record.get('sleep_notes', ''),
            record.get('urination_count', ''),
            record.get('resting_heart_rate', ''),
            record.get('heart_rate', ''),
            record.get('hrv', ''),
            record.get('blood_pressure', ''),
            record.get('vo2_max', ''),
            record.get('rhr_baseline', ''),
            record.get('hrv_baseline', ''),
            record.get('pain_score', ''),
            record.get('pain_location', ''),
            record.get('morning_stiffness_duration', ''),
            record.get('symptoms', ''),
            record.get('mood', ''),
            record.get('energy_level', ''),
            record.get('overall_feeling', ''),
            record.get('steps', ''),
            record.get('water_intake', ''),
            record.get('health_notes', ''),
            record.get('created_at', ''),
            record.get('updated_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        ]

        print("\n实际写入 Google Sheets 的数据:")
        print("-" * 100)
        for i, (header, value) in enumerate(zip(EXPECTED_HEADERS, row_data), 1):
            if value:  # 只显示非空值
                print(f"{i:2d}. {header:30s} = {value}")

        # 检查是否有空值导致偏移
        print("\n" + "=" * 100)
        print("检查空值:")
        print("=" * 100)
        empty_positions = []
        for i, (header, value) in enumerate(zip(EXPECTED_HEADERS, row_data), 1):
            if not value or value == '':
                empty_positions.append((i, header))

        if empty_positions:
            print(f"发现 {len(empty_positions)} 个空值字段:")
            for i, header in empty_positions:
                print(f"  位置 {i:2d}: {header}")
        else:
            print("✅ 没有空值字段")
    else:
        print("❌ 未找到 2026-03-01 的记录")

    conn.close()

if __name__ == '__main__':
    main()

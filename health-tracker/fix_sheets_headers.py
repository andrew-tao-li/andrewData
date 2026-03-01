#!/usr/bin/env python3
"""
修复 Google Sheets 表头对齐问题
强制更新表头为正确的顺序
"""

import json
import gspread
from google.oauth2.service_account import Credentials

# 正确的表头顺序
CORRECT_HEADERS = [
    'date', 'weight', 'muscle_mass', 'body_fat_percentage', 'bmi',
    'basal_metabolism', 'visceral_fat_level', 'weight_feeling',
    'sleep_duration', 'sleep_start', 'sleep_end', 'sleep_quality',
    'deep_sleep_duration', 'light_sleep_duration', 'rem_sleep_duration', 'awake_duration', 'sleep_notes',
    'urination_count',
    'resting_heart_rate', 'heart_rate', 'hrv', 'hrv_night', 'blood_pressure', 'vo2_max',
    'rhr_baseline', 'hrv_baseline',
    'pain_score', 'pain_location', 'morning_stiffness_duration', 'symptoms',
    'mood', 'energy_level', 'overall_feeling',
    'steps', 'water_intake', 'health_notes',
    'created_at', 'updated_at'
]

def main():
    # 加载配置
    with open('config/config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 连接 Google Sheets
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(
        config['google_credentials_file'],
        scopes=scopes
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(config['google_sheet_id'])
    worksheet = spreadsheet.worksheet('健康记录')

    # 获取当前表头
    current_headers = worksheet.row_values(1)

    print("=" * 100)
    print("Google Sheets 表头修复工具")
    print("=" * 100)

    print(f"\n当前表头字段数: {len(current_headers)}")
    print(f"正确表头字段数: {len(CORRECT_HEADERS)}")

    # 对比表头
    if current_headers == CORRECT_HEADERS:
        print("\n✅ 表头已经是正确的，无需修复!")
        return

    print("\n❌ 表头不匹配，需要修复!")

    # 显示差异
    print("\n" + "=" * 100)
    print("表头差异:")
    print("=" * 100)

    max_len = max(len(current_headers), len(CORRECT_HEADERS))
    for i in range(min(max_len, 30)):  # 只显示前30个
        current = current_headers[i] if i < len(current_headers) else "缺失"
        correct = CORRECT_HEADERS[i] if i < len(CORRECT_HEADERS) else "多余"

        if current != correct:
            print(f"位置 {i+1:2d}: 当前='{current}' -> 正确='{correct}'")

    # 询问是否修复
    print("\n" + "=" * 100)
    response = input("是否更新表头? (y/n): ")

    if response.lower() != 'y':
        print("已取消")
        return

    # 更新表头
    print("\n正在更新表头...")

    # 使用新的 API 调用方式 + 重试机制
    max_retries = 3
    for attempt in range(max_retries):
        try:
            worksheet.update(values=[CORRECT_HEADERS], range_name='A1')
            print("✅ 表头已更新!")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                import time
                print(f"尝试 {attempt + 1} 失败，2秒后重试...")
                time.sleep(2)
            else:
                print(f"❌ 更新失败: {e}")
                print("\n手动修复方案:")
                print("1. 打开 Google Sheets")
                print("2. 在表头第 14 列（N列）插入一列")
                print("3. 将新列的表头设置为: light_sleep_duration")
                return

    # 验证
    new_headers = worksheet.row_values(1)
    if new_headers == CORRECT_HEADERS:
        print("✅ 验证通过: 表头已正确更新")
    else:
        print("❌ 验证失败: 表头更新可能有问题")
        print(f"   当前: {len(new_headers)} 个字段")
        print(f"   预期: {len(CORRECT_HEADERS)} 个字段")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
清理 Google Sheets 中的重复记录

保留每个日期的第一条记录，删除重复的
"""

import json
from pathlib import Path
from storage.google_sheets_storage import GoogleSheetsStorage


def load_config():
    """加载配置"""
    config_path = Path(__file__).parent / "config" / "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def remove_duplicates():
    """清理重复记录"""
    config = load_config()

    # 初始化 Google Sheets
    sheets = GoogleSheetsStorage(
        credentials_file=config['google_credentials_file'],
        spreadsheet_id=config['google_sheet_id']
    )

    print("🔍 检查重复记录...")
    print()

    # 获取所有记录
    all_values = sheets.health_sheet.get_all_values()

    if len(all_values) <= 1:
        print("✅ 没有数据")
        return

    headers = all_values[0]
    date_col_index = 0  # 日期列是第一列

    # 记录每个日期第一次出现的行号
    seen_dates = {}
    duplicates = []

    for row_num, row_values in enumerate(all_values[1:], start=2):
        if not row_values or not row_values[0]:
            continue

        date_str = row_values[0]

        if date_str in seen_dates:
            # 发现重复
            duplicates.append({
                'date': date_str,
                'row': row_num,
                'first_row': seen_dates[date_str]
            })
        else:
            seen_dates[date_str] = row_num

    if not duplicates:
        print("✅ 没有发现重复记录")
        return

    print(f"⚠️  发现 {len(duplicates)} 条重复记录：")
    print()

    # 按日期分组显示
    from collections import defaultdict
    dup_by_date = defaultdict(list)
    for dup in duplicates:
        dup_by_date[dup['date']].append(dup['row'])

    for date, rows in sorted(dup_by_date.items()):
        print(f"  📅 {date}: 第 {seen_dates[date]} 行（保留）, 第 {', '.join(map(str, rows))} 行（删除）")

    print()

    # 确认删除
    response = input("是否删除重复记录？(y/n): ")
    if response.lower() != 'y':
        print("❌ 已取消")
        return

    print()
    print("🗑️  开始删除重复记录...")

    # 从后往前删除（避免行号变化）
    duplicates_sorted = sorted(duplicates, key=lambda x: x['row'], reverse=True)

    deleted_count = 0
    for dup in duplicates_sorted:
        try:
            sheets.health_sheet.delete_rows(dup['row'])
            deleted_count += 1
            print(f"  ✅ 删除第 {dup['row']} 行 ({dup['date']})")
        except Exception as e:
            print(f"  ❌ 删除第 {dup['row']} 行失败: {e}")

    print()
    print(f"✅ 完成！共删除 {deleted_count} 条重复记录")

    # 验证
    print()
    print("🔍 验证结果...")
    all_values_after = sheets.health_sheet.get_all_values()
    dates_after = [row[0] for row in all_values_after[1:] if row and row[0]]
    unique_dates = set(dates_after)

    print(f"  总记录数: {len(dates_after)}")
    print(f"  唯一日期数: {len(unique_dates)}")

    if len(dates_after) == len(unique_dates):
        print("  ✅ 所有日期唯一，去重成功！")
    else:
        print(f"  ⚠️  仍有 {len(dates_after) - len(unique_dates)} 条重复")


if __name__ == '__main__':
    remove_duplicates()

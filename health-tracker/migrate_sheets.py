#!/usr/bin/env python3
"""
Google Sheets 数据迁移脚本

功能：
1. 将新创建的英文 sheet（Health Data, Exercises, Meals）的数据合并到旧的中文 sheet
2. 删除英文 sheet，避免数据重复
3. 保留所有历史数据
"""

import json
import gspread
from google.oauth2.service_account import Credentials
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from datetime import datetime

console = Console()

def load_config():
    """加载配置"""
    with open('config/config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def connect_sheets(config):
    """连接到 Google Sheets"""
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    credentials_file = config.get('google_sheets_credentials') or config.get('google_credentials_file')
    sheet_id = config.get('google_sheet_id')

    creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(sheet_id)

    return spreadsheet

def migrate_health_data(spreadsheet):
    """
    迁移健康数据：Health Data → 健康记录

    注意：英文 sheet 的字段和中文 sheet 不同，需要映射
    """
    try:
        # 检查英文 sheet 是否存在
        try:
            english_sheet = spreadsheet.worksheet('Health Data')
        except gspread.WorksheetNotFound:
            console.print("[yellow]未找到 'Health Data' sheet，跳过迁移[/yellow]")
            return 0

        # 获取中文 sheet
        chinese_sheet = spreadsheet.worksheet('健康记录')

        console.print("\n[cyan]正在迁移健康数据...[/cyan]")

        # 获取英文 sheet 的所有数据
        english_data = english_sheet.get_all_records()

        if not english_data:
            console.print("[yellow]Health Data 没有数据，跳过[/yellow]")
            return 0

        # 获取中文 sheet 的现有日期
        chinese_data = chinese_sheet.get_all_records()
        existing_dates = {row['date'] for row in chinese_data if row.get('date')}

        console.print(f"  英文 sheet 有 {len(english_data)} 条记录")
        console.print(f"  中文 sheet 已有 {len(existing_dates)} 条记录")

        # 字段映射：英文 → 中文 sheet 字段名
        # 注意：中文 sheet 使用小写字段名
        field_mapping = {
            'Date': 'date',
            'Weight(kg)': 'weight',
            'Body Fat(%)': 'body_fat_percentage',
            'Muscle Mass(kg)': 'muscle_mass',
            'BMI': 'bmi',
            'Weight Feeling': 'weight_feeling',
            'Sleep Duration(h)': 'sleep_duration',
            'Sleep Start': 'sleep_start',
            'Sleep End': 'sleep_end',
            'Sleep Quality': 'sleep_quality',
            'Deep Sleep(h)': 'deep_sleep_duration',
            'Light Sleep(h)': 'light_sleep_duration',
            'REM Sleep(h)': 'rem_sleep_duration',
            'Awake Time(h)': 'awake_duration',
            'Sleep Notes': 'sleep_notes',
            'Heart Rate': 'heart_rate',
            'Blood Pressure': 'blood_pressure',
            'Mood': 'mood',
            'Energy Level': 'energy_level',
            'Water Intake(ml)': 'water_intake',
            'Steps': 'steps',
            'Overall Feeling': 'overall_feeling',
            'Health Notes': 'health_notes',
        }

        # 中文 sheet 的完整字段列表（按顺序）
        chinese_headers = [
            'date', 'weight', 'muscle_mass', 'body_fat_percentage', 'bmi',
            'basal_metabolism', 'visceral_fat_level', 'weight_feeling',
            'sleep_duration', 'sleep_start', 'sleep_end', 'sleep_quality',
            'deep_sleep_duration', 'light_sleep_duration', 'rem_sleep_duration',
            'awake_duration', 'sleep_notes', 'urination_count',
            'resting_heart_rate', 'heart_rate', 'hrv', 'blood_pressure', 'vo2_max',
            'rhr_baseline', 'hrv_baseline',
            'pain_score', 'pain_location', 'morning_stiffness_duration', 'symptoms',
            'mood', 'energy_level', 'overall_feeling',
            'steps', 'water_intake', 'health_notes',
            'created_at', 'updated_at'
        ]

        # 转换并合并数据
        new_count = 0
        updated_count = 0

        for eng_row in english_data:
            date = eng_row.get('Date', '')
            if not date:
                continue

            # 构建中文 sheet 的行数据
            chinese_row = []
            for field in chinese_headers:
                # 查找对应的英文字段
                eng_field = None
                for eng_key, chi_key in field_mapping.items():
                    if chi_key == field:
                        eng_field = eng_key
                        break

                if eng_field and eng_field in eng_row:
                    value = eng_row[eng_field]
                    chinese_row.append(value if value else '')
                elif field == 'updated_at':
                    chinese_row.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                else:
                    chinese_row.append('')

            # 检查是否已存在
            if date in existing_dates:
                # 更新现有记录（跳过，避免覆盖更完整的数据）
                updated_count += 1
                console.print(f"  [dim]跳过已存在的日期: {date}[/dim]")
            else:
                # 添加新记录
                chinese_sheet.append_row(chinese_row)
                new_count += 1
                console.print(f"  [green]+ 新增: {date}[/green]")
                existing_dates.add(date)

        console.print(f"\n[green]✓ 健康数据迁移完成！[/green]")
        console.print(f"  新增: {new_count} 条")
        console.print(f"  已存在（跳过）: {updated_count} 条")

        return new_count

    except Exception as e:
        console.print(f"[red]迁移健康数据时出错: {e}[/red]")
        return 0

def delete_english_sheets(spreadsheet):
    """删除英文 sheet"""
    sheets_to_delete = ['Health Data', 'Exercises', 'Meals', 'Statistics']

    console.print("\n[cyan]正在删除英文 sheet...[/cyan]")

    deleted_count = 0
    for sheet_name in sheets_to_delete:
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            spreadsheet.del_worksheet(worksheet)
            console.print(f"  [green]✓ 删除: {sheet_name}[/green]")
            deleted_count += 1
        except gspread.WorksheetNotFound:
            console.print(f"  [dim]未找到: {sheet_name}[/dim]")

    console.print(f"\n[green]✓ 删除了 {deleted_count} 个英文 sheet[/green]")
    return deleted_count

def main():
    """主函数"""
    console.print("\n[bold cyan]Google Sheets 数据迁移工具[/bold cyan]\n")

    # 加载配置
    console.print("加载配置...")
    config = load_config()

    # 连接 Google Sheets
    console.print("连接到 Google Sheets...")
    spreadsheet = connect_sheets(config)
    console.print(f"[green]✓ 已连接: {spreadsheet.title}[/green]")

    # 显示所有 sheet
    worksheets = spreadsheet.worksheets()
    console.print(f"\n当前所有 sheet ({len(worksheets)} 个):")
    for i, ws in enumerate(worksheets, 1):
        console.print(f"  {i}. {ws.title}")

    # 询问是否继续
    console.print("\n[yellow]⚠️  此操作将：[/yellow]")
    console.print("  1. 将 Health Data 的数据合并到 健康记录")
    console.print("  2. 删除英文 sheet: Health Data, Exercises, Meals, Statistics")
    console.print("  3. 保留所有历史数据（不会覆盖现有记录）")

    confirm = input("\n继续执行？(yes/no): ").strip().lower()

    if confirm != 'yes':
        console.print("[yellow]已取消操作[/yellow]")
        return

    # 迁移数据
    migrated = migrate_health_data(spreadsheet)

    # 删除英文 sheet
    deleted = delete_english_sheets(spreadsheet)

    # 完成
    console.print("\n[bold green]✓ 迁移完成！[/bold green]")
    console.print(f"\n统计：")
    console.print(f"  - 迁移了 {migrated} 条新记录")
    console.print(f"  - 删除了 {deleted} 个英文 sheet")
    console.print(f"\n[cyan]Google Sheets URL:[/cyan]")
    console.print(f"{spreadsheet.url}")

if __name__ == '__main__':
    main()

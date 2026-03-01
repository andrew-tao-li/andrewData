#!/usr/bin/env python3
"""
检查现有 Google Sheets 的结构
"""

import json
import gspread
from google.oauth2.service_account import Credentials
from rich.console import Console
from rich.table import Table

console = Console()

# 加载配置
with open('config/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 连接Google Sheets
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

credentials_file = config.get('google_sheets_credentials') or config.get('google_credentials_file')
sheet_id = config.get('google_sheet_id')

console.print(f"[cyan]连接到 Google Sheets...[/cyan]")
creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
client = gspread.authorize(creds)
spreadsheet = client.open_by_key(sheet_id)

console.print(f"\n[green]表格名称: {spreadsheet.title}[/green]")
console.print(f"[green]URL: {spreadsheet.url}[/green]\n")

# 列出所有工作表
worksheets = spreadsheet.worksheets()
console.print("[bold cyan]所有工作表:[/bold cyan]")
for i, ws in enumerate(worksheets, 1):
    console.print(f"  {i}. {ws.title} ({ws.row_count} 行 x {ws.col_count} 列)")

print()

# 检查中文命名的sheet
chinese_sheets = ['工作表1', '健康记录', '运动记录', '饮食记录']
for sheet_name in chinese_sheets:
    try:
        ws = spreadsheet.worksheet(sheet_name)
        headers = ws.row_values(1)

        console.print(f"\n[bold yellow]📊 {sheet_name}[/bold yellow]")
        console.print(f"  行数: {ws.row_count}, 列数: {ws.col_count}")

        # 获取一些数据样例
        data_rows = ws.get_all_values()
        console.print(f"  实际数据行数: {len(data_rows) - 1}")

        # 显示表头
        console.print(f"  [cyan]表头字段 ({len(headers)} 列):[/cyan]")
        for i, header in enumerate(headers, 1):
            console.print(f"    {i:2d}. {header}")

        # 显示前3行数据示例
        if len(data_rows) > 1:
            console.print(f"\n  [dim]数据示例（前3行）:[/dim]")
            table = Table(show_header=True, header_style="bold cyan")

            # 只显示前10列，避免太宽
            display_cols = min(10, len(headers))
            for header in headers[:display_cols]:
                table.add_column(header[:15])  # 限制列宽

            for row in data_rows[1:4]:  # 前3行数据
                if row:
                    display_row = [str(cell)[:15] for cell in row[:display_cols]]
                    table.add_row(*display_row)

            console.print(table)

    except gspread.exceptions.WorksheetNotFound:
        console.print(f"\n[yellow]⚠️  未找到工作表: {sheet_name}[/yellow]")

console.print("\n[green]✅ 检查完成！[/green]")

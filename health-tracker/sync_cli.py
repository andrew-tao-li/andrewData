#!/usr/bin/env python3
"""
数据同步CLI命令

简化的同步命令，用于Google Sheets双向同步
"""

import json
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table

from storage.sqlite_storage import HealthDatabase
from storage.google_sheets_storage import GoogleSheetsStorage
from sync_manager import SyncManager

console = Console()


def load_config() -> dict:
    """加载配置文件"""
    config_path = Path('config/config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


@click.group()
def cli():
    """数据同步管理"""
    pass


@cli.command('push')
@click.option('--date', help='同步指定日期的数据 (YYYY-MM-DD)')
def push_to_cloud(date: str):
    """推送本地数据到Google Sheets"""
    config = load_config()

    if not config.get('google_sheets_enabled'):
        console.print("[red]Google Sheets未启用[/red]")
        console.print("[yellow]请在config.json中设置 google_sheets_enabled: true[/yellow]")
        return

    console.print("\n[bold cyan]推送数据到云端...[/bold cyan]\n")

    try:
        # 初始化存储
        sqlite_db = HealthDatabase(config.get('database_path', 'data/health.db'))
        sheets_storage = GoogleSheetsStorage(
            credentials_file=config.get('google_credentials_file', 'config/credentials.json'),
            spreadsheet_id=config['google_sheet_id']
        )

        # 创建同步管理器
        sync_mgr = SyncManager(sqlite_db, sheets_storage)

        # 推送数据
        result = sync_mgr.push_to_cloud(date_str=date)

        if 'error' in result:
            console.print(f"[red]推送失败: {result['error']}[/red]")
        else:
            console.print(f"[green]✓ 推送成功[/green]")
            console.print(f"  已同步: {result.get('synced', 0)} 条")
            if result.get('failed', 0) > 0:
                console.print(f"  失败: {result['failed']} 条")

    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")


@cli.command('pull')
@click.option('--days', type=int, help='拉取最近N天数据')
@click.option('--date', help='拉取指定日期的数据 (YYYY-MM-DD)')
@click.option('--no-merge', is_flag=True, help='完全覆盖本地数据（默认为合并模式）')
def pull_from_cloud(days: int, date: str, no_merge: bool):
    """从Google Sheets拉取数据到本地"""
    config = load_config()

    if not config.get('google_sheets_enabled'):
        console.print("[red]Google Sheets未启用[/red]")
        return

    console.print("\n[bold cyan]从云端拉取数据...[/bold cyan]\n")

    try:
        # 初始化存储
        sqlite_db = HealthDatabase(config.get('database_path', 'data/health.db'))
        sheets_storage = GoogleSheetsStorage(
            credentials_file=config.get('google_credentials_file', 'config/credentials.json'),
            spreadsheet_id=config['google_sheet_id']
        )

        # 创建同步管理器
        sync_mgr = SyncManager(sqlite_db, sheets_storage)

        # 拉取数据
        result = sync_mgr.pull_from_cloud(
            date_str=date,
            days=days,
            merge=not no_merge
        )

        if 'error' in result:
            console.print(f"[red]拉取失败: {result['error']}[/red]")
        else:
            console.print(f"[green]✓ 拉取成功[/green]")
            console.print(f"  已同步: {result.get('synced', 0)} 条")
            if result.get('failed', 0) > 0:
                console.print(f"  失败: {result['failed']} 条")

    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")


@cli.command('status')
def sync_status():
    """查看同步状态"""
    config = load_config()

    if not config.get('google_sheets_enabled'):
        console.print("[red]Google Sheets未启用[/red]")
        return

    console.print("\n[bold cyan]同步状态[/bold cyan]\n")

    try:
        # 初始化存储
        sqlite_db = HealthDatabase(config.get('database_path', 'data/health.db'))
        sheets_storage = GoogleSheetsStorage(
            credentials_file=config.get('google_credentials_file', 'config/credentials.json'),
            spreadsheet_id=config['google_sheet_id']
        )

        # 创建同步管理器
        sync_mgr = SyncManager(sqlite_db, sheets_storage)

        # 获取状态
        status = sync_mgr.get_sync_status()

        if 'error' in status:
            console.print(f"[red]错误: {status['error']}[/red]")
            return

        # 显示状态
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("项目", style="cyan", width=20)
        table.add_column("值", style="green")

        table.add_row("Google Sheets", "✓ 已启用" if status['enabled'] else "✗ 未启用")
        table.add_row("本地记录数", str(status.get('local_records', 0)))
        table.add_row("云端记录数", str(status.get('cloud_records', 0)))
        table.add_row("本地最新日期", status.get('local_latest_date', 'N/A'))
        table.add_row("云端最新日期", status.get('cloud_latest_date', 'N/A'))
        table.add_row("同步状态", "✓ 已同步" if status.get('in_sync') else "⚠️  未同步")

        console.print(table)

        if 'spreadsheet_info' in status:
            info = status['spreadsheet_info']
            console.print(f"\n[cyan]表格信息:[/cyan]")
            console.print(f"  名称: {info['title']}")
            console.print(f"  URL: {info['url']}")

    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")


@cli.command('bidirectional')
@click.option('--strategy', type=click.Choice(['cloud_priority', 'local_priority', 'latest_priority']),
              default='cloud_priority', help='同步策略')
def sync_bidirectional(strategy: str):
    """双向智能同步"""
    config = load_config()

    if not config.get('google_sheets_enabled'):
        console.print("[red]Google Sheets未启用[/red]")
        return

    console.print(f"\n[bold cyan]双向同步 (策略: {strategy})...[/bold cyan]\n")

    try:
        # 初始化存储
        sqlite_db = HealthDatabase(config.get('database_path', 'data/health.db'))
        sheets_storage = GoogleSheetsStorage(
            credentials_file=config.get('google_credentials_file', 'config/credentials.json'),
            spreadsheet_id=config['google_sheet_id']
        )

        # 创建同步管理器
        sync_mgr = SyncManager(sqlite_db, sheets_storage)

        # 双向同步
        result = sync_mgr.sync_bidirectional(strategy=strategy)

        if 'error' in result:
            console.print(f"[red]同步失败: {result['error']}[/red]")
        else:
            console.print(f"[green]✓ 同步完成[/green]\n")

            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("操作", style="cyan")
            table.add_column("数量", style="green")

            table.add_row("总日期数", str(result.get('total_dates', 0)))
            table.add_row("推送到云端", str(result.get('pushed_to_cloud', 0)))
            table.add_row("拉取到本地", str(result.get('pulled_from_cloud', 0)))
            table.add_row("合并记录", str(result.get('merged', 0)))

            console.print(table)

    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")


if __name__ == '__main__':
    cli()

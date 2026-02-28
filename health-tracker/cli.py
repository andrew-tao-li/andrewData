#!/usr/bin/env python3
"""
Health Tracker CLI

命令行界面，用于管理健康数据的采集、分析和同步
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

# 导入项目模块
from parsers import ObsidianParser
from extractors import HealthDataExtractor
from storage import HealthDatabase
from sync import GoogleSheetsSync
from analytics import HealthAnalyzer

console = Console()


def load_config() -> dict:
    """加载配置文件"""
    config_path = Path(__file__).parent / "config" / "config.json"

    if not config_path.exists():
        console.print("[red]配置文件不存在，请先创建 config/config.json[/red]")
        console.print("[yellow]参考 config/config.example.json 创建配置文件[/yellow]")
        sys.exit(1)

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_date(date_str: str) -> str:
    """解析日期字符串"""
    if date_str.lower() == 'today':
        return datetime.now().date().isoformat()
    elif date_str.lower() == 'yesterday':
        return (datetime.now().date() - timedelta(days=1)).isoformat()
    else:
        try:
            # 验证日期格式
            datetime.fromisoformat(date_str)
            return date_str
        except ValueError:
            console.print(f"[red]无效的日期格式: {date_str}[/red]")
            console.print("[yellow]请使用 YYYY-MM-DD 格式，或 'today', 'yesterday'[/yellow]")
            sys.exit(1)


def create_extractor(config: dict) -> HealthDataExtractor:
    """
    根据配置创建数据提取器

    支持 Anthropic API 或 OpenRouter
    """
    use_openrouter = config.get('use_openrouter', False)

    if use_openrouter:
        # 使用 OpenRouter
        api_key = config.get('openrouter_api_key')
        if not api_key:
            console.print("[red]错误: 配置了 use_openrouter 但缺少 openrouter_api_key[/red]")
            sys.exit(1)

        model = config.get('openrouter_model', 'anthropic/claude-3.5-sonnet')
        console.print(f"[cyan]使用 OpenRouter API[/cyan]")

        return HealthDataExtractor(
            api_key=api_key,
            model=model,
            use_openrouter=True
        )
    else:
        # 使用原生 Anthropic API
        api_key = config.get('claude_api_key')
        if not api_key:
            console.print("[red]错误: 缺少 claude_api_key 配置[/red]")
            sys.exit(1)

        model = config.get('claude_model', 'claude-3-5-sonnet-20241022')
        console.print(f"[cyan]使用 Anthropic API[/cyan]")

        return HealthDataExtractor(
            api_key=api_key,
            model=model,
            use_openrouter=False
        )


@click.group()
def cli():
    """健康追踪系统 - 使用 Claude AI 管理你的健康数据"""
    pass


@cli.command()
@click.option('--date', default='today', help='日期 (YYYY-MM-DD, today, yesterday)')
@click.option('--force', is_flag=True, help='强制重新处理已存在的记录')
def parse(date: str, force: bool):
    """解析 Obsidian 笔记并提取健康数据"""
    config = load_config()
    date_str = get_date(date)

    console.print(f"\n[bold cyan]正在解析 {date_str} 的健康笔记...[/bold cyan]\n")

    try:
        # 初始化组件
        parser = ObsidianParser(
            config['obsidian_vault_path'],
            config.get('obsidian_health_folder', 'Health'),
            health_section_start=config.get('health_section_start'),
            health_section_end=config.get('health_section_end')
        )
        extractor = create_extractor(config)
        db = HealthDatabase(config.get('database_path', 'health_data.db'))

        # 检查是否已处理
        if not force:
            existing = db.get_record_by_date(date_str)
            if existing:
                console.print(f"[yellow]{date_str} 的记录已存在[/yellow]")
                console.print("[yellow]使用 --force 选项强制重新处理[/yellow]")
                return

        # 解析笔记
        note = parser.parse_note(datetime.fromisoformat(date_str))

        if not note:
            console.print(f"[red]未找到 {date_str} 的笔记[/red]")
            return

        console.print(f"[green]找到笔记: {note['file_path']}[/green]")

        # 显示图片信息
        if note['images']:
            console.print(f"[green]找到 {len(note['images'])} 张图片[/green]")

        # 使用 Claude 提取数据
        console.print("\n[bold cyan]正在使用 Claude AI 提取数据...[/bold cyan]\n")

        image_paths = [img['path'] for img in note['images']]
        extracted_data = extractor.extract_from_note(
            text=note['content'],
            images=image_paths if image_paths else None,
            date=date_str
        )

        # 检查是否有错误
        if 'error' in extracted_data:
            console.print(f"[red]提取数据时出错: {extracted_data['error']}[/red]")
            return

        # 保存到数据库
        console.print("[bold cyan]正在保存到数据库...[/bold cyan]\n")

        if db.save_health_record(extracted_data):
            console.print("[green]✓ 数据保存成功！[/green]\n")

            # 显示提取的数据
            display_health_data(extracted_data)
        else:
            console.print("[red]✗ 保存数据失败[/red]")

    except Exception as e:
        console.print(f"[red]错误: {str(e)}[/red]")
        import traceback
        traceback.print_exc()


@cli.command()
@click.option('--date', default='today', help='日期 (YYYY-MM-DD, today, yesterday)')
def show(date: str):
    """显示指定日期的健康数据"""
    config = load_config()
    date_str = get_date(date)

    db = HealthDatabase(config.get('database_path', 'health_data.db'))
    record = db.get_record_by_date(date_str)

    if not record:
        console.print(f"[yellow]未找到 {date_str} 的记录[/yellow]")
        return

    display_health_data(record)


@cli.command()
@click.option('--days', default=7, help='同步最近N天的数据')
@click.option('--all', 'sync_all', is_flag=True, help='同步所有未同步的数据')
def sync(days: int, sync_all: bool):
    """同步数据到 Google Sheets"""
    config = load_config()

    console.print("\n[bold cyan]正在同步到 Google Sheets...[/bold cyan]\n")

    try:
        db = HealthDatabase(config.get('database_path', 'health_data.db'))

        # 确保Google Sheets配置存在
        if 'google_sheets_credentials' not in config or 'google_sheet_id' not in config:
            console.print("[red]Google Sheets 配置缺失[/red]")
            console.print("[yellow]请在 config.json 中配置 google_sheets_credentials 和 google_sheet_id[/yellow]")
            return

        sheets_sync = GoogleSheetsSync(
            config['google_sheets_credentials'],
            config['google_sheet_id']
        )

        # 获取要同步的记录
        if sync_all:
            records = db.get_unsynced_records()
            console.print(f"找到 {len(records)} 条未同步的记录")
        else:
            records = db.get_recent_records(days)
            console.print(f"将同步最近 {days} 天的 {len(records)} 条记录")

        if not records:
            console.print("[yellow]没有需要同步的记录[/yellow]")
            return

        # 同步
        if sheets_sync.sync_records(records):
            console.print("[green]✓ 同步成功！[/green]")

            # 标记为已同步
            for record in records:
                db.mark_as_synced(record['date'])

            # 更新统计信息
            stats = db.get_statistics(days=30)
            sheets_sync.update_statistics(stats)

            console.print(f"\n[green]Google Sheets URL:[/green]")
            console.print(sheets_sync.get_spreadsheet_url())
        else:
            console.print("[red]✗ 同步失败[/red]")

    except Exception as e:
        console.print(f"[red]错误: {str(e)}[/red]")
        import traceback
        traceback.print_exc()


@cli.command()
@click.option('--days', default=30, help='统计天数')
def stats(days: int):
    """显示健康数据统计"""
    config = load_config()
    db = HealthDatabase(config.get('database_path', 'health_data.db'))

    console.print(f"\n[bold cyan]最近 {days} 天的健康统计[/bold cyan]\n")

    stats = db.get_statistics(days)

    if not stats:
        console.print("[yellow]暂无数据[/yellow]")
        return

    # 创建统计表格
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("指标", style="cyan")
    table.add_column("数值", style="green")

    # 体重统计
    if stats.get('weight'):
        w = stats['weight']
        if w.get('current'):
            table.add_row("当前体重", f"{w['current']} kg")
        if w.get('average'):
            table.add_row("平均体重", f"{w['average']:.1f} kg")
        if w.get('change'):
            change_emoji = "📉" if w['change'] < 0 else "📈"
            table.add_row("体重变化", f"{w['change']:+.1f} kg {change_emoji}")

    # 睡眠统计
    if stats.get('sleep'):
        s = stats['sleep']
        if s.get('average_duration'):
            table.add_row("平均睡眠", f"{s['average_duration']:.1f} 小时")

    # 运动统计
    if stats.get('exercise'):
        e = stats['exercise']
        table.add_row("总运动时长", f"{e['total_minutes']} 分钟")
        table.add_row("运动次数", f"{e['total_sessions']} 次")

    # 记录统计
    table.add_row("总记录天数", f"{stats['days_with_data']} 天")

    console.print(table)


@cli.command()
@click.option('--period', type=click.Choice(['day', 'week', 'month']), default='week', help='报告周期')
@click.option('--date', help='日期 (YYYY-MM-DD)')
def report(period: str, date: Optional[str]):
    """生成健康报告"""
    config = load_config()

    console.print(f"\n[bold cyan]正在生成{period_name(period)}报告...[/bold cyan]\n")

    try:
        extractor = create_extractor(config)
        db = HealthDatabase(config.get('database_path', 'health_data.db'))
        analyzer = HealthAnalyzer(extractor, db)

        if period == 'day':
            date_str = get_date(date) if date else get_date('today')
            analysis = analyzer.generate_daily_summary(date_str)
        elif period == 'week':
            date_str = get_date(date) if date else None
            analysis = analyzer.generate_weekly_report(date_str)
        else:  # month
            if date:
                dt = datetime.fromisoformat(get_date(date))
            else:
                dt = datetime.now()
            analysis = analyzer.generate_monthly_report(dt.year, dt.month)

        # 显示报告
        console.print(Panel(
            Markdown(analysis),
            title=f"{period_name(period)}健康报告",
            border_style="cyan"
        ))

    except Exception as e:
        console.print(f"[red]错误: {str(e)}[/red]")
        import traceback
        traceback.print_exc()


@cli.command()
@click.argument('question')
@click.option('--days', default=30, help='查询最近N天的数据')
def chat(question: str, days: int):
    """向 Claude 提问关于你的健康数据"""
    config = load_config()

    console.print(f"\n[bold cyan]正在分析数据并回答问题...[/bold cyan]\n")

    try:
        extractor = create_extractor(config)
        db = HealthDatabase(config.get('database_path', 'health_data.db'))
        analyzer = HealthAnalyzer(extractor, db)

        answer = analyzer.answer_question(question, days)

        console.print(Panel(
            Markdown(answer),
            title="Claude 的回答",
            border_style="green"
        ))

    except Exception as e:
        console.print(f"[red]错误: {str(e)}[/red]")
        import traceback
        traceback.print_exc()


@cli.command()
@click.option('--days', default=30, help='分析天数')
def correlations(days: int):
    """分析健康指标之间的相关性"""
    config = load_config()

    console.print(f"\n[bold cyan]正在分析最近 {days} 天的数据相关性...[/bold cyan]\n")

    try:
        extractor = create_extractor(config)
        db = HealthDatabase(config.get('database_path', 'health_data.db'))
        analyzer = HealthAnalyzer(extractor, db)

        analysis = analyzer.identify_correlations(days)

        console.print(Panel(
            Markdown(analysis),
            title="相关性分析",
            border_style="magenta"
        ))

    except Exception as e:
        console.print(f"[red]错误: {str(e)}[/red]")


@cli.command()
@click.option('--goal', help='健康目标（如：减重5kg）')
def recommend(goal: Optional[str]):
    """获取个性化健康建议"""
    config = load_config()

    console.print("\n[bold cyan]正在生成个性化建议...[/bold cyan]\n")

    try:
        extractor = create_extractor(config)
        db = HealthDatabase(config.get('database_path', 'health_data.db'))
        analyzer = HealthAnalyzer(extractor, db)

        recommendations = analyzer.generate_recommendations(goal)

        console.print(Panel(
            Markdown(recommendations),
            title="个性化健康建议",
            border_style="yellow"
        ))

    except Exception as e:
        console.print(f"[red]错误: {str(e)}[/red]")


def display_health_data(data: dict):
    """显示健康数据的美化输出"""
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("项目", style="cyan", width=24)
    table.add_column("数值", style="green")

    # 日期
    if 'date' in data or 'processed_date' in data:
        table.add_row("日期", data.get('date') or data.get('processed_date'))

    # 体重相关
    if data.get('weight'):
        table.add_row("体重", f"{data['weight']} kg")
    if data.get('body_fat_percentage'):
        table.add_row("体脂率", f"{data['body_fat_percentage']}%")
    if data.get('muscle_mass'):
        table.add_row("肌肉量", f"{data['muscle_mass']} kg")
    if data.get('basal_metabolism'):
        table.add_row("基础代谢", f"{data['basal_metabolism']} kcal/天")
    if data.get('visceral_fat_level'):
        table.add_row("内脏脂肪等级", str(data['visceral_fat_level']))
    if data.get('bmi'):
        table.add_row("BMI", f"{data['bmi']}")

    # 睡眠相关
    if data.get('sleep_duration'):
        table.add_row("睡眠时长", f"{data['sleep_duration']} 小时")
    if data.get('deep_sleep_duration'):
        table.add_row("深度睡眠", f"{data['deep_sleep_duration']} 小时")
    if data.get('rem_sleep_duration'):
        table.add_row("REM睡眠", f"{data['rem_sleep_duration']} 小时")
    if data.get('sleep_quality'):
        table.add_row("睡眠质量", str(data['sleep_quality']))
    if data.get('urination_count'):
        table.add_row("夜间排尿", f"{data['urination_count']} 次")

    # 心血管相关
    if data.get('resting_heart_rate'):
        table.add_row("静息心率", f"{data['resting_heart_rate']} bpm")
    if data.get('heart_rate'):
        table.add_row("心率", f"{data['heart_rate']} bpm")
    if data.get('hrv'):
        table.add_row("HRV", str(data['hrv']))
    if data.get('blood_pressure'):
        table.add_row("血压", data['blood_pressure'])
    if data.get('vo2_max'):
        table.add_row("VO2 Max", str(data['vo2_max']))

    # 疼痛和症状
    if data.get('pain_score'):
        table.add_row("疼痛评分", f"{data['pain_score']}/10")
    if data.get('pain_location'):
        table.add_row("疼痛部位", data['pain_location'])
    if data.get('morning_stiffness_duration'):
        table.add_row("晨僵时间", f"{data['morning_stiffness_duration']} 分钟")
    if data.get('symptoms'):
        table.add_row("症状", data['symptoms'])

    # 主观感受
    if data.get('mood'):
        table.add_row("心情", str(data['mood']))
    if data.get('energy_level'):
        table.add_row("精力水平", str(data['energy_level']))
    if data.get('overall_feeling'):
        table.add_row("整体感受", data['overall_feeling'])

    # 运动
    if data.get('exercises'):
        exercises_text = "\n".join([
            f"• {ex.get('type', '未知')} - {ex.get('duration', '?')}分钟"
            for ex in data['exercises']
        ])
        table.add_row("运动", exercises_text)

    # 其他
    if data.get('steps'):
        table.add_row("步数", str(data['steps']))
    if data.get('water_intake'):
        table.add_row("饮水量", f"{data['water_intake']} ml")
    if data.get('health_notes'):
        table.add_row("健康备注", data['health_notes'])

    console.print(table)


def period_name(period: str) -> str:
    """获取周期的中文名称"""
    names = {
        'day': '每日',
        'week': '每周',
        'month': '每月'
    }
    return names.get(period, period)


@cli.command()
@click.option('--date', default='yesterday', help='同步日期 (YYYY-MM-DD, today, yesterday)')
@click.option('--force', is_flag=True, help='强制重新同步')
def garmin_sync(date: str, force: bool):
    """从 Garmin 同步健康数据"""
    from datetime import datetime
    from garmin.garmin_client import GarminClient
    from garmin.obsidian_writer import ObsidianWriter
    from garmin.health_analyzer import HealthAnalyzer

    config = load_config()
    date_obj = datetime.fromisoformat(get_date(date))

    console.print(f"\n[bold cyan]🔄 正在同步 Garmin 数据 ({date_obj.strftime('%Y-%m-%d')})...[/bold cyan]\n")

    try:
        # 初始化 Garmin 客户端
        garmin = GarminClient(
            email=config['garmin_email'],
            password=config['garmin_password'],
            is_china=config.get('garmin_is_china', True)
        )

        # 获取数据
        data = garmin.get_daily_summary(date_obj)

        if not data:
            console.print("[red]✗ 获取 Garmin 数据失败[/red]")
            return

        # 验证数据
        required_fields = config.get('garmin_required_fields', ['sleep_duration', 'hrv'])
        if not garmin.validate_data(data, required_fields):
            console.print("[yellow]⚠️  数据不完整，但仍会保存[/yellow]")

        # 保存到数据库
        db = HealthDatabase(config.get('database_path', 'health_data.db'))

        health_record = {
            'date': data['date'],
            'sleep_duration': data['sleep'].get('sleep_duration') if data.get('sleep') else None,
            'deep_sleep_duration': data['sleep'].get('deep_sleep_duration') if data.get('sleep') else None,
            'rem_sleep_duration': data['sleep'].get('rem_sleep_duration') if data.get('sleep') else None,
            'hrv': data['hrv'].get('hrv') if data.get('hrv') else None,
            'resting_heart_rate': data['heart_rate'].get('resting_heart_rate') if data.get('heart_rate') else None,
        }

        db.save_health_record(health_record)

        # 保存运动记录
        if data.get('activities'):
            for activity in data['activities']:
                exercise_data = {
                    'date': data['date'],
                    'type': activity.get('type'),
                    'duration': int(activity.get('duration', 0)),
                    'distance': activity.get('distance'),
                    'calories': activity.get('calories'),
                }
                db.save_exercise(exercise_data)

        # 写入 Obsidian
        obsidian = ObsidianWriter(
            vault_path=config['obsidian_vault_path'],
            health_log_start=config.get('health_log_section_start', '（健康日志）'),
            health_log_end=config.get('health_log_section_end', '（健康日志结束）')
        )

        create_if_missing = config.get('create_daily_note_if_missing', True)
        obsidian.write_health_log(date_obj, data, create_if_missing)

        # 生成分析
        extractor = create_extractor(config)
        analyzer = HealthAnalyzer(db, extractor)

        brief_analysis = analyzer.generate_brief_summary(days=7)
        obsidian.append_analysis(date_obj, brief_analysis)

        console.print("[green]✓ Garmin 数据同步成功！[/green]")

    except Exception as e:
        console.print(f"[red]✗ 同步失败: {str(e)}[/red]")
        import traceback
        traceback.print_exc()


@cli.command()
def garmin_test():
    """测试 Garmin 连接"""
    from garmin.garmin_client import GarminClient

    config = load_config()

    console.print("\n[bold cyan]🔍 测试 Garmin 连接...[/bold cyan]\n")

    try:
        garmin = GarminClient(
            email=config['garmin_email'],
            password=config['garmin_password'],
            is_china=config.get('garmin_is_china', True)
        )

        if garmin.authenticate():
            console.print("[green]✓ Garmin 认证成功！[/green]")
            console.print(f"[cyan]账号: {config['garmin_email']}[/cyan]")
        else:
            console.print("[red]✗ Garmin 认证失败[/red]")

    except Exception as e:
        console.print(f"[red]✗ 测试失败: {str(e)}[/red]")


@cli.command()
def start_scheduler():
    """启动 Garmin 自动同步调度器"""
    from garmin.scheduler import GarminScheduler

    console.print("\n[bold cyan]🚀 启动 Garmin 自动同步调度器...[/bold cyan]\n")

    try:
        scheduler = GarminScheduler()
        scheduler.start()
    except KeyboardInterrupt:
        console.print("\n[yellow]调度器已停止[/yellow]")
    except Exception as e:
        console.print(f"[red]✗ 启动失败: {str(e)}[/red]")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    cli()

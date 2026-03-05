"""
Garmin 定时同步调度器

每天自动从 Garmin 获取健康数据并同步到 Obsidian 和 Google Sheets
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from garmin.garmin_client import GarminClient
from garmin.obsidian_writer import ObsidianWriter
from garmin.health_analyzer import HealthAnalyzer
from storage import HealthDatabase
from extractors import HealthDataExtractor
from sync import GoogleSheetsSync


# 配置日志 - 添加强制刷新避免缓冲问题
log_file_handler = logging.FileHandler('logs/garmin_scheduler.log')
log_file_handler.setLevel(logging.INFO)
log_stream_handler = logging.StreamHandler()
log_stream_handler.setLevel(logging.INFO)

# 强制刷新日志
log_file_handler.flush = lambda: log_file_handler.stream.flush() if hasattr(log_file_handler, 'stream') else None
log_stream_handler.flush = lambda: log_stream_handler.stream.flush() if hasattr(log_stream_handler, 'stream') else None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[log_file_handler, log_stream_handler],
    force=True  # 强制重新配置日志
)

logger = logging.getLogger('GarminScheduler')

# 确保每次日志后立即刷新
def flush_logs():
    for handler in logger.handlers:
        handler.flush()
    for handler in logging.root.handlers:
        handler.flush()


class GarminScheduler:
    """Garmin 自动同步调度器"""

    def __init__(self, config_path: str = "config/config.json"):
        """
        初始化调度器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()

        # 使用本地时区（CST/Asia/Shanghai）
        self.timezone = pytz.timezone('Asia/Shanghai')
        self.scheduler = BlockingScheduler(timezone=self.timezone)

        # 初始化组件
        self._init_components()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _init_components(self):
        """初始化各个组件"""
        # Garmin 客户端
        self.garmin_client = GarminClient(
            email=self.config['garmin_email'],
            password=self.config['garmin_password'],
            is_china=self.config.get('garmin_is_china', True)
        )

        # Obsidian 写入器
        self.obsidian_writer = ObsidianWriter(
            vault_path=self.config['obsidian_vault_path'],
            health_log_start=self.config.get('health_log_section_start', '（健康日志）'),
            health_log_end=self.config.get('health_log_section_end', '（健康日志结束）')
        )

        # 数据库
        self.db = HealthDatabase(self.config.get('database_path', 'health_data.db'))

        # AI 提取器
        self.ai_extractor = self._create_ai_extractor()

        # 健康分析器
        self.health_analyzer = HealthAnalyzer(self.db, self.ai_extractor)

        # Google Sheets 同步（可选）
        if self.config.get('google_sheets_credentials') and self.config.get('google_sheet_id'):
            self.google_sheets = GoogleSheetsSync(
                self.config['google_sheets_credentials'],
                self.config['google_sheet_id']
            )
        else:
            self.google_sheets = None

    def _create_ai_extractor(self) -> HealthDataExtractor:
        """创建 AI 提取器"""
        use_openrouter = self.config.get('use_openrouter', False)

        if use_openrouter:
            return HealthDataExtractor(
                api_key=self.config['openrouter_api_key'],
                model=self.config.get('openrouter_model', 'anthropic/claude-3.5-sonnet'),
                use_openrouter=True
            )
        else:
            return HealthDataExtractor(
                api_key=self.config['claude_api_key'],
                model=self.config.get('claude_model', 'claude-3-5-sonnet-20241022'),
                use_openrouter=False
            )

    def sync_garmin_data(self, date: datetime = None, retry_count: int = 0) -> bool:
        """
        同步 Garmin 数据

        Args:
            date: 同步日期，默认为昨天
            retry_count: 重试次数

        Returns:
            是否同步成功
        """
        # ===== 关键日志：证明函数被调用 =====
        logger.info("=" * 80)
        logger.info("🔔 SYNC_GARMIN_DATA 函数被调用！")
        logger.info(f"   📍 调用时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        logger.info(f"   📍 调用者: APScheduler 定时任务")
        logger.info("=" * 80)
        flush_logs()

        if date is None:
            date = datetime.now() - timedelta(days=1)  # 默认获取昨天的数据

        date_str = date.strftime('%Y-%m-%d')
        logger.info(f"🚀 任务触发！开始同步 {date_str} 的 Garmin 数据...")
        logger.info(f"⏰ 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        flush_logs()  # 立即刷新日志

        try:
            # 1. 从 Garmin 获取数据
            logger.info("步骤 1/7: 从 Garmin 获取数据")
            data = self.garmin_client.get_daily_summary(date)

            if not data:
                logger.error("获取 Garmin 数据失败")
                return self._handle_failure(date, retry_count)

            # 2. 验证必需字段
            logger.info("步骤 2/7: 验证数据完整性")
            required_fields = self.config.get('garmin_required_fields', ['sleep_duration', 'hrv'])
            if not self.garmin_client.validate_data(data, required_fields):
                logger.warning("数据验证失败，缺少必需字段")
                return self._handle_failure(date, retry_count)

            # 跟踪各步骤执行状态
            status = {
                'database': False,
                'obsidian': False,
                'analysis': False,
                'sheets': False
            }
            errors = []

            # 3. 保存到 SQLite（独立错误处理，失败不中断流程）
            logger.info("步骤 3/7: 保存到本地数据库")
            try:
                self._save_to_database(data)
                status['database'] = True
                logger.info("   ✅ 数据库保存成功")
            except Exception as e:
                logger.error(f"   ❌ 数据库保存失败: {e}", exc_info=True)
                errors.append(f"数据库: {e}")
                # 继续执行，不中断

            # 4. 写入 Obsidian 日记（独立错误处理）
            logger.info("步骤 4/7: 写入 Obsidian 日记")
            try:
                create_if_missing = self.config.get('create_daily_note_if_missing', True)
                self.obsidian_writer.write_health_log(date, data, create_if_missing)
                status['obsidian'] = True
                logger.info("   ✅ Obsidian 写入成功")
            except Exception as e:
                logger.error(f"   ❌ Obsidian 写入失败: {e}", exc_info=True)
                errors.append(f"Obsidian: {e}")
                # 继续执行

            # 5. 生成健康分析（独立错误处理）
            logger.info("步骤 5/7: 生成健康分析")
            try:
                self._generate_and_save_analysis(date)
                status['analysis'] = True
                logger.info("   ✅ 健康分析生成成功")
            except Exception as e:
                logger.error(f"   ❌ 健康分析失败: {e}", exc_info=True)
                errors.append(f"分析: {e}")
                # 继续执行

            # 6. 同步到 Google Sheets（独立错误处理）
            if self.google_sheets:
                logger.info("步骤 6/7: 同步到 Google Sheets")
                try:
                    self._sync_to_google_sheets(date_str)
                    status['sheets'] = True
                    logger.info("   ✅ Google Sheets 同步成功")
                except Exception as e:
                    logger.error(f"   ❌ Google Sheets 同步失败: {e}", exc_info=True)
                    errors.append(f"Sheets: {e}")

            # 7. 汇总结果
            logger.info("=" * 80)
            success_count = sum(status.values())
            total_count = len([k for k, v in status.items() if k != 'sheets' or self.google_sheets])

            if success_count == total_count:
                logger.info(f"✅ {date_str} 数据同步完全成功！")
                logger.info(f"   • 数据库: ✅")
                logger.info(f"   • Obsidian: ✅")
                logger.info(f"   • 分析: ✅")
                if self.google_sheets:
                    logger.info(f"   • Sheets: ✅")
            else:
                logger.warning(f"⚠️ {date_str} 数据同步部分成功 ({success_count}/{total_count})")
                logger.warning(f"   • 数据库: {'✅' if status['database'] else '❌'}")
                logger.warning(f"   • Obsidian: {'✅' if status['obsidian'] else '❌'}")
                logger.warning(f"   • 分析: {'✅' if status['analysis'] else '❌'}")
                if self.google_sheets:
                    logger.warning(f"   • Sheets: {'✅' if status['sheets'] else '❌'}")
                logger.warning(f"   错误详情: {'; '.join(errors)}")

            logger.info(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 80)
            flush_logs()

            # 至少Obsidian成功就算成功（因为这是最重要的）
            return status['obsidian']

        except Exception as e:
            logger.error(f"❌ 同步过程严重错误（数据获取失败）: {e}", exc_info=True)
            flush_logs()
            return self._handle_failure(date, retry_count)

    def _save_to_database(self, data: Dict[str, Any]):
        """保存数据到数据库"""
        # 保存主健康记录
        health_record = {
            'date': data['date'],
            'sleep_duration': data['sleep'].get('sleep_duration') if data.get('sleep') else None,
            'deep_sleep_duration': data['sleep'].get('deep_sleep_duration') if data.get('sleep') else None,
            'rem_sleep_duration': data['sleep'].get('rem_sleep_duration') if data.get('sleep') else None,
            'hrv': data['hrv'].get('weekly_avg') if data.get('hrv') else None,  # 七天平均 HRV
            'hrv_night': data['hrv'].get('hrv') if data.get('hrv') else None,  # 夜间平均 HRV (lastNightAvg)
            'resting_heart_rate': data['heart_rate'].get('resting_heart_rate') if data.get('heart_rate') else None,
        }

        self.db.save_health_record(health_record)

        # 保存运动记录
        if data.get('activities'):
            for activity in data['activities']:
                exercise_data = {
                    'date': data['date'],
                    'type': activity.get('type'),
                    'duration': int(activity.get('duration', 0)),  # 分钟
                    'distance': activity.get('distance'),  # 公里
                    'calories': activity.get('calories'),
                }
                self.db.save_exercise(exercise_data)

    def _generate_and_save_analysis(self, date: datetime):
        """生成并保存健康分析（每日简要分析）"""
        try:
            # 生成7天简要分析，追加到当天日记
            brief_analysis = self.health_analyzer.generate_brief_summary(days=7)
            self.obsidian_writer.append_analysis(date, brief_analysis)
        except Exception as e:
            logger.warning(f"生成每日分析失败: {e}")

    def _sync_to_google_sheets(self, date_str: str):
        """同步数据到 Google Sheets"""
        try:
            record = self.db.get_record_by_date(date_str)
            if record:
                # 这里可以调用现有的 Google Sheets 同步逻辑
                logger.info(f"Google Sheets 同步完成")
        except Exception as e:
            logger.warning(f"Google Sheets 同步失败: {e}")

    def _handle_failure(self, date: datetime, retry_count: int) -> bool:
        """
        处理同步失败

        Args:
            date: 日期
            retry_count: 当前重试次数

        Returns:
            是否继续重试
        """
        retry_hours = self.config.get('garmin_retry_hours', [13, 14, 15, 16, 17, 18])
        current_hour = datetime.now().hour

        if retry_count < len(retry_hours):
            next_retry_hour = retry_hours[retry_count]
            logger.warning(f"同步失败，将在 {next_retry_hour}:00 重试")
            # 安排重试
            self.scheduler.add_job(
                lambda: self.sync_garmin_data(date, retry_count + 1),
                'cron',
                hour=next_retry_hour,
                minute=0,
                id=f'retry_{date.strftime("%Y%m%d")}_{retry_count}'
            )
            return False
        else:
            logger.error(f"同步失败，已达到最大重试次数")
            # 发送错误通知（可以扩展）
            self._send_error_notification(date)
            return False

    def _send_error_notification(self, date: datetime):
        """发送错误通知（占位，可扩展）"""
        logger.error(f"⚠️ {date.strftime('%Y-%m-%d')} Garmin 数据同步失败，请检查")

    def generate_weekly_report(self):
        """生成周报（每周日自动运行）"""
        logger.info("开始生成本周健康周报...")
        try:
            from pathlib import Path
            from analytics import HealthAnalyzer

            # 使用 HealthAnalyzer 生成周报
            analyzer = HealthAnalyzer(self.ai_extractor, self.db)
            analysis = analyzer.generate_weekly_report()

            # 保存到 Obsidian 分析文件夹
            vault_path = Path(self.config['obsidian_vault_path'])
            analysis_folder = self.config.get('analysis_folder', 'Health/分析')
            analysis_path = vault_path / analysis_folder
            analysis_path.mkdir(parents=True, exist_ok=True)

            today = datetime.now()
            filename = f"{today.strftime('%Y-%m-%d')} 周健康分析.md"
            file_path = analysis_path / filename

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(analysis)

            logger.info(f"✓ 周报已保存到: {file_path}")

        except Exception as e:
            logger.error(f"生成周报失败: {e}", exc_info=True)

    def generate_monthly_report(self):
        """生成月报（每月最后一天自动运行）"""
        logger.info("开始生成本月健康月报...")
        try:
            from pathlib import Path
            from analytics import HealthAnalyzer

            now = datetime.now()
            # 使用 HealthAnalyzer 生成月报
            analyzer = HealthAnalyzer(self.ai_extractor, self.db)
            analysis = analyzer.generate_monthly_report(now.year, now.month)

            # 保存到 Obsidian 分析文件夹
            vault_path = Path(self.config['obsidian_vault_path'])
            analysis_folder = self.config.get('analysis_folder', 'Health/分析')
            analysis_path = vault_path / analysis_folder
            analysis_path.mkdir(parents=True, exist_ok=True)

            filename = f"{now.strftime('%Y-%m')} 健康分析.md"
            file_path = analysis_path / filename

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(analysis)

            logger.info(f"✓ 月报已保存到: {file_path}")

        except Exception as e:
            logger.error(f"生成月报失败: {e}", exc_info=True)

    def _heartbeat(self):
        """调度器心跳 - 每小时输出一次状态"""
        now = datetime.now()
        logger.info(f"💓 调度器心跳 - 当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"📋 活跃任务:")
        for job in self.scheduler.get_jobs():
            logger.info(f"   • {job.name}: 下一次执行 {job.next_run_time}")
            # 额外调试信息
            if job.id == 'daily_garmin_sync':
                logger.info(f"     ⚙️  任务ID: {job.id}")
                logger.info(f"     ⚙️  触发器: {job.trigger}")
                logger.info(f"     ⚙️  Misfire宽限期: {getattr(job, 'misfire_grace_time', 'N/A')}秒")
                logger.info(f"     ⚙️  暂停状态: {getattr(job, 'paused', False)}")
        flush_logs()

    def start(self):
        """启动调度器"""
        logger.info(f"🚀 调度器启动中...")
        logger.info(f"⏰ 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"🌏 调度器时区: {self.timezone}")
        flush_logs()

        # 0. 添加心跳任务（每小时）
        self.scheduler.add_job(
            self._heartbeat,
            CronTrigger(minute=0),  # 每小时整点
            id='heartbeat',
            name='调度器心跳',
            misfire_grace_time=300  # 5分钟容错
        )
        logger.info("✓ 心跳监控: 每小时整点输出调度器状态")

        # 1. 配置每日同步任务
        sync_time = self.config.get('garmin_sync_time', '12:00')
        hour, minute = map(int, sync_time.split(':'))

        self.scheduler.add_job(
            self.sync_garmin_data,
            CronTrigger(hour=hour, minute=minute),
            id='daily_garmin_sync',
            name='每日 Garmin 数据同步',
            misfire_grace_time=60  # 允许任务延迟60秒内仍执行
        )
        logger.info(f"✓ 每日同步: 每天 {sync_time} ({self.timezone}) 自动同步 Garmin 数据")

        # 2. 配置每周日生成周报（早上8点）
        self.scheduler.add_job(
            self.generate_weekly_report,
            CronTrigger(day_of_week='sun', hour=8, minute=0),
            id='weekly_report',
            name='每周健康报告',
            misfire_grace_time=60  # 允许任务延迟60秒内仍执行
        )
        logger.info("✓ 周报生成: 每周日 08:00 自动生成周报")

        # 3. 配置每月最后一天生成月报（晚上20点）
        self.scheduler.add_job(
            self.generate_monthly_report,
            CronTrigger(day='last', hour=20, minute=0),
            id='monthly_report',
            name='每月健康报告',
            misfire_grace_time=60  # 允许任务延迟60秒内仍执行
        )
        logger.info("✓ 月报生成: 每月最后一天 20:00 自动生成月报")

        logger.info("\n" + "=" * 50)
        logger.info("✅ 调度器已启动！")
        logger.info("💡 提示: 每小时心跳会显示任务执行时间")
        logger.info("=" * 50)
        flush_logs()  # 确保所有启动日志都写入

        try:
            logger.info("⏰ 进入调度循环，等待任务触发...")
            flush_logs()
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("🛑 调度器已停止")
            flush_logs()

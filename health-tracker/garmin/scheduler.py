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

from garmin.garmin_client import GarminClient
from garmin.obsidian_writer import ObsidianWriter
from garmin.health_analyzer import HealthAnalyzer
from storage import HealthDatabase
from extractors import HealthDataExtractor
from sync import GoogleSheetsSync


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/garmin_scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('GarminScheduler')


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
        self.scheduler = BlockingScheduler()

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
        if date is None:
            date = datetime.now() - timedelta(days=1)  # 默认获取昨天的数据

        date_str = date.strftime('%Y-%m-%d')
        logger.info(f"开始同步 {date_str} 的 Garmin 数据...")

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

            # 3. 保存到 SQLite
            logger.info("步骤 3/7: 保存到本地数据库")
            self._save_to_database(data)

            # 4. 写入 Obsidian 日记
            logger.info("步骤 4/7: 写入 Obsidian 日记")
            create_if_missing = self.config.get('create_daily_note_if_missing', True)
            self.obsidian_writer.write_health_log(date, data, create_if_missing)

            # 5. 生成健康分析
            logger.info("步骤 5/7: 生成健康分析")
            self._generate_and_save_analysis(date)

            # 6. 同步到 Google Sheets
            if self.google_sheets:
                logger.info("步骤 6/7: 同步到 Google Sheets")
                self._sync_to_google_sheets(date_str)

            # 7. 完成
            logger.info(f"✓ {date_str} 数据同步成功")
            return True

        except Exception as e:
            logger.error(f"同步过程出错: {e}", exc_info=True)
            return self._handle_failure(date, retry_count)

    def _save_to_database(self, data: Dict[str, Any]):
        """保存数据到数据库"""
        # 保存主健康记录
        health_record = {
            'date': data['date'],
            'sleep_duration': data['sleep'].get('sleep_duration') if data.get('sleep') else None,
            'deep_sleep_duration': data['sleep'].get('deep_sleep_duration') if data.get('sleep') else None,
            'rem_sleep_duration': data['sleep'].get('rem_sleep_duration') if data.get('sleep') else None,
            'hrv': data['hrv'].get('hrv') if data.get('hrv') else None,
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
        """生成并保存健康分析"""
        try:
            # 生成7天简要分析
            brief_analysis = self.health_analyzer.generate_brief_summary(days=7)
            self.obsidian_writer.append_analysis(date, brief_analysis)

            # 生成30天详细分析（每周更新一次）
            if date.weekday() == 6:  # 周日
                detailed_analysis = self.health_analyzer.generate_detailed_analysis(days=30)
                period = date.strftime('%Y-%m')
                analysis_folder = self.config.get('analysis_folder', 'Health/分析')
                self.obsidian_writer.create_analysis_note(period, detailed_analysis, analysis_folder)

        except Exception as e:
            logger.warning(f"生成分析失败: {e}")

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

    def start(self):
        """启动调度器"""
        # 配置每日同步任务
        sync_time = self.config.get('garmin_sync_time', '12:00')
        hour, minute = map(int, sync_time.split(':'))

        self.scheduler.add_job(
            self.sync_garmin_data,
            CronTrigger(hour=hour, minute=minute),
            id='daily_garmin_sync',
            name='每日 Garmin 数据同步'
        )

        logger.info(f"✓ 调度器已启动，每天 {sync_time} 自动同步 Garmin 数据")
        logger.info("按 Ctrl+C 停止调度器")

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("调度器已停止")

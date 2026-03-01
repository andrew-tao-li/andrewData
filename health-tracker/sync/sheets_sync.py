"""
Google Sheets同步模块

将本地SQLite数据同步到Google Sheets进行云端备份和跨设备访问
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False
    print("Warning: gspread not installed. Google Sheets sync will not work.")


class GoogleSheetsSync:
    """Google Sheets同步管理器"""

    def __init__(
        self,
        credentials_file: str,
        spreadsheet_id: str
    ):
        """
        初始化同步器

        Args:
            credentials_file: Google服务账号凭证JSON文件路径
            spreadsheet_id: Google Sheets的ID
        """
        if not GSPREAD_AVAILABLE:
            raise ImportError("gspread is required for Google Sheets sync")

        self.credentials_file = credentials_file
        self.spreadsheet_id = spreadsheet_id
        self.client = None
        self.spreadsheet = None
        self._connect()

    def _connect(self):
        """连接到Google Sheets"""
        try:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]

            creds = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=scopes
            )

            self.client = gspread.authorize(creds)
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            print(f"Connected to spreadsheet: {self.spreadsheet.title}")

        except Exception as e:
            print(f"Error connecting to Google Sheets: {e}")
            raise

    def sync_records(self, records: List[Dict[str, Any]]) -> bool:
        """
        同步健康记录到Google Sheets

        Args:
            records: 健康记录列表

        Returns:
            是否同步成功
        """
        try:
            # 确保工作表存在
            self._ensure_worksheets()

            # 同步主数据
            self._sync_main_data(records)

            # 同步运动数据
            self._sync_exercises(records)

            # 同步饮食数据
            self._sync_meals(records)

            print(f"Successfully synced {len(records)} records to Google Sheets")
            return True

        except Exception as e:
            print(f"Error syncing to Google Sheets: {e}")
            return False

    def _ensure_worksheets(self):
        """确保所有需要的工作表都存在"""
        # 使用原有的中文 sheet 名称和字段
        required_sheets = {
            '健康记录': [
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
            ],
            '运动记录': [
                'id', 'date', 'type', 'duration', 'distance', 'intensity',
                'calories', 'avg_heart_rate', 'max_heart_rate', 'avg_pace',
                'training_load', 'feeling', 'notes', 'created_at'
            ],
            '饮食记录': [
                'id', 'date', 'meal_type', 'description', 'calories',
                'quantity', 'notes', 'created_at'
            ]
        }

        for sheet_name, headers in required_sheets.items():
            try:
                worksheet = self.spreadsheet.worksheet(sheet_name)
                # 检查是否需要添加表头
                if not worksheet.row_values(1):
                    worksheet.append_row(headers)
            except gspread.exceptions.WorksheetNotFound:
                # 创建新工作表
                worksheet = self.spreadsheet.add_worksheet(
                    title=sheet_name,
                    rows=1000,
                    cols=len(headers)
                )
                worksheet.append_row(headers)
                print(f"Created worksheet: {sheet_name}")

    def _sync_main_data(self, records: List[Dict[str, Any]]):
        """同步主健康数据"""
        worksheet = self.spreadsheet.worksheet('健康记录')

        # 获取现有数据
        existing_data = worksheet.get_all_records()
        existing_dates = {row['date']: idx + 2 for idx, row in enumerate(existing_data)}

        for record in records:
            # 按照原有字段顺序构建数据行
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

            date = record.get('date')
            if date in existing_dates:
                # 更新现有行
                row_num = existing_dates[date]
                # 更新整行（A到AJ列，共36列）
                end_col = chr(ord('A') + len(row_data) - 1)
                worksheet.update(f'A{row_num}:{end_col}{row_num}', [row_data])
            else:
                # 添加新行
                worksheet.append_row(row_data)

    def _sync_exercises(self, records: List[Dict[str, Any]]):
        """同步运动数据"""
        worksheet = self.spreadsheet.worksheet('运动记录')

        # 收集所有运动记录
        all_exercises = []
        for record in records:
            date = record.get('date')
            for exercise in record.get('exercises', []):
                all_exercises.append([
                    exercise.get('id', ''),
                    date,
                    exercise.get('type', ''),
                    exercise.get('duration', ''),
                    exercise.get('distance', ''),
                    exercise.get('intensity', ''),
                    exercise.get('calories', ''),
                    exercise.get('avg_heart_rate', ''),
                    exercise.get('max_heart_rate', ''),
                    exercise.get('avg_pace', ''),
                    exercise.get('training_load', ''),
                    exercise.get('feeling', ''),
                    exercise.get('notes', ''),
                    exercise.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                ])

        if all_exercises:
            # 获取现有数据
            existing_data = worksheet.get_all_values()
            # ex[1] 是 date（第2列，因为第1列是id）
            dates_to_sync = {ex[1] for ex in all_exercises}

            # 删除要更新日期的旧记录
            rows_to_delete = []
            for idx, row in enumerate(existing_data[1:], start=2):  # 跳过表头
                # row[1] 是 date 列
                if len(row) > 1 and row[1] in dates_to_sync:
                    rows_to_delete.append(idx)

            # 从后往前删除，避免索引变化
            for row_num in sorted(rows_to_delete, reverse=True):
                worksheet.delete_rows(row_num)

            # 添加新记录
            if all_exercises:
                worksheet.append_rows(all_exercises)

    def _sync_meals(self, records: List[Dict[str, Any]]):
        """同步饮食数据"""
        worksheet = self.spreadsheet.worksheet('饮食记录')

        # 收集所有餐食记录
        all_meals = []
        for record in records:
            date = record.get('date')
            for meal in record.get('meals', []):
                all_meals.append([
                    meal.get('id', ''),
                    date,
                    meal.get('meal_type', ''),
                    meal.get('description', ''),
                    meal.get('calories', ''),
                    meal.get('quantity', ''),
                    meal.get('notes', ''),
                    meal.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                ])

        if all_meals:
            # 获取现有数据
            existing_data = worksheet.get_all_values()
            # meal[1] 是 date（第2列，因为第1列是id）
            dates_to_sync = {meal[1] for meal in all_meals}

            # 删除要更新日期的旧记录
            rows_to_delete = []
            for idx, row in enumerate(existing_data[1:], start=2):
                # row[1] 是 date 列
                if len(row) > 1 and row[1] in dates_to_sync:
                    rows_to_delete.append(idx)

            for row_num in sorted(rows_to_delete, reverse=True):
                worksheet.delete_rows(row_num)

            # 添加新记录
            if all_meals:
                worksheet.append_rows(all_meals)

    def update_statistics(self, stats: Dict[str, Any]):
        """
        更新统计信息到Google Sheets

        注意：此功能已禁用，原有系统不使用独立的统计表

        Args:
            stats: 统计数据字典
        """
        # 原有系统不使用独立的统计表，跳过此功能
        print("统计信息更新已跳过（原有系统不使用）")
        return

        try:
            worksheet = self.spreadsheet.worksheet('Statistics')

            # 清除现有数据（保留表头）
            worksheet.clear()
            worksheet.append_row(['Metric', 'Value', 'Period', 'Last Updated'])

            # 格式化统计数据
            stats_rows = []
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 体重统计
            if 'weight' in stats:
                weight = stats['weight']
                if weight.get('current'):
                    stats_rows.append(['Current Weight', f"{weight['current']} kg", f"{stats['total_days']} days", timestamp])
                if weight.get('average'):
                    stats_rows.append(['Average Weight', f"{weight['average']:.1f} kg", f"{stats['total_days']} days", timestamp])
                if weight.get('change'):
                    stats_rows.append(['Weight Change', f"{weight['change']:+.1f} kg", f"{stats['total_days']} days", timestamp])

            # 睡眠统计
            if 'sleep' in stats:
                sleep = stats['sleep']
                if sleep.get('average_duration'):
                    stats_rows.append(['Average Sleep', f"{sleep['average_duration']:.1f} hours", f"{stats['total_days']} days", timestamp])

            # 运动统计
            if 'exercise' in stats:
                exercise = stats['exercise']
                stats_rows.append(['Total Exercise Time', f"{exercise['total_minutes']} min", f"{stats['total_days']} days", timestamp])
                stats_rows.append(['Exercise Sessions', f"{exercise['total_sessions']}", f"{stats['total_days']} days", timestamp])

            # 添加到表格
            if stats_rows:
                worksheet.append_rows(stats_rows)

            print("Statistics updated successfully")

        except Exception as e:
            print(f"Error updating statistics: {e}")

    def get_spreadsheet_url(self) -> str:
        """获取Google Sheets的URL"""
        return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}"

    def create_new_spreadsheet(self, title: str = "Health Tracking Data") -> str:
        """
        创建新的Google Spreadsheet

        Args:
            title: 表格标题

        Returns:
            新创建的spreadsheet ID
        """
        try:
            spreadsheet = self.client.create(title)
            self.spreadsheet = spreadsheet
            self.spreadsheet_id = spreadsheet.id

            # 设置工作表
            self._ensure_worksheets()

            print(f"Created new spreadsheet: {title}")
            print(f"URL: {self.get_spreadsheet_url()}")

            return spreadsheet.id

        except Exception as e:
            print(f"Error creating spreadsheet: {e}")
            raise

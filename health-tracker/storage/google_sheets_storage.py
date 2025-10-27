"""
Google Sheets存储模块

使用Google Sheets作为云端数据源，支持多设备实时同步
"""

import gspread
from google.oauth2.service_account import Credentials
from typing import Dict, List, Any, Optional
from datetime import datetime, date
import json


class GoogleSheetsStorage:
    """Google Sheets数据存储"""

    def __init__(self, credentials_file: str, spreadsheet_id: str):
        """
        初始化Google Sheets存储

        Args:
            credentials_file: 服务账号凭据文件路径
            spreadsheet_id: Google表格ID
        """
        self.credentials_file = credentials_file
        self.spreadsheet_id = spreadsheet_id

        # 配置权限范围
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        # 加载凭据
        self.creds = Credentials.from_service_account_file(
            credentials_file,
            scopes=scopes
        )

        # 连接Google Sheets
        self.client = gspread.authorize(self.creds)
        self.spreadsheet = self.client.open_by_key(spreadsheet_id)

        # 工作表
        self.health_sheet = self._get_or_create_worksheet('健康记录')
        self.exercises_sheet = self._get_or_create_worksheet('运动记录')
        self.meals_sheet = self._get_or_create_worksheet('饮食记录')

        # 初始化表头
        self._initialize_headers()

    def _get_or_create_worksheet(self, title: str) -> gspread.Worksheet:
        """
        获取或创建工作表

        Args:
            title: 工作表名称

        Returns:
            工作表对象
        """
        try:
            worksheet = self.spreadsheet.worksheet(title)
            return worksheet
        except gspread.WorksheetNotFound:
            # 创建新工作表
            worksheet = self.spreadsheet.add_worksheet(
                title=title,
                rows=1000,
                cols=50
            )
            return worksheet

    def _initialize_headers(self):
        """初始化表头"""
        # 健康记录表头
        health_headers = [
            'date', 'weight', 'muscle_mass', 'body_fat_percentage', 'bmi',
            'basal_metabolism', 'visceral_fat_level', 'weight_feeling',
            'sleep_duration', 'sleep_start', 'sleep_end', 'sleep_quality',
            'deep_sleep_duration', 'rem_sleep_duration', 'sleep_notes',
            'urination_count', 'awake_time',
            'resting_heart_rate', 'heart_rate', 'hrv', 'blood_pressure', 'vo2_max',
            'rhr_baseline', 'hrv_baseline',
            'pain_score', 'pain_location', 'morning_stiffness_duration', 'symptoms',
            'mood', 'energy_level', 'overall_feeling',
            'steps', 'water_intake', 'health_notes',
            'created_at', 'updated_at'
        ]

        # 检查是否已有表头
        if not self.health_sheet.row_values(1):
            self.health_sheet.update('A1', [health_headers])

        # 运动记录表头
        exercise_headers = [
            'id', 'date', 'type', 'duration', 'distance', 'intensity',
            'calories', 'avg_heart_rate', 'max_heart_rate', 'avg_pace',
            'training_load', 'feeling', 'notes', 'created_at'
        ]

        if not self.exercises_sheet.row_values(1):
            self.exercises_sheet.update('A1', [exercise_headers])

        # 饮食记录表头
        meal_headers = [
            'id', 'date', 'meal_type', 'description', 'calories',
            'quantity', 'notes', 'created_at'
        ]

        if not self.meals_sheet.row_values(1):
            self.meals_sheet.update('A1', [meal_headers])

    def save_health_record(self, record: Dict[str, Any]) -> bool:
        """
        保存或更新健康记录

        Args:
            record: 健康数据字典

        Returns:
            是否成功
        """
        try:
            date_str = record.get('date')
            if not date_str:
                return False

            # 查找是否已存在该日期的记录
            dates_column = self.health_sheet.col_values(1)[1:]  # 跳过表头

            row_num = None
            for i, d in enumerate(dates_column, start=2):  # 从第2行开始
                if d == date_str:
                    row_num = i
                    break

            # 准备数据行
            data_row = self._record_to_row(record)

            if row_num:
                # 更新现有记录
                self.health_sheet.update(f'A{row_num}', [data_row])
            else:
                # 添加新记录
                self.health_sheet.append_row(data_row)

            return True

        except Exception as e:
            print(f"保存到Google Sheets失败: {e}")
            return False

    def _record_to_row(self, record: Dict[str, Any]) -> List[Any]:
        """
        将记录字典转换为表格行

        Args:
            record: 记录字典

        Returns:
            行数据列表
        """
        # 按表头顺序构建行数据
        headers = self.health_sheet.row_values(1)
        row = []

        for header in headers:
            value = record.get(header)

            # 处理特殊类型
            if value is None:
                row.append('')
            elif isinstance(value, (date, datetime)):
                row.append(value.strftime('%Y-%m-%d'))
            elif isinstance(value, (list, dict)):
                row.append(json.dumps(value, ensure_ascii=False))
            else:
                row.append(value)

        return row

    def get_health_record(self, date_str: str) -> Optional[Dict[str, Any]]:
        """
        获取指定日期的健康记录

        Args:
            date_str: 日期字符串 (YYYY-MM-DD)

        Returns:
            健康记录字典，如果不存在返回None
        """
        try:
            # 查找日期
            dates_column = self.health_sheet.col_values(1)[1:]

            for i, d in enumerate(dates_column, start=2):
                if d == date_str:
                    # 找到记录，读取整行
                    row_values = self.health_sheet.row_values(i)
                    headers = self.health_sheet.row_values(1)

                    # 转换为字典
                    record = {}
                    for j, header in enumerate(headers):
                        if j < len(row_values):
                            value = row_values[j]
                            # 空值转为None
                            if value == '':
                                record[header] = None
                            else:
                                record[header] = value
                        else:
                            record[header] = None

                    return record

            return None

        except Exception as e:
            print(f"从Google Sheets读取失败: {e}")
            return None

    def get_health_records(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取健康记录列表

        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            limit: 最大返回数量

        Returns:
            健康记录列表
        """
        try:
            # 获取所有记录
            all_values = self.health_sheet.get_all_values()

            if len(all_values) <= 1:
                return []

            headers = all_values[0]
            records = []

            for row_values in all_values[1:]:  # 跳过表头
                if not row_values or not row_values[0]:  # 跳过空行
                    continue

                # 转换为字典
                record = {}
                for j, header in enumerate(headers):
                    if j < len(row_values):
                        value = row_values[j]
                        record[header] = None if value == '' else value
                    else:
                        record[header] = None

                # 日期过滤
                record_date = record.get('date')
                if start_date and record_date < start_date:
                    continue
                if end_date and record_date > end_date:
                    continue

                records.append(record)

            # 按日期降序排序
            records.sort(key=lambda x: x.get('date', ''), reverse=True)

            # 限制数量
            if limit:
                records = records[:limit]

            return records

        except Exception as e:
            print(f"从Google Sheets读取失败: {e}")
            return []

    def delete_health_record(self, date_str: str) -> bool:
        """
        删除指定日期的健康记录

        Args:
            date_str: 日期字符串

        Returns:
            是否成功
        """
        try:
            dates_column = self.health_sheet.col_values(1)[1:]

            for i, d in enumerate(dates_column, start=2):
                if d == date_str:
                    self.health_sheet.delete_rows(i)
                    return True

            return False

        except Exception as e:
            print(f"删除记录失败: {e}")
            return False

    def batch_save_health_records(self, records: List[Dict[str, Any]], batch_size: int = 20) -> int:
        """
        批量保存健康记录（带速率限制）

        Args:
            records: 记录列表
            batch_size: 每批处理的记录数（避免API配额限制）

        Returns:
            成功保存的数量
        """
        import time

        success_count = 0
        total = len(records)

        print(f"开始批量同步 {total} 条记录...")

        # 获取现有的所有日期（只调用一次API）
        dates_column = self.health_sheet.col_values(1)[1:]
        existing_dates_map = {d: i+2 for i, d in enumerate(dates_column)}  # 日期->行号映射

        # 分批处理记录
        for batch_start in range(0, total, batch_size):
            batch_end = min(batch_start + batch_size, total)
            batch_records = records[batch_start:batch_end]

            print(f"处理第 {batch_start+1}-{batch_end} 条记录...")

            # 准备批量更新的数据
            new_rows = []
            update_data = []  # 批量更新请求

            for record in batch_records:
                date_str = record.get('date')
                if not date_str:
                    continue

                row_data = self._record_to_row(record)

                if date_str in existing_dates_map:
                    # 需要更新现有行
                    row_num = existing_dates_map[date_str]
                    # 准备批量更新请求
                    range_name = f'A{row_num}'
                    update_data.append({
                        'range': range_name,
                        'values': [row_data]
                    })
                else:
                    # 新记录
                    new_rows.append(row_data)

            try:
                # 批量添加新记录（一次API调用）
                if new_rows:
                    self.health_sheet.append_rows(new_rows)
                    success_count += len(new_rows)
                    print(f"  ✅ 新增 {len(new_rows)} 条记录")

                # 批量更新现有记录（一次API调用）
                if update_data:
                    self.health_sheet.batch_update(update_data)
                    success_count += len(update_data)
                    print(f"  ✅ 更新 {len(update_data)} 条记录")

            except Exception as e:
                print(f"  ❌ 批次失败: {e}")

            # 速率限制：每批之间暂停，避免超过配额（60次/分钟）
            if batch_end < total:
                wait_time = 15  # 每批之间等待15秒，确保不超过API配额
                print(f"  ⏳ 等待 {wait_time} 秒以避免API限速...")
                time.sleep(wait_time)

        print(f"✅ 批量同步完成！成功 {success_count}/{total} 条")
        return success_count

    def get_spreadsheet_info(self) -> Dict[str, Any]:
        """
        获取表格信息

        Returns:
            表格信息字典
        """
        return {
            'title': self.spreadsheet.title,
            'id': self.spreadsheet.id,
            'url': self.spreadsheet.url,
            'worksheets': [ws.title for ws in self.spreadsheet.worksheets()],
            'record_count': len(self.health_sheet.col_values(1)) - 1  # 减去表头
        }

    def close(self):
        """关闭连接（Google Sheets API无需显式关闭）"""
        pass

"""
数据同步管理器

协调本地SQLite数据库和Google Sheets之间的双向同步
"""

from storage.sqlite_storage import HealthDatabase
from storage.google_sheets_storage import GoogleSheetsStorage
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json


class SyncManager:
    """数据同步管理器"""

    def __init__(
        self,
        sqlite_storage: HealthDatabase,
        google_sheets_storage: Optional[GoogleSheetsStorage] = None
    ):
        """
        初始化同步管理器

        Args:
            sqlite_storage: SQLite存储对象
            google_sheets_storage: Google Sheets存储对象（可选）
        """
        self.sqlite = sqlite_storage
        self.sheets = google_sheets_storage
        self.sync_enabled = google_sheets_storage is not None

    def push_to_cloud(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        推送本地数据到云端

        Args:
            date_str: 指定日期（如果为None则同步所有数据）

        Returns:
            同步结果统计
        """
        if not self.sync_enabled:
            return {'error': 'Google Sheets未启用'}

        try:
            if date_str:
                # 同步单条记录
                record = self.sqlite.get_health_record(date_str)
                if record:
                    success = self.sheets.save_health_record(record)
                    return {
                        'success': success,
                        'synced': 1 if success else 0,
                        'failed': 0 if success else 1
                    }
                else:
                    return {'error': f'本地未找到{date_str}的记录'}
            else:
                # 同步所有记录
                records = self.sqlite.get_health_records()
                synced_count = self.sheets.batch_save_health_records(records)

                return {
                    'success': True,
                    'total': len(records),
                    'synced': synced_count,
                    'failed': len(records) - synced_count
                }

        except Exception as e:
            return {'error': str(e)}

    def pull_from_cloud(
        self,
        date_str: Optional[str] = None,
        days: Optional[int] = None,
        merge: bool = True
    ) -> Dict[str, Any]:
        """
        从云端拉取数据到本地

        Args:
            date_str: 指定日期
            days: 拉取最近N天数据
            merge: 是否合并数据（True=保留本地字段，False=完全覆盖）

        Returns:
            同步结果统计
        """
        if not self.sync_enabled:
            return {'error': 'Google Sheets未启用'}

        try:
            if date_str:
                # 拉取单条记录
                cloud_record = self.sheets.get_health_record(date_str)
                if cloud_record:
                    if merge:
                        # 合并模式：保留本地有值但云端为空的字段
                        local_record = self.sqlite.get_health_record(date_str)
                        if local_record:
                            merged_record = self._merge_records(local_record, cloud_record)
                            self.sqlite.save_health_record(merged_record)
                        else:
                            self.sqlite.save_health_record(cloud_record)
                    else:
                        # 覆盖模式
                        self.sqlite.save_health_record(cloud_record)

                    return {'success': True, 'synced': 1}
                else:
                    return {'error': f'云端未找到{date_str}的记录'}

            else:
                # 拉取多条记录
                start_date = None
                if days:
                    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

                cloud_records = self.sheets.get_health_records(start_date=start_date)

                synced = 0
                failed = 0

                for cloud_record in cloud_records:
                    try:
                        date_key = cloud_record.get('date')
                        if not date_key:
                            failed += 1
                            continue

                        if merge:
                            local_record = self.sqlite.get_health_record(date_key)
                            if local_record:
                                merged_record = self._merge_records(local_record, cloud_record)
                                self.sqlite.save_health_record(merged_record)
                            else:
                                self.sqlite.save_health_record(cloud_record)
                        else:
                            self.sqlite.save_health_record(cloud_record)

                        synced += 1

                    except Exception as e:
                        print(f"同步{cloud_record.get('date')}失败: {e}")
                        failed += 1

                return {
                    'success': True,
                    'total': len(cloud_records),
                    'synced': synced,
                    'failed': failed
                }

        except Exception as e:
            return {'error': str(e)}

    def _merge_records(
        self,
        local_record: Dict[str, Any],
        cloud_record: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        合并本地和云端记录

        策略：
        - 云端有值：使用云端值（云端优先）
        - 云端为空，本地有值：使用本地值（保留本地数据）
        - 都为空：保留空值

        Args:
            local_record: 本地记录
            cloud_record: 云端记录

        Returns:
            合并后的记录
        """
        merged = {}

        # 获取所有可能的键
        all_keys = set(local_record.keys()) | set(cloud_record.keys())

        for key in all_keys:
            cloud_value = cloud_record.get(key)
            local_value = local_record.get(key)

            # 云端优先策略
            if cloud_value is not None and cloud_value != '':
                merged[key] = cloud_value
            elif local_value is not None and local_value != '':
                merged[key] = local_value
            else:
                merged[key] = None

        return merged

    def sync_bidirectional(
        self,
        strategy: str = 'cloud_priority'
    ) -> Dict[str, Any]:
        """
        双向同步（智能合并）

        Args:
            strategy: 同步策略
                - 'cloud_priority': 云端优先
                - 'local_priority': 本地优先
                - 'latest_priority': 最新修改优先

        Returns:
            同步结果统计
        """
        if not self.sync_enabled:
            return {'error': 'Google Sheets未启用'}

        try:
            # 获取本地和云端所有记录
            local_records = {r['date']: r for r in self.sqlite.get_health_records()}
            cloud_records = {r['date']: r for r in self.sheets.get_health_records()}

            # 所有日期
            all_dates = set(local_records.keys()) | set(cloud_records.keys())

            stats = {
                'total_dates': len(all_dates),
                'pushed_to_cloud': 0,
                'pulled_from_cloud': 0,
                'merged': 0,
                'conflicts': 0
            }

            for date_key in all_dates:
                local_rec = local_records.get(date_key)
                cloud_rec = cloud_records.get(date_key)

                if local_rec and not cloud_rec:
                    # 只有本地有：推送到云端
                    self.sheets.save_health_record(local_rec)
                    stats['pushed_to_cloud'] += 1

                elif cloud_rec and not local_rec:
                    # 只有云端有：拉取到本地
                    self.sqlite.save_health_record(cloud_rec)
                    stats['pulled_from_cloud'] += 1

                elif local_rec and cloud_rec:
                    # 两边都有：需要合并
                    if strategy == 'cloud_priority':
                        merged = self._merge_records(local_rec, cloud_rec)
                        self.sqlite.save_health_record(merged)
                        stats['merged'] += 1

                    elif strategy == 'local_priority':
                        merged = self._merge_records(cloud_rec, local_rec)
                        self.sheets.save_health_record(merged)
                        stats['merged'] += 1

                    elif strategy == 'latest_priority':
                        # 比较更新时间
                        local_updated = local_rec.get('updated_at', '')
                        cloud_updated = cloud_rec.get('updated_at', '')

                        if cloud_updated >= local_updated:
                            # 云端更新
                            merged = self._merge_records(local_rec, cloud_rec)
                            self.sqlite.save_health_record(merged)
                        else:
                            # 本地更新
                            merged = self._merge_records(cloud_rec, local_rec)
                            self.sheets.save_health_record(merged)

                        stats['merged'] += 1

            stats['success'] = True
            return stats

        except Exception as e:
            return {'error': str(e)}

    def get_sync_status(self) -> Dict[str, Any]:
        """
        获取同步状态

        Returns:
            同步状态信息
        """
        if not self.sync_enabled:
            return {
                'enabled': False,
                'message': 'Google Sheets未启用'
            }

        try:
            # 获取记录数
            local_count = len(self.sqlite.get_health_records())
            cloud_count = self.sheets.get_spreadsheet_info().get('record_count', 0)

            # 获取最新记录日期
            local_records = self.sqlite.get_health_records(limit=1)
            cloud_records = self.sheets.get_health_records(limit=1)

            local_latest = local_records[0]['date'] if local_records else None
            cloud_latest = cloud_records[0]['date'] if cloud_records else None

            return {
                'enabled': True,
                'local_records': local_count,
                'cloud_records': cloud_count,
                'local_latest_date': local_latest,
                'cloud_latest_date': cloud_latest,
                'in_sync': local_count == cloud_count and local_latest == cloud_latest,
                'spreadsheet_info': self.sheets.get_spreadsheet_info()
            }

        except Exception as e:
            return {
                'enabled': True,
                'error': str(e)
            }

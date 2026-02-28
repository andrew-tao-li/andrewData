"""
Garmin 数据获取客户端

使用 garth 和 garminconnect 从 Garmin 中国云端获取健康数据
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import garth
from garminconnect import Garmin, GarminConnectAuthenticationError


class GarminClient:
    """Garmin 健康数据客户端"""

    def __init__(self, email: str, password: str, is_china: bool = True, tokens_dir: str = "data/garmin_tokens"):
        """
        初始化 Garmin 客户端

        Args:
            email: Garmin 账号邮箱
            password: Garmin 密码
            is_china: 是否使用 Garmin 中国（garmin.com.cn）
            tokens_dir: 认证令牌存储目录
        """
        self.email = email
        self.password = password
        self.is_china = is_china
        self.tokens_dir = Path(tokens_dir)
        self.tokens_dir.mkdir(parents=True, exist_ok=True)

        self.garmin = None
        self._authenticated = False

    def authenticate(self) -> bool:
        """
        认证 Garmin 账号

        Returns:
            是否认证成功
        """
        try:
            # 设置 Garmin 域名（中国 vs 国际）
            if self.is_china:
                garth.configure(domain="garmin.cn")

            # 为当前用户创建专用的 token 目录
            user_token_dir = self.tokens_dir / self.email.replace('@', '_at_')
            user_token_dir.mkdir(parents=True, exist_ok=True)

            # 尝试恢复已保存的会话
            try:
                garth.resume(str(user_token_dir))
                self.garmin = Garmin()
                self._authenticated = True
                print(f"✓ 使用已保存的令牌登录成功")
                return True
            except Exception as e:
                print(f"加载令牌失败: {e}，重新登录...")

            # 新登录
            garth.login(self.email, self.password)
            garth.save(str(user_token_dir))

            # 初始化 Garmin 客户端
            self.garmin = Garmin()
            self._authenticated = True

            print(f"✓ Garmin 认证成功: {self.email}")
            return True

        except GarminConnectAuthenticationError as e:
            print(f"✗ Garmin 认证失败: {e}")
            return False
        except Exception as e:
            print(f"✗ 认证过程出错: {e}")
            return False

    def get_sleep_data(self, date: datetime) -> Optional[Dict[str, Any]]:
        """
        获取睡眠数据

        Args:
            date: 日期

        Returns:
            睡眠数据字典，包含：
            - sleep_duration: 睡眠总时长（小时）
            - deep_sleep_duration: 深度睡眠时长（小时）
            - rem_sleep_duration: REM 睡眠时长（小时）
            - light_sleep_duration: 浅睡眠时长（小时）
            - awake_duration: 清醒时长（小时）
            - sleep_score: 睡眠评分
            - sleep_start: 入睡时间
            - sleep_end: 醒来时间
        """
        if not self._authenticated:
            print("✗ 未认证，请先调用 authenticate()")
            return None

        try:
            date_str = date.strftime("%Y-%m-%d")

            # 获取睡眠数据
            sleep_data = self.garmin.get_sleep_data(date_str)

            if not sleep_data or 'dailySleepDTO' not in sleep_data:
                print(f"⚠️  {date_str} 无睡眠数据")
                return None

            daily_sleep = sleep_data['dailySleepDTO']

            # 提取睡眠阶段数据
            sleep_levels = daily_sleep.get('sleepLevels', {})

            result = {
                'sleep_duration': round(daily_sleep.get('sleepTimeSeconds', 0) / 3600, 2),
                'deep_sleep_duration': round(sleep_levels.get('deepSleepSeconds', 0) / 3600, 2),
                'rem_sleep_duration': round(sleep_levels.get('remSleepSeconds', 0) / 3600, 2),
                'light_sleep_duration': round(sleep_levels.get('lightSleepSeconds', 0) / 3600, 2),
                'awake_duration': round(sleep_levels.get('awakeSeconds', 0) / 3600, 2),
                'sleep_score': daily_sleep.get('sleepScores', {}).get('overall', {}).get('value'),
                'sleep_start': daily_sleep.get('sleepStartTimestampLocal'),
                'sleep_end': daily_sleep.get('sleepEndTimestampLocal'),
            }

            return result

        except Exception as e:
            print(f"✗ 获取睡眠数据失败 ({date_str}): {e}")
            return None

    def get_hrv_data(self, date: datetime) -> Optional[Dict[str, Any]]:
        """
        获取 HRV（心率变异性）数据

        Args:
            date: 日期

        Returns:
            HRV 数据字典，包含：
            - hrv: 昨晚 HRV 值
            - weekly_avg: 7天平均 HRV
            - status: HRV 状态（balanced/unbalanced）
        """
        if not self._authenticated:
            print("✗ 未认证，请先调用 authenticate()")
            return None

        try:
            date_str = date.strftime("%Y-%m-%d")

            # 获取 HRV 数据
            hrv_data = self.garmin.get_hrv_data(date_str)

            if not hrv_data or 'hrvSummary' not in hrv_data:
                print(f"⚠️  {date_str} 无 HRV 数据")
                return None

            hrv_summary = hrv_data['hrvSummary']

            result = {
                'hrv': hrv_summary.get('lastNightAvg'),
                'weekly_avg': hrv_summary.get('weeklyAvg'),
                'status': hrv_summary.get('status'),  # balanced/unbalanced
            }

            return result

        except Exception as e:
            print(f"✗ 获取 HRV 数据失败 ({date_str}): {e}")
            return None

    def get_heart_rate_data(self, date: datetime) -> Optional[Dict[str, Any]]:
        """
        获取心率数据

        Args:
            date: 日期

        Returns:
            心率数据字典，包含：
            - resting_heart_rate: 静息心率
            - avg_heart_rate: 平均心率
            - max_heart_rate: 最大心率
        """
        if not self._authenticated:
            print("✗ 未认证，请先调用 authenticate()")
            return None

        try:
            date_str = date.strftime("%Y-%m-%d")

            # 获取心率数据
            heart_rate = self.garmin.get_rhr_day(date_str)

            if not heart_rate:
                print(f"⚠️  {date_str} 无心率数据")
                return None

            result = {
                'resting_heart_rate': heart_rate.get('restingHeartRate'),
                'avg_heart_rate': heart_rate.get('currentDayRestingHeartRate'),
                'max_heart_rate': heart_rate.get('maxHeartRate'),
            }

            return result

        except Exception as e:
            print(f"✗ 获取心率数据失败 ({date_str}): {e}")
            return None

    def get_activities(self, date: datetime, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取运动记录

        Args:
            date: 日期
            limit: 最多获取多少条记录

        Returns:
            运动记录列表，每条记录包含：
            - type: 运动类型（跑步、骑行、椭圆机等）
            - duration: 运动时长（分钟）
            - distance: 距离（公里）
            - calories: 卡路里
            - avg_hr: 平均心率
            - start_time: 开始时间
        """
        if not self._authenticated:
            print("✗ 未认证，请先调用 authenticate()")
            return []

        try:
            date_str = date.strftime("%Y-%m-%d")

            # 获取活动列表
            activities = self.garmin.get_activities_by_date(date_str, date_str, None)

            if not activities:
                print(f"ℹ️  {date_str} 无运动记录")
                return []

            results = []
            for activity in activities[:limit]:
                result = {
                    'type': activity.get('activityType', {}).get('typeKey', '未知'),
                    'duration': round(activity.get('duration', 0) / 60, 1),  # 秒转分钟
                    'distance': round(activity.get('distance', 0) / 1000, 2),  # 米转公里
                    'calories': activity.get('calories'),
                    'avg_hr': activity.get('averageHR'),
                    'max_hr': activity.get('maxHR'),
                    'start_time': activity.get('startTimeLocal'),
                    'activity_name': activity.get('activityName'),
                }
                results.append(result)

            print(f"✓ 获取到 {len(results)} 条运动记录")
            return results

        except Exception as e:
            print(f"✗ 获取运动数据失败 ({date_str}): {e}")
            return []

    def get_daily_summary(self, date: datetime) -> Optional[Dict[str, Any]]:
        """
        获取当天完整健康数据摘要

        Args:
            date: 日期

        Returns:
            完整健康数据，包含睡眠、HRV、心率、运动
        """
        if not self._authenticated:
            if not self.authenticate():
                return None

        print(f"\n🔍 正在获取 {date.strftime('%Y-%m-%d')} 的健康数据...")

        # 获取各项数据
        sleep = self.get_sleep_data(date)
        hrv = self.get_hrv_data(date)
        heart_rate = self.get_heart_rate_data(date)
        activities = self.get_activities(date)

        summary = {
            'date': date.strftime('%Y-%m-%d'),
            'sleep': sleep,
            'hrv': hrv,
            'heart_rate': heart_rate,
            'activities': activities,
        }

        return summary

    def validate_data(self, data: Dict[str, Any], required_fields: List[str] = None) -> bool:
        """
        验证数据完整性

        Args:
            data: 健康数据字典
            required_fields: 必需字段列表，默认为 ['sleep_duration', 'hrv']

        Returns:
            数据是否有效
        """
        if required_fields is None:
            required_fields = ['sleep_duration', 'hrv']

        missing_fields = []

        for field in required_fields:
            if field == 'sleep_duration':
                if not data.get('sleep') or data['sleep'].get('sleep_duration') is None:
                    missing_fields.append('睡眠时长')
            elif field == 'hrv':
                if not data.get('hrv') or data['hrv'].get('hrv') is None:
                    missing_fields.append('HRV')

        if missing_fields:
            print(f"✗ 数据验证失败：缺少 {', '.join(missing_fields)}")
            return False

        print(f"✓ 数据验证通过")
        return True


# 运动类型中文映射
ACTIVITY_TYPE_MAP = {
    'running': '跑步',
    'cycling': '骑行',
    'walking': '步行',
    'hiking': '徒步',
    'swimming': '游泳',
    'elliptical': '椭圆机',
    'strength_training': '力量训练',
    'yoga': '瑜伽',
    'cardio': '有氧运动',
    'other': '其他运动',
}


def get_activity_type_cn(type_key: str) -> str:
    """获取运动类型的中文名称"""
    return ACTIVITY_TYPE_MAP.get(type_key.lower(), type_key)

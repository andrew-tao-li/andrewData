"""
SQLite数据库存储

本地存储健康数据，支持快速查询和离线访问
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any


class HealthDatabase:
    """健康数据SQLite数据库"""

    def __init__(self, db_path: str = "health_data.db"):
        """
        初始化数据库

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.conn = None
        self._init_database()

    def _init_database(self):
        """初始化数据库表结构"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # 返回字典格式
        cursor = self.conn.cursor()

        # 主健康数据表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                weight REAL,
                body_fat_percentage REAL,
                muscle_mass REAL,
                bmi REAL,
                weight_feeling TEXT,

                sleep_duration REAL,
                sleep_start TEXT,
                sleep_end TEXT,
                sleep_quality TEXT,
                deep_sleep_duration REAL,
                sleep_notes TEXT,

                heart_rate INTEGER,
                blood_pressure TEXT,
                mood TEXT,
                energy_level TEXT,
                water_intake INTEGER,
                steps INTEGER,

                overall_feeling TEXT,
                health_notes TEXT,
                goals TEXT,

                raw_text TEXT,
                raw_json TEXT,
                has_images BOOLEAN,
                image_count INTEGER,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                synced_to_sheets BOOLEAN DEFAULT FALSE,
                last_sync_at TIMESTAMP
            )
        """)

        # 运动记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                type TEXT,
                duration INTEGER,
                distance REAL,
                intensity TEXT,
                calories INTEGER,
                feeling TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (date) REFERENCES health_records(date)
            )
        """)

        # 饮食记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                meal_type TEXT,
                description TEXT,
                calories INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (date) REFERENCES health_records(date)
            )
        """)

        # 原始笔记表（保存完整的原始数据）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                file_path TEXT,
                content TEXT,
                metadata TEXT,
                images TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT FALSE
            )
        """)

        # Claude分析记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_range_start TEXT,
                date_range_end TEXT,
                insight_type TEXT,
                question TEXT,
                analysis TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_date ON health_records(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_exercises_date ON exercises(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meals_date ON meals(date)")

        self.conn.commit()

    def save_health_record(self, data: Dict[str, Any]) -> bool:
        """
        保存健康记录

        Args:
            data: 健康数据字典

        Returns:
            是否保存成功
        """
        try:
            date = data.get('processed_date') or data.get('date')
            if not date:
                print("Error: No date provided")
                return False

            cursor = self.conn.cursor()

            # 检查是否已存在该日期的记录
            cursor.execute("SELECT id FROM health_records WHERE date = ?", (date,))
            existing = cursor.fetchone()

            # 准备主记录数据
            record_data = {
                'date': date,
                'weight': data.get('weight'),
                'body_fat_percentage': data.get('body_fat_percentage'),
                'muscle_mass': data.get('muscle_mass'),
                'bmi': data.get('bmi'),
                'weight_feeling': data.get('weight_feeling'),
                'sleep_duration': data.get('sleep_duration'),
                'sleep_start': data.get('sleep_start'),
                'sleep_end': data.get('sleep_end'),
                'sleep_quality': str(data.get('sleep_quality')) if data.get('sleep_quality') else None,
                'deep_sleep_duration': data.get('deep_sleep_duration'),
                'sleep_notes': data.get('sleep_notes'),
                'heart_rate': data.get('heart_rate'),
                'blood_pressure': data.get('blood_pressure'),
                'mood': str(data.get('mood')) if data.get('mood') else None,
                'energy_level': str(data.get('energy_level')) if data.get('energy_level') else None,
                'water_intake': data.get('water_intake'),
                'steps': data.get('steps'),
                'overall_feeling': data.get('overall_feeling'),
                'health_notes': data.get('health_notes'),
                'goals': data.get('goals'),
                'raw_text': data.get('raw_text'),
                'raw_json': json.dumps(data, ensure_ascii=False),
                'has_images': data.get('has_images', False),
                'image_count': data.get('image_count', 0),
                'updated_at': datetime.now().isoformat()
            }

            if existing:
                # 更新现有记录
                set_clause = ', '.join([f"{k} = ?" for k in record_data.keys() if k != 'date'])
                values = [v for k, v in record_data.items() if k != 'date']
                values.append(date)

                cursor.execute(f"""
                    UPDATE health_records
                    SET {set_clause}
                    WHERE date = ?
                """, values)
            else:
                # 插入新记录
                columns = ', '.join(record_data.keys())
                placeholders = ', '.join(['?' for _ in record_data])
                cursor.execute(f"""
                    INSERT INTO health_records ({columns})
                    VALUES ({placeholders})
                """, list(record_data.values()))

            # 保存运动记录
            if 'exercises' in data and data['exercises']:
                # 删除旧的运动记录
                cursor.execute("DELETE FROM exercises WHERE date = ?", (date,))

                for exercise in data['exercises']:
                    cursor.execute("""
                        INSERT INTO exercises
                        (date, type, duration, distance, intensity, calories, feeling, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        date,
                        exercise.get('type'),
                        exercise.get('duration'),
                        exercise.get('distance'),
                        exercise.get('intensity'),
                        exercise.get('calories'),
                        exercise.get('feeling'),
                        exercise.get('notes')
                    ))

            # 保存饮食记录
            if 'meals' in data and data['meals']:
                # 删除旧的饮食记录
                cursor.execute("DELETE FROM meals WHERE date = ?", (date,))

                for meal in data['meals']:
                    cursor.execute("""
                        INSERT INTO meals
                        (date, meal_type, description, calories, notes)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        date,
                        meal.get('meal_type'),
                        meal.get('description'),
                        meal.get('calories'),
                        meal.get('notes')
                    ))

            self.conn.commit()
            return True

        except Exception as e:
            print(f"Error saving health record: {e}")
            self.conn.rollback()
            return False

    def get_record_by_date(self, date: str) -> Optional[Dict[str, Any]]:
        """
        获取指定日期的记录

        Args:
            date: 日期字符串 (YYYY-MM-DD)

        Returns:
            健康记录字典，不存在则返回None
        """
        cursor = self.conn.cursor()

        # 获取主记录
        cursor.execute("SELECT * FROM health_records WHERE date = ?", (date,))
        record = cursor.fetchone()

        if not record:
            return None

        result = dict(record)

        # 获取运动记录
        cursor.execute("SELECT * FROM exercises WHERE date = ?", (date,))
        exercises = [dict(row) for row in cursor.fetchall()]
        result['exercises'] = exercises

        # 获取饮食记录
        cursor.execute("SELECT * FROM meals WHERE date = ?", (date,))
        meals = [dict(row) for row in cursor.fetchall()]
        result['meals'] = meals

        return result

    def get_records_by_range(
        self,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """
        获取日期范围内的记录

        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            健康记录列表
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM health_records
            WHERE date BETWEEN ? AND ?
            ORDER BY date DESC
        """, (start_date, end_date))

        records = []
        for row in cursor.fetchall():
            record = dict(row)
            date = record['date']

            # 获取运动记录
            cursor.execute("SELECT * FROM exercises WHERE date = ?", (date,))
            record['exercises'] = [dict(r) for r in cursor.fetchall()]

            # 获取饮食记录
            cursor.execute("SELECT * FROM meals WHERE date = ?", (date,))
            record['meals'] = [dict(r) for r in cursor.fetchall()]

            records.append(record)

        return records

    def get_recent_records(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取最近N天的记录

        Args:
            days: 天数

        Returns:
            健康记录列表
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)

        return self.get_records_by_range(
            start_date.isoformat(),
            end_date.isoformat()
        )

    def save_raw_note(self, note_data: Dict[str, Any]) -> bool:
        """
        保存原始笔记数据

        Args:
            note_data: 笔记数据

        Returns:
            是否保存成功
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO raw_notes
                (date, file_path, content, metadata, images, tags)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                note_data.get('date'),
                note_data.get('file_path'),
                note_data.get('content'),
                json.dumps(note_data.get('metadata', {})),
                json.dumps(note_data.get('images', [])),
                json.dumps(note_data.get('tags', []))
            ))
            self.conn.commit()
            return True

        except Exception as e:
            print(f"Error saving raw note: {e}")
            return False

    def save_insight(
        self,
        analysis: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        insight_type: str = "general",
        question: Optional[str] = None
    ) -> bool:
        """
        保存Claude分析结果

        Args:
            analysis: 分析文本
            start_date: 开始日期
            end_date: 结束日期
            insight_type: 洞察类型
            question: 用户问题

        Returns:
            是否保存成功
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO insights
                (date_range_start, date_range_end, insight_type, question, analysis)
                VALUES (?, ?, ?, ?, ?)
            """, (start_date, end_date, insight_type, question, analysis))
            self.conn.commit()
            return True

        except Exception as e:
            print(f"Error saving insight: {e}")
            return False

    def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        获取统计数据

        Args:
            days: 统计天数

        Returns:
            统计信息字典
        """
        records = self.get_recent_records(days)

        if not records:
            return {}

        # 提取各项指标
        weights = [r['weight'] for r in records if r.get('weight')]
        sleep_durations = [r['sleep_duration'] for r in records if r.get('sleep_duration')]

        # 计算运动总时长
        total_exercise_minutes = 0
        for record in records:
            for exercise in record.get('exercises', []):
                if exercise.get('duration'):
                    total_exercise_minutes += exercise['duration']

        stats = {
            'total_days': len(records),
            'days_with_data': len([r for r in records if r.get('weight') or r.get('sleep_duration')]),
            'weight': {
                'current': weights[0] if weights else None,
                'average': sum(weights) / len(weights) if weights else None,
                'min': min(weights) if weights else None,
                'max': max(weights) if weights else None,
                'change': weights[0] - weights[-1] if len(weights) >= 2 else None
            },
            'sleep': {
                'average_duration': sum(sleep_durations) / len(sleep_durations) if sleep_durations else None,
                'min_duration': min(sleep_durations) if sleep_durations else None,
                'max_duration': max(sleep_durations) if sleep_durations else None
            },
            'exercise': {
                'total_minutes': total_exercise_minutes,
                'average_per_day': total_exercise_minutes / days if total_exercise_minutes > 0 else 0,
                'total_sessions': sum(len(r.get('exercises', [])) for r in records)
            }
        }

        return stats

    def mark_as_synced(self, date: str):
        """标记记录已同步到Google Sheets"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE health_records
            SET synced_to_sheets = TRUE, last_sync_at = ?
            WHERE date = ?
        """, (datetime.now().isoformat(), date))
        self.conn.commit()

    def get_unsynced_records(self) -> List[Dict[str, Any]]:
        """获取未同步的记录"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM health_records
            WHERE synced_to_sheets = FALSE OR synced_to_sheets IS NULL
            ORDER BY date
        """)

        records = []
        for row in cursor.fetchall():
            record = dict(row)
            date = record['date']

            cursor.execute("SELECT * FROM exercises WHERE date = ?", (date,))
            record['exercises'] = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT * FROM meals WHERE date = ?", (date,))
            record['meals'] = [dict(r) for r in cursor.fetchall()]

            records.append(record)

        return records

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

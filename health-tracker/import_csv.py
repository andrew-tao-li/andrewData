#!/usr/bin/env python3
"""
从CSV导入历史健康数据

支持：
- 一天多行数据自动合并（晨测、运动、饮食）
- 时间格式转换（h:m → 小时数）
- 空列自动清理
- 冲突处理（跳过或更新）
"""

import pandas as pd
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import re


class HealthDataImporter:
    """健康数据CSV导入器"""

    def __init__(self, db_path: str = "data/health.db"):
        """
        初始化导入器

        Args:
            db_path: SQLite数据库路径
        """
        self.db_path = db_path

        # 确保数据库目录存在
        db_dir = Path(db_path).parent
        if db_dir and not db_dir.exists():
            db_dir.mkdir(parents=True, exist_ok=True)
            print(f"创建数据库目录: {db_dir}")

        self.conn = sqlite3.connect(db_path)

        # 字段映射：CSV列名 → 数据库字段名
        self.field_mapping = {
            # 体重相关
            '体重(kg)': 'weight',
            '肌肉(kg)': 'muscle_mass',
            '基代(kcal)': 'basal_metabolism',
            '内脏脂肪等级': 'visceral_fat_level',

            # 睡眠相关
            '睡眠(h:m)': 'sleep_duration',
            '深睡(h:m)': 'deep_sleep_duration',
            'REM(h:m)': 'rem_sleep_duration',
            '排尿(次)': 'urination_count',
            '清醒(min)': 'awake_time',

            # 心血管相关
            '静息HR': 'resting_heart_rate',
            'HRV': 'hrv',
            'RHR基线(bpm)': 'rhr_baseline',
            'HRV基线(ms)': 'hrv_baseline',

            # 疼痛和症状
            '离心提踵-疼痛评分(0-10)': 'pain_score',
            '晨僵持续时间(分钟)': 'morning_stiffness_duration',
            '最疼部位': 'pain_location',

            # 备注（QA备注也合并到health_notes）
            '备注': 'health_notes',
            'QA备注': 'health_notes',
        }

    def parse_time_duration(self, time_str: str) -> Optional[float]:
        """
        解析时间格式为小时数

        支持:
        - "7:16" (h:m) → 7.27
        - "1:30" (h:m) → 1.5
        - "30:07" (m:s) → 0.502
        - "0:30:07" (h:m:s) → 0.502

        Args:
            time_str: 时间字符串

        Returns:
            小时数，如果无法解析返回 None
        """
        if pd.isna(time_str) or str(time_str).strip() == '':
            return None

        time_str = str(time_str).strip()

        try:
            parts = time_str.split(':')

            if len(parts) == 2:
                # h:m 格式（如 "7:16" 或 "1:30"）
                h_or_m = int(parts[0])
                m_or_s = int(parts[1])

                # 判断是 h:m 还是 m:s
                if h_or_m < 24 and m_or_s < 60:
                    # 大概率是 h:m
                    return h_or_m + m_or_s / 60.0
                else:
                    # 可能是 m:s
                    return h_or_m / 60.0 + m_or_s / 3600.0

            elif len(parts) == 3:
                # h:m:s 格式
                h = int(parts[0])
                m = int(parts[1])
                s = int(parts[2])
                return h + m / 60.0 + s / 3600.0

            else:
                return None

        except (ValueError, AttributeError):
            return None

    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清理DataFrame

        - 删除完全为空的列
        - 删除 Unnamed 列
        - 删除重复列

        Args:
            df: 原始DataFrame

        Returns:
            清理后的DataFrame
        """
        print("\n清理数据...")

        # 删除完全为空的列
        empty_cols = df.columns[df.isna().all()].tolist()
        if empty_cols:
            print(f"删除完全为空的列: {len(empty_cols)}个")
            df = df.drop(columns=empty_cols)

        # 删除 Unnamed 列
        unnamed_cols = [col for col in df.columns if 'Unnamed' in str(col)]
        if unnamed_cols:
            print(f"删除 Unnamed 列: {len(unnamed_cols)}个")
            df = df.drop(columns=unnamed_cols)

        # 删除重复列（如 HRV基线偏差(ms)__dup1）
        dup_cols = [col for col in df.columns if '__dup' in str(col)]
        if dup_cols:
            print(f"删除重复列: {len(dup_cols)}个")
            df = df.drop(columns=dup_cols)

        print(f"清理后剩余列数: {len(df.columns)}")

        return df

    def parse_date(self, date_str: str) -> Optional[str]:
        """
        解析日期字符串

        Args:
            date_str: 日期字符串

        Returns:
            标准格式日期 YYYY-MM-DD
        """
        if pd.isna(date_str):
            return None

        try:
            date_obj = pd.to_datetime(date_str)
            return date_obj.strftime('%Y-%m-%d')
        except:
            return None

    def extract_morning_data(self, group: pd.DataFrame) -> Dict[str, Any]:
        """
        从同一天的多行数据中提取晨测数据

        Args:
            group: 同一天的所有行

        Returns:
            晨测数据字典
        """
        data = {}

        # 找到包含体重数据的行（晨测行）
        morning_rows = group[group['体重(kg)'].notna()]

        if morning_rows.empty:
            # 如果没有明确的晨测行，尝试从所有行中提取
            morning_rows = group

        # 合并所有行的数据（优先取第一个非空值）
        for csv_col, db_col in self.field_mapping.items():
            if csv_col not in group.columns:
                continue

            # 跳过备注字段（在后面单独处理）
            if csv_col in ['备注', 'QA备注']:
                continue

            # 获取第一个非空值
            values = morning_rows[csv_col].dropna()
            if not values.empty:
                value = values.iloc[0]

                # 时间格式转换
                if csv_col in ['睡眠(h:m)', '深睡(h:m)', 'REM(h:m)']:
                    value = self.parse_time_duration(value)
                    if value is None:
                        continue

                # 清醒时间（分钟转小时）
                elif csv_col == '清醒(min)' and pd.notna(value):
                    value = float(value) / 60.0

                data[db_col] = value

        # 合并备注
        notes = []
        if '备注' in group.columns:
            note_values = group['备注'].dropna().unique()
            notes.extend([str(n) for n in note_values])
        if 'QA备注' in group.columns:
            qa_values = group['QA备注'].dropna().unique()
            notes.extend([str(n) for n in qa_values])

        if notes:
            data['health_notes'] = '; '.join(notes)

        return data

    def extract_exercises(self, group: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        从同一天的多行数据中提取运动数据

        Args:
            group: 同一天的所有行

        Returns:
            运动记录列表
        """
        exercises = []

        # 找到包含运动数据的行
        exercise_rows = group[group['运动-项目'].notna()]

        for _, row in exercise_rows.iterrows():
            exercise = {
                'type': row.get('运动-项目'),
            }

            # 时长
            if pd.notna(row.get('运动-时长(h:m:s)')):
                duration = self.parse_time_duration(row['运动-时长(h:m:s)'])
                if duration:
                    exercise['duration'] = round(duration * 60, 1)  # 转为分钟

            # 距离
            if pd.notna(row.get('运动-估算距离(km)')):
                exercise['distance'] = float(row['运动-估算距离(km)'])

            # 心率
            if pd.notna(row.get('运动-平均HR(bpm)')):
                exercise['avg_heart_rate'] = int(row['运动-平均HR(bpm)'])
            if pd.notna(row.get('运动-最大HR(bpm)')):
                exercise['max_heart_rate'] = int(row['运动-最大HR(bpm)'])

            # 配速
            if pd.notna(row.get('运动-平均配速(min/km)')):
                exercise['avg_pace'] = str(row['运动-平均配速(min/km)'])

            # 训练负荷
            if pd.notna(row.get('运动-训练负荷')):
                exercise['training_load'] = float(row['运动-训练负荷'])

            # 备注（从"类别"或"备注"列）
            notes = []
            if pd.notna(row.get('类别')):
                notes.append(str(row['类别']))
            if pd.notna(row.get('备注')):
                notes.append(str(row['备注']))
            if notes:
                exercise['notes'] = ', '.join(notes)

            exercises.append(exercise)

        return exercises

    def extract_meals(self, group: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        从同一天的多行数据中提取饮食数据

        Args:
            group: 同一天的所有行

        Returns:
            饮食记录列表
        """
        meals = []

        # 找到包含饮食数据的行（行为 = 摄入）
        meal_rows = group[group['行为'] == '摄入']

        for _, row in meal_rows.iterrows():
            meal = {}

            # 食物名称（从"类别"列）
            if pd.notna(row.get('类别')):
                meal['description'] = str(row['类别'])

            # 热量
            if pd.notna(row.get('热量')):
                meal['calories'] = float(row['热量'])

            # 数量
            if pd.notna(row.get('数量')):
                meal['quantity'] = float(row['数量'])

            # 备注
            if pd.notna(row.get('备注')):
                meal['notes'] = str(row['备注'])

            if meal:  # 只添加非空记录
                meals.append(meal)

        return meals

    def merge_daily_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        按日期合并同一天的多行数据

        Args:
            df: 原始DataFrame

        Returns:
            每天一条记录的列表
        """
        print("\n按日期合并数据...")

        # 解析日期
        df['日期_parsed'] = df['日期'].apply(self.parse_date)
        df = df[df['日期_parsed'].notna()]

        # 按日期分组
        grouped = df.groupby('日期_parsed')

        merged_data = []

        for date, group in grouped:
            record = {'date': date}

            # 提取晨测数据
            morning_data = self.extract_morning_data(group)
            record.update(morning_data)

            # 提取运动数据
            exercises = self.extract_exercises(group)
            if exercises:
                record['exercises'] = json.dumps(exercises, ensure_ascii=False)

            # 提取饮食数据
            meals = self.extract_meals(group)
            if meals:
                record['meals'] = json.dumps(meals, ensure_ascii=False)

            merged_data.append(record)

        print(f"合并后记录数: {len(merged_data)}条")

        return merged_data

    def import_data(self, csv_file: str, skip_existing: bool = True, dry_run: bool = False):
        """
        导入CSV数据到数据库

        Args:
            csv_file: CSV文件路径
            skip_existing: 是否跳过已存在的日期（True=跳过，False=更新）
            dry_run: 是否只预览不实际导入
        """
        print(f"\n{'='*60}")
        print(f"开始导入CSV数据: {csv_file}")
        print(f"{'='*60}")

        # 读取CSV
        print("\n读取CSV文件...")
        df = pd.read_csv(csv_file)
        print(f"原始数据: {len(df)}行, {len(df.columns)}列")

        # 清理数据
        df = self.clean_dataframe(df)

        # 合并同一天的数据
        merged_data = self.merge_daily_data(df)

        if not merged_data:
            print("\n⚠️  没有可导入的数据")
            return

        # 预览数据
        print(f"\n预览前3条记录:")
        print("-" * 60)
        for i, record in enumerate(merged_data[:3], 1):
            print(f"\n记录 {i}: {record.get('date')}")
            for key, value in record.items():
                if key != 'date' and value is not None:
                    if isinstance(value, str) and len(value) > 50:
                        print(f"  {key}: {value[:50]}...")
                    else:
                        print(f"  {key}: {value}")

        if dry_run:
            print("\n[DRY RUN] 预览模式，不会实际导入数据")
            return

        # 导入数据
        print(f"\n开始导入 {len(merged_data)} 条记录...")

        imported = 0
        skipped = 0
        updated = 0
        errors = 0

        cursor = self.conn.cursor()

        for record in merged_data:
            date = record.get('date')
            if not date:
                continue

            try:
                # 检查是否已存在
                cursor.execute("SELECT date FROM health_records WHERE date = ?", (date,))
                exists = cursor.fetchone()

                if exists:
                    if skip_existing:
                        skipped += 1
                        continue
                    else:
                        # 更新模式
                        update_fields = []
                        update_values = []
                        for key, value in record.items():
                            if key != 'date':
                                update_fields.append(f"{key} = ?")
                                update_values.append(value)

                        if update_fields:
                            update_values.append(date)
                            sql = f"UPDATE health_records SET {', '.join(update_fields)} WHERE date = ?"
                            cursor.execute(sql, update_values)
                            updated += 1
                else:
                    # 插入新记录
                    fields = list(record.keys())
                    placeholders = ', '.join(['?' for _ in fields])
                    sql = f"INSERT INTO health_records ({', '.join(fields)}) VALUES ({placeholders})"
                    cursor.execute(sql, [record[f] for f in fields])
                    imported += 1

            except Exception as e:
                print(f"  ❌ 导入失败 {date}: {e}")
                errors += 1

        self.conn.commit()

        # 统计结果
        print(f"\n{'='*60}")
        print(f"导入完成!")
        print(f"{'='*60}")
        print(f"✓ 新增: {imported} 条")
        if not skip_existing:
            print(f"✓ 更新: {updated} 条")
        print(f"⊙ 跳过: {skipped} 条 (已存在)")
        if errors > 0:
            print(f"✗ 错误: {errors} 条")

    def close(self):
        """关闭数据库连接"""
        self.conn.close()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='导入CSV健康数据到SQLite数据库')
    parser.add_argument('csv_file', help='CSV文件路径')
    parser.add_argument('--db', default='data/health.db', help='数据库路径')
    parser.add_argument('--update', action='store_true', help='更新已存在的记录（默认跳过）')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际导入')

    args = parser.parse_args()

    # 创建导入器
    importer = HealthDataImporter(db_path=args.db)

    try:
        # 导入数据
        importer.import_data(
            csv_file=args.csv_file,
            skip_existing=not args.update,
            dry_run=args.dry_run
        )
    finally:
        importer.close()


if __name__ == '__main__':
    main()

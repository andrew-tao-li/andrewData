#!/usr/bin/env python3
"""
初始化健康追踪数据库

创建所有必要的表结构
"""

import sqlite3
from pathlib import Path


def init_database(db_path: str = "data/health.db"):
    """初始化数据库表结构"""

    # 确保目录存在
    db_dir = Path(db_path).parent
    if db_dir and not db_dir.exists():
        db_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ 创建数据库目录: {db_dir}")

    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"\n初始化数据库: {db_path}\n")

    # 创建健康记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS health_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,

            -- 体重相关
            weight REAL,
            muscle_mass REAL,
            body_fat_percentage REAL,
            bmi REAL,
            basal_metabolism INTEGER,
            visceral_fat_level INTEGER,
            weight_feeling TEXT,

            -- 睡眠相关
            sleep_duration REAL,
            sleep_start TEXT,
            sleep_end TEXT,
            sleep_quality TEXT,
            deep_sleep_duration REAL,
            rem_sleep_duration REAL,
            sleep_notes TEXT,
            urination_count INTEGER,
            awake_time REAL,

            -- 心血管相关
            resting_heart_rate INTEGER,
            heart_rate INTEGER,
            hrv INTEGER,
            blood_pressure TEXT,
            vo2_max INTEGER,
            rhr_baseline INTEGER,
            hrv_baseline INTEGER,

            -- 疼痛和症状
            pain_score INTEGER,
            pain_location TEXT,
            morning_stiffness_duration INTEGER,
            symptoms TEXT,

            -- 主观感受
            mood TEXT,
            energy_level TEXT,
            overall_feeling TEXT,

            -- 其他指标
            steps INTEGER,
            water_intake INTEGER,
            health_notes TEXT,

            -- 运动和饮食（JSON格式）
            exercises TEXT,
            meals TEXT,

            -- 元数据
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            synced_at TEXT
        )
    ''')

    print("✓ 创建表: health_records")

    # 创建索引
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_date ON health_records(date)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_created_at ON health_records(created_at)
    ''')

    print("✓ 创建索引: idx_date, idx_created_at")

    # 提交并关闭
    conn.commit()
    conn.close()

    print(f"\n✅ 数据库初始化完成！\n")
    print(f"数据库路径: {Path(db_path).absolute()}")
    print(f"\n现在可以导入CSV数据了:")
    print(f'  python import_csv.py "热量赤字-明细-1026.csv"')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='初始化健康追踪数据库')
    parser.add_argument('--db', default='data/health.db', help='数据库路径')

    args = parser.parse_args()

    init_database(args.db)

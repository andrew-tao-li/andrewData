#!/usr/bin/env python3
"""
数据库Schema同步脚本

自动检测并添加所有缺失的字段，确保本地数据库与最新schema一致
"""

import sqlite3
from pathlib import Path
import json


def load_config():
    """加载配置"""
    config_path = Path(__file__).parent / "config" / "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_current_columns(conn, table_name):
    """获取当前表的所有列"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = {row[1]: row[2] for row in cursor.fetchall()}  # {column_name: type}
    return columns


def sync_database_schema(db_path="data/health.db"):
    """同步数据库Schema"""

    print("=" * 60)
    print("🔄 数据库Schema同步")
    print("=" * 60)
    print()

    if not Path(db_path).exists():
        print(f"❌ 数据库不存在: {db_path}")
        print("   请先运行: python init_database.py")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 定义完整的schema（最新版本）
    expected_schema = {
        'health_records': {
            # 基础
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'date': 'TEXT NOT NULL UNIQUE',

            # 体重相关
            'weight': 'REAL',
            'body_fat_percentage': 'REAL',
            'muscle_mass': 'REAL',
            'bmi': 'REAL',
            'basal_metabolism': 'INTEGER',
            'visceral_fat_level': 'INTEGER',
            'weight_feeling': 'TEXT',

            # 睡眠相关
            'sleep_duration': 'REAL',
            'sleep_start': 'TEXT',
            'sleep_end': 'TEXT',
            'sleep_quality': 'TEXT',
            'deep_sleep_duration': 'REAL',
            'rem_sleep_duration': 'REAL',
            'sleep_notes': 'TEXT',
            'urination_count': 'INTEGER',
            'awake_time': 'REAL',

            # 心血管相关
            'heart_rate': 'INTEGER',
            'resting_heart_rate': 'INTEGER',
            'hrv': 'INTEGER',
            'blood_pressure': 'TEXT',
            'vo2_max': 'INTEGER',
            'rhr_baseline': 'INTEGER',
            'hrv_baseline': 'INTEGER',

            # 主观感受
            'mood': 'TEXT',
            'energy_level': 'TEXT',
            'overall_feeling': 'TEXT',

            # 其他指标
            'water_intake': 'INTEGER',
            'steps': 'INTEGER',

            # 疼痛和症状
            'pain_score': 'INTEGER',
            'pain_location': 'TEXT',
            'morning_stiffness_duration': 'INTEGER',
            'symptoms': 'TEXT',

            # 目标和备注
            'health_notes': 'TEXT',
            'goals': 'TEXT',  # ← 缺失的字段

            # 原始数据
            'raw_text': 'TEXT',
            'raw_json': 'TEXT',
            'has_images': 'BOOLEAN',
            'image_count': 'INTEGER',

            # 元数据
            'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'synced_to_sheets': 'BOOLEAN DEFAULT FALSE',
            'last_sync_at': 'TIMESTAMP'
        }
    }

    # 检查并添加缺失字段
    current_columns = get_current_columns(conn, 'health_records')
    expected_columns = expected_schema['health_records']

    missing_columns = []
    for col_name, col_type in expected_columns.items():
        if col_name not in current_columns:
            missing_columns.append((col_name, col_type))

    if not missing_columns:
        print("✅ 数据库Schema已是最新版本，无需更新")
        print(f"   当前字段数: {len(current_columns)}")
        conn.close()
        return True

    print(f"⚠️  发现 {len(missing_columns)} 个缺失字段：")
    print()

    # 添加缺失字段
    for col_name, col_type in missing_columns:
        try:
            # 提取类型和默认值
            if 'DEFAULT' in col_type.upper():
                sql = f"ALTER TABLE health_records ADD COLUMN {col_name} {col_type}"
            else:
                # 没有默认值的字段，添加时设为NULL
                sql = f"ALTER TABLE health_records ADD COLUMN {col_name} {col_type.split()[0]}"

            cursor.execute(sql)
            print(f"  ✅ 添加字段: {col_name} ({col_type.split()[0]})")

        except Exception as e:
            print(f"  ❌ 添加字段失败: {col_name} - {e}")

    conn.commit()

    # 验证
    print()
    print("🔍 验证更新结果...")
    updated_columns = get_current_columns(conn, 'health_records')

    still_missing = []
    for col_name in expected_columns:
        if col_name not in updated_columns:
            still_missing.append(col_name)

    if still_missing:
        print(f"  ⚠️  仍有 {len(still_missing)} 个字段缺失:")
        for col in still_missing:
            print(f"     - {col}")
    else:
        print(f"  ✅ 所有字段已添加")
        print(f"  📊 当前字段数: {len(updated_columns)}")

    conn.close()

    print()
    print("=" * 60)
    print("✅ Schema同步完成")
    print("=" * 60)
    print()
    print("下一步:")
    print("  1. 重新拉取云端数据: python sync_cli.py pull")
    print("  2. 查看同步状态: python sync_cli.py status")

    return len(still_missing) == 0


if __name__ == '__main__':
    import sys
    config = load_config()
    db_path = config.get('database_path', 'data/health.db')

    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    success = sync_database_schema(db_path)
    sys.exit(0 if success else 1)

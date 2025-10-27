#!/usr/bin/env python3
"""
数据库迁移脚本：添加同步相关字段

添加 synced_to_sheets 和 last_sync_at 字段到现有数据库
"""

import sqlite3
from pathlib import Path


def migrate_database(db_path: str = "data/health.db"):
    """为数据库添加同步字段"""

    if not Path(db_path).exists():
        print(f"❌ 数据库不存在: {db_path}")
        return False

    print(f"开始迁移数据库: {db_path}\n")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(health_records)")
        columns = [row[1] for row in cursor.fetchall()]

        fields_to_add = []

        if 'synced_to_sheets' not in columns:
            fields_to_add.append(('synced_to_sheets', 'BOOLEAN DEFAULT FALSE'))

        if 'last_sync_at' not in columns:
            fields_to_add.append(('last_sync_at', 'TIMESTAMP'))

        if not fields_to_add:
            print("✅ 数据库已是最新版本，无需迁移")
            return True

        # 添加缺失的字段
        for field_name, field_def in fields_to_add:
            print(f"添加字段: {field_name} {field_def}")
            cursor.execute(f"ALTER TABLE health_records ADD COLUMN {field_name} {field_def}")

        conn.commit()
        print("\n✅ 数据库迁移完成！")

        # 显示更新后的结构
        cursor.execute("PRAGMA table_info(health_records)")
        columns = cursor.fetchall()
        print(f"\n当前表结构（共{len(columns)}个字段）:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")

        return True

    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='迁移数据库添加同步字段')
    parser.add_argument('--db', default='data/health.db', help='数据库路径')

    args = parser.parse_args()

    migrate_database(args.db)

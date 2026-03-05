#!/usr/bin/env python3
"""
数据库迁移：添加hrv_night字段

为health_records表添加hrv_night列
"""

import sqlite3
import sys
from pathlib import Path


def migrate_database(db_path: str):
    """添加hrv_night字段到health_records表"""
    print(f"正在迁移数据库: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 检查列是否已存在
        cursor.execute("PRAGMA table_info(health_records)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'hrv_night' in columns:
            print("✅ hrv_night字段已存在，无需迁移")
            return True

        # 添加列
        print("📝 添加hrv_night字段...")
        cursor.execute("ALTER TABLE health_records ADD COLUMN hrv_night INTEGER")
        conn.commit()

        print("✅ 迁移成功！hrv_night字段已添加")
        return True

    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()


if __name__ == '__main__':
    # 默认数据库路径
    default_db = Path(__file__).parent / 'health_data.db'

    # 允许自定义路径
    db_path = sys.argv[1] if len(sys.argv) > 1 else str(default_db)

    if not Path(db_path).exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        sys.exit(1)

    success = migrate_database(db_path)
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
数据库迁移：添加 hrv_night 字段

HRV 数据分为两个字段：
- hrv: 七天平均 HRV (Garmin 的 weeklyAvg)
- hrv_night: 夜间平均 HRV (Garmin 的 lastNightAvg)
"""

import sqlite3
import sys

def migrate_database(db_path='health_data.db'):
    """添加 hrv_night 字段"""

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("=" * 80)
        print("数据库迁移：添加 hrv_night 字段")
        print("=" * 80)

        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(health_records)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'hrv_night' in columns:
            print("✓ hrv_night 字段已存在，无需迁移")
            conn.close()
            return True

        # 添加新字段
        print("\n正在添加 hrv_night 字段...")
        cursor.execute("""
            ALTER TABLE health_records
            ADD COLUMN hrv_night INTEGER
        """)

        conn.commit()
        print("✓ hrv_night 字段添加成功")

        # 验证
        cursor.execute("PRAGMA table_info(health_records)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'hrv_night' in columns:
            print("✓ 验证通过：字段已成功添加到数据库")
        else:
            print("✗ 验证失败：字段未添加")
            return False

        conn.close()

        print("\n" + "=" * 80)
        print("迁移完成！")
        print("=" * 80)
        print("\n说明：")
        print("- hrv: 七天平均 HRV（Garmin weeklyAvg）")
        print("- hrv_night: 夜间平均 HRV（Garmin lastNightAvg）")
        print("\n下一步：重新同步 Garmin 数据以填充新字段")

        return True

    except Exception as e:
        print(f"✗ 迁移失败: {e}")
        return False

if __name__ == '__main__':
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'health_data.db'
    success = migrate_database(db_path)
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Google Sheets连接测试脚本

测试Google Sheets API配置是否正确
"""

import json
from pathlib import Path
from storage.google_sheets_storage import GoogleSheetsStorage


def test_google_sheets():
    """测试Google Sheets连接"""

    print("\n" + "="*60)
    print("Google Sheets 连接测试")
    print("="*60 + "\n")

    # 1. 检查配置文件
    print("📋 步骤 1: 检查配置文件")
    config_file = Path('config/config.json')

    if not config_file.exists():
        print("❌ 配置文件不存在: config/config.json")
        print("请先创建配置文件并填写Google Sheets相关配置")
        return False

    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 检查必要配置
    if not config.get('google_sheets_enabled'):
        print("❌ Google Sheets未启用")
        print("请在config.json中设置: \"google_sheets_enabled\": true")
        return False

    print("✓ 配置文件存在")
    print(f"✓ Google Sheets已启用")

    # 2. 检查凭据文件
    print("\n📋 步骤 2: 检查凭据文件")
    credentials_file = config.get('google_credentials_file', 'config/credentials.json')
    credentials_path = Path(credentials_file)

    if not credentials_path.exists():
        print(f"❌ 凭据文件不存在: {credentials_file}")
        print("\n请完成以下步骤:")
        print("1. 访问 https://console.cloud.google.com/")
        print("2. 创建服务账号并下载JSON密钥文件")
        print("3. 将文件重命名为 credentials.json")
        print("4. 放到 config/ 目录下")
        return False

    print(f"✓ 凭据文件存在: {credentials_file}")

    # 3. 检查表格ID
    print("\n📋 步骤 3: 检查表格ID")
    spreadsheet_id = config.get('google_sheet_id')

    if not spreadsheet_id:
        print("❌ 未配置表格ID")
        print("请在config.json中设置: \"google_sheet_id\": \"你的表格ID\"")
        return False

    print(f"✓ 表格ID: {spreadsheet_id}")

    # 4. 测试连接
    print("\n📋 步骤 4: 测试Google Sheets连接")

    try:
        sheets = GoogleSheetsStorage(
            credentials_file=credentials_file,
            spreadsheet_id=spreadsheet_id
        )

        print("✓ 成功连接到Google Sheets")

        # 5. 获取表格信息
        print("\n📋 步骤 5: 获取表格信息")
        info = sheets.get_spreadsheet_info()

        print(f"\n表格信息:")
        print(f"  名称: {info['title']}")
        print(f"  URL: {info['url']}")
        print(f"  工作表: {', '.join(info['worksheets'])}")
        print(f"  记录数: {info['record_count']}")

        # 6. 测试写入
        print("\n📋 步骤 6: 测试写入数据")

        test_record = {
            'date': '2025-01-01',
            'weight': 70.0,
            'muscle_mass': 35.0,
            'sleep_duration': 7.5,
            'hrv': 50,
            'health_notes': 'Google Sheets测试记录'
        }

        success = sheets.save_health_record(test_record)

        if success:
            print("✓ 成功写入测试记录")

            # 7. 测试读取
            print("\n📋 步骤 7: 测试读取数据")

            retrieved = sheets.get_health_record('2025-01-01')

            if retrieved:
                print("✓ 成功读取测试记录")
                print(f"\n读取到的数据:")
                print(f"  日期: {retrieved.get('date')}")
                print(f"  体重: {retrieved.get('weight')} kg")
                print(f"  肌肉量: {retrieved.get('muscle_mass')} kg")
                print(f"  睡眠时长: {retrieved.get('sleep_duration')} 小时")
                print(f"  HRV: {retrieved.get('hrv')}")
                print(f"  备注: {retrieved.get('health_notes')}")

                # 8. 删除测试记录
                print("\n📋 步骤 8: 清理测试数据")
                deleted = sheets.delete_health_record('2025-01-01')

                if deleted:
                    print("✓ 成功删除测试记录")
                else:
                    print("⚠️  删除测试记录失败（不影响使用）")

            else:
                print("❌ 读取测试记录失败")
                return False

        else:
            print("❌ 写入测试记录失败")
            return False

        # 测试完成
        print("\n" + "="*60)
        print("✅ 所有测试通过！Google Sheets配置正确")
        print("="*60 + "\n")

        print("下一步:")
        print("  1. 导入历史数据: python import_csv.py data.csv --sync")
        print("  2. 解析笔记并同步: python cli.py parse --date 2025-10-27 --sync")
        print("  3. 查看同步状态: python cli.py sync-status")

        return True

    except FileNotFoundError as e:
        print(f"\n❌ 文件未找到: {e}")
        print("请检查凭据文件路径是否正确")
        return False

    except Exception as e:
        print(f"\n❌ 连接失败: {e}")
        print("\n可能的原因:")
        print("  1. 凭据文件格式不正确")
        print("  2. 表格ID错误")
        print("  3. 未将表格共享给服务账号邮箱")
        print("  4. Google Sheets API未启用")
        print("\n请检查配置后重试")
        return False


if __name__ == '__main__':
    test_google_sheets()

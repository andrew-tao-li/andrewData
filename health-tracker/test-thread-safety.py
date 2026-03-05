#!/usr/bin/env python3
"""
测试SQLite线程安全修复

模拟APScheduler的多线程环境，验证数据库操作的线程安全性
"""

import sys
import os
import threading
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage.sqlite_storage import HealthDatabase
from garmin.garmin_client import GarminClient


def test_thread_safety():
    """测试多线程环境下的数据库操作"""
    print("=" * 80)
    print("测试SQLite线程安全修复")
    print("=" * 80)

    # 1. 初始化数据库（主线程）
    print("\n1️⃣ 在主线程中初始化数据库...")
    db = HealthDatabase("test_thread_safety.db")
    print(f"   ✅ 数据库初始化成功（线程ID: {threading.get_ident()}）")

    # 2. 创建工作线程函数（模拟APScheduler）
    def worker_thread(thread_id: int):
        """工作线程：模拟APScheduler的任务执行"""
        try:
            print(f"\n🧵 线程 {thread_id} 启动（线程ID: {threading.get_ident()}）")

            # 模拟获取Garmin数据并保存
            test_date = (datetime.now() - timedelta(days=thread_id)).strftime('%Y-%m-%d')

            health_data = {
                'date': test_date,
                'sleep_duration': 7.5 + thread_id * 0.1,
                'hrv': 40 + thread_id,
                'resting_heart_rate': 55 + thread_id,
                'deep_sleep_duration': 2.0,
                'rem_sleep_duration': 1.5,
                'exercises': []
            }

            print(f"   🔄 线程 {thread_id} 保存数据到数据库...")
            success = db.save_health_record(health_data)

            if success:
                print(f"   ✅ 线程 {thread_id} 保存成功！日期: {test_date}")
            else:
                print(f"   ❌ 线程 {thread_id} 保存失败！")
                return False

            # 验证数据
            print(f"   🔍 线程 {thread_id} 读取数据验证...")
            record = db.get_record_by_date(test_date)

            if record:
                print(f"   ✅ 线程 {thread_id} 读取成功！HRV: {record.get('hrv')}")
                return True
            else:
                print(f"   ❌ 线程 {thread_id} 读取失败！")
                return False

        except Exception as e:
            print(f"   ❌ 线程 {thread_id} 发生错误: {e}")
            import traceback
            traceback.print_exc()
            return False

    # 3. 创建多个线程同时访问数据库
    print("\n2️⃣ 创建多个工作线程（模拟APScheduler）...")
    threads = []
    results = {}

    def thread_wrapper(tid):
        results[tid] = worker_thread(tid)

    # 创建5个线程
    for i in range(5):
        thread = threading.Thread(target=thread_wrapper, args=(i+1,))
        threads.append(thread)

    print(f"   创建了 {len(threads)} 个工作线程")

    # 4. 启动所有线程
    print("\n3️⃣ 启动所有线程...")
    for thread in threads:
        thread.start()
        time.sleep(0.1)  # 稍微错开启动时间

    # 5. 等待所有线程完成
    print("\n4️⃣ 等待所有线程完成...")
    for thread in threads:
        thread.join()

    print("\n5️⃣ 验证结果...")
    all_success = all(results.values())

    if all_success:
        print("   ✅ 所有线程都成功完成！")
    else:
        print("   ❌ 部分线程失败！")
        print(f"   结果: {results}")

    # 6. 清理
    db.close()

    # 删除测试数据库
    if os.path.exists("test_thread_safety.db"):
        os.remove("test_thread_safety.db")
        print("\n🗑️  已清理测试数据库")

    print("\n" + "=" * 80)
    if all_success:
        print("🎉 线程安全测试通过！")
        print("   SQLite修复成功，可以在APScheduler多线程环境中正常工作")
    else:
        print("❌ 线程安全测试失败！")
        print("   需要进一步修复")
    print("=" * 80)

    return all_success


def test_real_sync():
    """测试真实的Garmin同步（在线程中执行）"""
    print("\n" + "=" * 80)
    print("测试真实Garmin同步（多线程环境）")
    print("=" * 80)

    def sync_in_thread():
        """在工作线程中执行同步"""
        try:
            print(f"\n🧵 工作线程启动（线程ID: {threading.get_ident()}）")

            # 加载配置
            config_path = Path(__file__).parent / 'config' / 'config.json'
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 初始化数据库
            db = HealthDatabase(config.get('database', {}).get('path', 'health_data.db'))

            # 初始化Garmin客户端
            garmin_config = config.get('garmin', {})
            client = GarminClient(
                email=garmin_config['email'],
                password=garmin_config['password'],
                is_china=garmin_config.get('is_china', True)
            )

            # 获取昨天的数据
            target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            print(f"\n📅 目标日期: {target_date}")

            print("🔄 在线程中获取Garmin数据...")
            data = client.get_health_data(target_date)

            if data:
                print("✅ 获取数据成功")
                print(f"   睡眠时长: {data.get('sleep_duration')} 小时")
                print(f"   HRV: {data.get('hrv')}")
                print(f"   静息心率: {data.get('resting_heart_rate')}")

                print("\n🔄 在线程中保存到数据库...")
                success = db.save_health_record(data)

                if success:
                    print("✅ 保存成功！")

                    # 验证
                    print("\n🔍 验证数据...")
                    record = db.get_record_by_date(target_date)
                    if record:
                        print(f"✅ 验证成功！数据库中的HRV: {record.get('hrv')}")
                        return True
                    else:
                        print("❌ 验证失败！数据库中找不到记录")
                        return False
                else:
                    print("❌ 保存失败！")
                    return False
            else:
                print("❌ 获取数据失败")
                return False

        except Exception as e:
            print(f"❌ 线程中发生错误: {e}")
            import traceback
            traceback.print_exc()
            return False

    # 在新线程中执行
    result = [False]

    def wrapper():
        result[0] = sync_in_thread()

    thread = threading.Thread(target=wrapper)
    print("启动工作线程...")
    thread.start()
    thread.join()

    print("\n" + "=" * 80)
    if result[0]:
        print("🎉 真实同步测试通过！")
        print("   在多线程环境中成功同步Garmin数据")
    else:
        print("❌ 真实同步测试失败！")
    print("=" * 80)

    return result[0]


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("SQLite线程安全性测试套件")
    print("=" * 80)

    # 测试1：线程安全性
    print("\n【测试 1/2】模拟多线程数据库操作")
    test1_passed = test_thread_safety()

    # 测试2：真实同步
    print("\n【测试 2/2】真实Garmin同步（多线程）")
    test2_passed = test_real_sync()

    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    print(f"测试1 - 多线程数据库操作: {'✅ 通过' if test1_passed else '❌ 失败'}")
    print(f"测试2 - 真实Garmin同步: {'✅ 通过' if test2_passed else '❌ 失败'}")

    if test1_passed and test2_passed:
        print("\n🎉 所有测试通过！SQLite线程安全修复成功！")
        print("💡 现在可以重启调度器，应该能正常工作了。")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败，需要进一步调查")
        sys.exit(1)

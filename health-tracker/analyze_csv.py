#!/usr/bin/env python3
"""
CSV数据深度分析工具

在导入前全面分析CSV数据质量和覆盖率
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import json


def analyze_csv(csv_file: str):
    """
    深度分析CSV数据

    Args:
        csv_file: CSV文件路径
    """
    print(f"\n{'='*70}")
    print(f"CSV数据深度分析: {csv_file}")
    print(f"{'='*70}\n")

    # 读取CSV
    df = pd.read_csv(csv_file)
    total_rows = len(df)

    print(f"📊 基本统计")
    print(f"  总行数: {total_rows}")
    print(f"  总列数: {len(df.columns)}")

    # 解析日期
    df['日期_parsed'] = pd.to_datetime(df['日期'], errors='coerce')
    df = df[df['日期_parsed'].notna()]

    if len(df) == 0:
        print("\n❌ 没有有效的日期数据！")
        return

    # 日期范围
    date_range = (df['日期_parsed'].min(), df['日期_parsed'].max())
    days_span = (date_range[1] - date_range[0]).days + 1
    unique_dates = df['日期_parsed'].nunique()

    print(f"\n📅 日期分析")
    print(f"  日期范围: {date_range[0].strftime('%Y-%m-%d')} 至 {date_range[1].strftime('%Y-%m-%d')}")
    print(f"  跨度天数: {days_span} 天")
    print(f"  实际有数据的天数: {unique_dates} 天")
    print(f"  数据覆盖率: {unique_dates/days_span*100:.1f}%")

    # 行为类型统计
    print(f"\n📝 数据类型统计")
    if '行为' in df.columns:
        behavior_counts = df['行为'].value_counts()
        print(f"  行为类型分布:")
        for behavior, count in behavior_counts.items():
            if pd.notna(behavior):
                print(f"    - {behavior}: {count} 行 ({count/total_rows*100:.1f}%)")
        empty_behavior = df['行为'].isna().sum()
        print(f"    - (空值/晨测): {empty_behavior} 行 ({empty_behavior/total_rows*100:.1f}%)")

    # 关键健康指标覆盖率
    print(f"\n💊 健康指标覆盖率")

    health_fields = {
        '体重(kg)': '体重',
        '肌肉(kg)': '肌肉量',
        '基代(kcal)': '基础代谢',
        '睡眠(h:m)': '睡眠时长',
        '深睡(h:m)': '深睡时长',
        'REM(h:m)': 'REM睡眠',
        '静息HR': '静息心率',
        'HRV': 'HRV',
        '排尿(次)': '排尿次数',
        '内脏脂肪等级': '内脏脂肪',
        '离心提踵-疼痛评分(0-10)': '疼痛评分',
        '晨僵持续时间(分钟)': '晨僵时间',
        '最疼部位': '疼痛部位',
    }

    for col, name in health_fields.items():
        if col in df.columns:
            non_null = df[col].notna().sum()
            coverage = non_null / unique_dates * 100
            if non_null > 0:
                print(f"  ✓ {name:12s}: {non_null:3d} 条记录 ({coverage:5.1f}% 覆盖)")
        else:
            print(f"  ✗ {name:12s}: 列不存在")

    # 运动数据统计
    print(f"\n🏃 运动数据统计")
    if '运动-项目' in df.columns:
        exercise_rows = df[df['运动-项目'].notna()]
        print(f"  运动记录数: {len(exercise_rows)} 条")
        if len(exercise_rows) > 0:
            exercise_types = exercise_rows['运动-项目'].value_counts()
            print(f"  运动类型分布:")
            for ex_type, count in exercise_types.head(10).items():
                print(f"    - {ex_type}: {count} 次")
    else:
        print(f"  ✗ 无运动数据列")

    # 饮食数据统计
    print(f"\n🍽️  饮食数据统计")
    meal_rows = df[df['行为'] == '摄入']
    print(f"  饮食记录数: {len(meal_rows)} 条")
    if len(meal_rows) > 0 and '热量' in df.columns:
        total_calories = meal_rows['热量'].sum()
        avg_calories_per_day = total_calories / unique_dates
        print(f"  总热量: {total_calories:.0f} kcal")
        print(f"  平均每天摄入: {avg_calories_per_day:.0f} kcal")

    # 按时期抽样展示
    print(f"\n📈 时期抽样检查")

    # 分成早期、中期、晚期
    dates_sorted = sorted(df['日期_parsed'].unique())

    periods = [
        ("早期", dates_sorted[0]),
        ("中期", dates_sorted[len(dates_sorted)//2]),
        ("晚期", dates_sorted[-1])
    ]

    for period_name, sample_date in periods:
        sample_data = df[df['日期_parsed'] == sample_date]
        print(f"\n  {period_name} ({sample_date.strftime('%Y-%m-%d')}):")
        print(f"    该日行数: {len(sample_data)}")

        # 显示该日有哪些类型的数据
        has_weight = sample_data['体重(kg)'].notna().any() if '体重(kg)' in sample_data.columns else False
        has_sleep = sample_data['睡眠(h:m)'].notna().any() if '睡眠(h:m)' in sample_data.columns else False
        has_hrv = sample_data['HRV'].notna().any() if 'HRV' in sample_data.columns else False
        has_exercise = sample_data['运动-项目'].notna().any() if '运动-项目' in sample_data.columns else False
        has_meal = (sample_data['行为'] == '摄入').any() if '行为' in sample_data.columns else False

        data_types = []
        if has_weight: data_types.append("晨测")
        if has_sleep: data_types.append("睡眠")
        if has_hrv: data_types.append("HRV")
        if has_exercise: data_types.append("运动")
        if has_meal: data_types.append("饮食")

        print(f"    数据类型: {', '.join(data_types) if data_types else '(空)'}")

        # 显示部分数据
        if has_weight:
            weight = sample_data['体重(kg)'].dropna().iloc[0]
            print(f"      体重: {weight} kg")
        if has_hrv:
            hrv = sample_data['HRV'].dropna().iloc[0]
            print(f"      HRV: {hrv}")
        if has_exercise:
            ex = sample_data[sample_data['运动-项目'].notna()].iloc[0]
            print(f"      运动: {ex['运动-项目']}")

    # 数据质量问题检测
    print(f"\n⚠️  潜在问题检测")

    issues = []

    # 检查时间格式异常
    if '睡眠(h:m)' in df.columns:
        sleep_data = df['睡眠(h:m)'].dropna()
        for idx, val in sleep_data.items():
            val_str = str(val)
            if ':' in val_str:
                parts = val_str.split(':')
                try:
                    hours = int(parts[0])
                    if hours > 24:
                        issues.append(f"行{idx}: 睡眠时长异常 ({val})")
                except:
                    pass

    # 检查体重异常值
    if '体重(kg)' in df.columns:
        weights = df['体重(kg)'].dropna()
        if len(weights) > 0:
            weight_min = weights.min()
            weight_max = weights.max()
            if weight_max - weight_min > 20:
                issues.append(f"体重变化过大: {weight_min:.1f} - {weight_max:.1f} kg (相差{weight_max-weight_min:.1f}kg)")

    # 检查日期重复（多行同日期）
    date_counts = df['日期_parsed'].value_counts()
    multi_date_count = (date_counts > 1).sum()
    if multi_date_count > 0:
        print(f"  ✓ 有 {multi_date_count} 天存在多行数据（将自动合并）")

    if issues:
        for issue in issues[:5]:  # 只显示前5个
            print(f"  ⚠️  {issue}")
    else:
        print(f"  ✓ 未发现明显问题")

    # 建议
    print(f"\n💡 导入建议")

    if unique_dates < 30:
        print(f"  ⚠️  数据天数较少（{unique_dates}天），建议至少有30天以上数据")
    elif unique_dates < 60:
        print(f"  ✓ 数据天数适中（{unique_dates}天），可以进行基本趋势分析")
    else:
        print(f"  ✓ 数据天数充足（{unique_dates}天），可以进行深度分析")

    # 检查HRV覆盖率
    if 'HRV' in df.columns:
        hrv_coverage = df['HRV'].notna().sum() / unique_dates * 100
        if hrv_coverage < 30:
            print(f"  ⚠️  HRV数据覆盖率较低（{hrv_coverage:.1f}%），部分分析可能不准确")
        else:
            print(f"  ✓ HRV数据覆盖率良好（{hrv_coverage:.1f}%）")

    # 检查睡眠数据
    if '睡眠(h:m)' in df.columns:
        sleep_coverage = df['睡眠(h:m)'].notna().sum() / unique_dates * 100
        if sleep_coverage < 30:
            print(f"  ⚠️  睡眠数据覆盖率较低（{sleep_coverage:.1f}%）")
        else:
            print(f"  ✓ 睡眠数据覆盖率良好（{sleep_coverage:.1f}%）")

    print(f"\n{'='*70}")
    print(f"分析完成！如无明显问题，可以执行导入。")
    print(f"{'='*70}\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='深度分析CSV健康数据')
    parser.add_argument('csv_file', help='CSV文件路径')

    args = parser.parse_args()

    analyze_csv(args.csv_file)


if __name__ == '__main__':
    main()

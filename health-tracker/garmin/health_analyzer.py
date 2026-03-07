"""
健康分析器

使用 Claude AI 分析健康数据趋势
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from storage import HealthDatabase
from extractors import HealthDataExtractor


class HealthAnalyzer:
    """健康数据分析器"""

    def __init__(self, db: HealthDatabase, ai_extractor: HealthDataExtractor):
        """
        初始化分析器

        Args:
            db: 健康数据库
            ai_extractor: AI 数据提取器（用于生成分析）
        """
        self.db = db
        self.ai = ai_extractor

    def get_recent_data(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取最近 N 天的健康数据

        Args:
            days: 天数

        Returns:
            健康记录列表
        """
        records = self.db.get_recent_records(days)
        return records

    @staticmethod
    def _safe_avg(values: List[Optional[float]]) -> Optional[float]:
        valid = [v for v in values if v is not None]
        if not valid:
            return None
        return sum(valid) / len(valid)

    @staticmethod
    def _fmt_delta(delta: float, unit: str, digits: int = 1) -> str:
        return f"{delta:+.{digits}f}{unit}"

    def _sum_exercise_minutes(self, record: Dict[str, Any]) -> int:
        exercises = record.get('exercises') or []
        total = 0
        for ex in exercises:
            duration = ex.get('duration')
            if duration is not None:
                total += int(duration)
        return total

    def generate_brief_summary(
        self,
        days: int = 7,
        reference_date: Optional[datetime] = None,
        current_record: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成“当天 + 过去7天基线对比”的简要健康分析（用于日记末尾）

        Args:
            days: 分析天数
            reference_date: 参考日期（通常为当前日记日期）
            current_record: 当天最新记录（未写入 DB 时用于即时分析）

        Returns:
            简要分析文本
        """
        today = (reference_date.date() if reference_date else datetime.now().date())
        target_date = today.isoformat()

        # 当天记录优先使用调用方传入的最新数据，确保中午同步时分析的是“今天”。
        target_record = None
        if current_record and current_record.get('date') == target_date:
            target_record = current_record
        else:
            target_record = self.db.get_record_by_date(target_date)

        if not target_record:
            if current_record:
                target_record = current_record
                target_date = current_record.get('date', target_date)
            else:
                return f"### 近{days}天健康分析\n\n暂无 {target_date} 的可用数据。"

        baseline_end = today - timedelta(days=1)
        baseline_start = baseline_end - timedelta(days=days - 1)
        compare_pool = []
        if baseline_end >= baseline_start:
            compare_pool = self.db.get_records_by_range(
                baseline_start.isoformat(),
                baseline_end.isoformat()
            )

        target_sleep = target_record.get('sleep_duration')
        target_deep = target_record.get('deep_sleep_duration')
        target_rem = target_record.get('rem_sleep_duration')
        target_hrv = target_record.get('hrv')
        target_rhr = target_record.get('resting_heart_rate')
        target_ex_minutes = self._sum_exercise_minutes(target_record)
        target_exercises = target_record.get('exercises') or []

        avg_sleep = self._safe_avg([r.get('sleep_duration') for r in compare_pool])
        avg_hrv = self._safe_avg([r.get('hrv') for r in compare_pool])
        avg_rhr = self._safe_avg([r.get('resting_heart_rate') for r in compare_pool])
        avg_ex_minutes = self._safe_avg([self._sum_exercise_minutes(r) for r in compare_pool])

        compares = []
        improved = []
        declined = []
        cautions = []

        if target_sleep is not None and avg_sleep is not None:
            sleep_diff = target_sleep - avg_sleep
            compares.append(f"- 睡眠时长：{target_sleep:.2f}h（过去{days}天基线 {avg_sleep:.2f}h，{self._fmt_delta(sleep_diff, 'h', 2)}）")
            if sleep_diff >= 0.30:
                improved.append(f"睡眠时长高于过去{days}天基线 {sleep_diff:.2f}h。")
            elif sleep_diff <= -0.30:
                declined.append(f"睡眠时长低于过去{days}天基线 {abs(sleep_diff):.2f}h。")

        if target_hrv is not None and avg_hrv is not None:
            hrv_diff = target_hrv - avg_hrv
            compares.append(f"- HRV：{target_hrv:.0f}（过去{days}天基线 {avg_hrv:.1f}，{self._fmt_delta(hrv_diff, '', 1)}）")
            if hrv_diff >= 2:
                improved.append(f"HRV 高于基线 {hrv_diff:.1f}，恢复状态偏好。")
            elif hrv_diff <= -2:
                declined.append(f"HRV 低于基线 {abs(hrv_diff):.1f}，恢复压力偏高。")

        if target_rhr is not None and avg_rhr is not None:
            rhr_diff = target_rhr - avg_rhr
            compares.append(f"- 静息心率：{target_rhr:.0f}bpm（过去{days}天基线 {avg_rhr:.1f}bpm，{self._fmt_delta(rhr_diff, 'bpm', 1)}）")
            if rhr_diff <= -1:
                improved.append(f"静息心率低于基线 {abs(rhr_diff):.1f}bpm，恢复较好。")
            elif rhr_diff >= 1:
                declined.append(f"静息心率高于基线 {rhr_diff:.1f}bpm，需关注疲劳累积。")

        if avg_ex_minutes is not None:
            ex_diff = target_ex_minutes - avg_ex_minutes
            compares.append(f"- 运动时长：{target_ex_minutes} 分钟（过去{days}天基线 {avg_ex_minutes:.1f} 分钟，{self._fmt_delta(ex_diff, ' 分钟', 1)}）")
            if ex_diff >= 20:
                improved.append(f"今日运动负荷高于过去{days}天常态。")
            elif ex_diff <= -20:
                declined.append(f"今日运动明显少于过去{days}天常态。")

        if target_sleep is not None and target_sleep < 7:
            cautions.append("昨夜总睡眠低于 7 小时，优先补足睡眠。")
        if target_sleep and target_deep and target_sleep > 0:
            deep_ratio = target_deep / target_sleep
            if deep_ratio < 0.18:
                cautions.append("深睡占比偏低，晚间减少刺激并提前放松。")
        if target_hrv is not None and avg_hrv is not None and target_hrv < avg_hrv - 3:
            cautions.append("HRV 显著低于基线，建议降低训练强度。")
        if target_rhr is not None and avg_rhr is not None and target_rhr > avg_rhr + 2:
            cautions.append("静息心率高于基线较多，注意恢复和补水。")
        if target_ex_minutes == 0:
            cautions.append("今日暂无运动记录，可安排低强度活动保持节律。")

        exercise_line = "- 今日运动：无记录"
        if target_exercises:
            types = []
            for ex in target_exercises:
                ex_type = ex.get('type')
                if ex_type:
                    types.append(ex_type)
            unique_types = "、".join(sorted(set(types))) if types else "有运动记录"
            exercise_line = (
                f"- 今日运动：{len(target_exercises)} 次，累计 {target_ex_minutes} 分钟（{unique_types}）"
            )

        improved_text = "\n".join(f"- {x}" for x in improved) if improved else "- 暂无显著提升项。"
        declined_text = "\n".join(f"- {x}" for x in declined) if declined else "- 暂无显著下降项。"
        caution_text = "\n".join(f"- {x}" for x in cautions) if cautions else "- 状态整体平稳，保持当前节奏。"
        compare_text = "\n".join(compares) if compares else "- 近7天对比数据不足。"

        summary = f"""### 近{days}天健康分析（重点回顾 {target_date}）

**今日回顾（截至当前同步时刻）**
- 昨夜睡眠（记入 {target_date}）：{target_sleep:.2f}h（深睡 {target_deep:.2f}h，REM {target_rem:.2f}h）""" if (
            target_sleep is not None and target_deep is not None and target_rem is not None
        ) else f"""### 近{days}天健康分析（重点回顾 {target_date}）

**今日回顾（截至当前同步时刻）**
- 昨夜睡眠（记入 {target_date}）：数据不完整"""

        summary += f"""
{exercise_line}

**与过去{days}天基线对比（{baseline_start.isoformat()} ~ {baseline_end.isoformat()}）**
{compare_text}

**提升项**
{improved_text}

**下降项**
{declined_text}

**后续注意**
{caution_text}

详细分析：[[Health/分析/{today.strftime('%Y-%m')} 健康分析]]"""

        return summary

    def generate_detailed_analysis(self, days: int = 30) -> str:
        """
        生成详细健康分析（用于单独笔记）

        Args:
            days: 分析天数

        Returns:
            详细分析文本
        """
        records = self.get_recent_data(days)

        if not records or len(records) == 0:
            return "## 📊 数据不足\n\n暂无足够数据进行分析。"

        # 构建分析提示词
        data_summary = self._summarize_records(records)

        prompt = f"""请分析以下 {days} 天的健康数据，生成详细的健康分析报告。

{data_summary}

请按以下结构生成分析报告（使用 Markdown 格式）：

## 📈 {days}天趋势分析

### 睡眠质量
分析睡眠时长、深度睡眠、REM 睡眠的趋势，指出异常变化。

### HRV 分析
分析心率变异性的变化趋势和稳定性。

### 心率监测
分析静息心率和平均心率的变化。

### 运动情况
总结运动频率、类型和强度。

## 💡 健康建议

基于数据给出 3-5 条具体的健康建议。

## ⚠️ 需要关注

指出需要特别注意的健康指标或异常趋势。
"""

        try:
            # 使用 AI 生成分析
            analysis = self.ai._call_claude(prompt)
            return analysis
        except Exception as e:
            print(f"✗ 生成AI分析失败: {e}")
            # 返回基础统计分析
            return self._generate_basic_analysis(records, days)

    def _summarize_records(self, records: List[Dict[str, Any]]) -> str:
        """将健康记录转换为文本摘要"""
        lines = ["健康数据摘要：\n"]

        for record in records:
            date = record.get('date', '未知')
            sleep = record.get('sleep_duration')
            deep_sleep = record.get('deep_sleep_duration')
            hrv = record.get('hrv')
            hr = record.get('resting_heart_rate')

            line = f"- {date}: "
            parts = []
            if sleep:
                parts.append(f"睡眠{sleep:.1f}h")
            if deep_sleep:
                parts.append(f"深睡{deep_sleep:.1f}h")
            if hrv:
                parts.append(f"HRV{hrv}")
            if hr:
                parts.append(f"心率{hr}bpm")

            line += ", ".join(parts)
            lines.append(line)

        return "\n".join(lines)

    def _generate_basic_analysis(self, records: List[Dict[str, Any]], days: int) -> str:
        """生成基础统计分析（不使用AI）"""
        sleep_durations = [r.get('sleep_duration') for r in records if r.get('sleep_duration')]
        deep_sleeps = [r.get('deep_sleep_duration') for r in records if r.get('deep_sleep_duration')]
        hrvs = [r.get('hrv') for r in records if r.get('hrv')]
        hrs = [r.get('resting_heart_rate') for r in records if r.get('resting_heart_rate')]

        analysis = f"## 📈 {days}天趋势分析\n\n"

        # 睡眠分析
        if sleep_durations:
            avg_sleep = sum(sleep_durations) / len(sleep_durations)
            analysis += f"### 睡眠质量\n"
            analysis += f"- 平均睡眠时长：{avg_sleep:.1f} 小时\n"
            if deep_sleeps:
                avg_deep = sum(deep_sleeps) / len(deep_sleeps)
                deep_pct = (avg_deep / avg_sleep * 100) if avg_sleep > 0 else 0
                analysis += f"- 平均深度睡眠：{avg_deep:.1f} 小时（占比 {deep_pct:.1f}%）\n"
            analysis += "\n"

        # HRV 分析
        if hrvs:
            avg_hrv = sum(hrvs) / len(hrvs)
            analysis += f"### HRV 分析\n"
            analysis += f"- 平均 HRV：{avg_hrv:.0f} ms\n"
            analysis += f"- 变化范围：{min(hrvs)}-{max(hrvs)} ms\n\n"

        # 心率分析
        if hrs:
            avg_hr = sum(hrs) / len(hrs)
            analysis += f"### 心率监测\n"
            analysis += f"- 平均静息心率：{avg_hr:.0f} bpm\n\n"

        analysis += "## 💡 健康建议\n\n"
        analysis += "1. 保持规律的作息时间\n"
        analysis += "2. 确保足够的深度睡眠\n"
        analysis += "3. 注意 HRV 变化趋势\n"

        return analysis

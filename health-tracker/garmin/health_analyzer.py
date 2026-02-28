"""
健康分析器

使用 Claude AI 分析健康数据趋势
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
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

    def generate_brief_summary(self, days: int = 7) -> str:
        """
        生成简要健康分析（用于日记末尾）

        Args:
            days: 分析天数

        Returns:
            简要分析文本
        """
        records = self.get_recent_data(days)

        if not records or len(records) == 0:
            return f"### 近{days}天概况\n\n暂无数据"

        # 计算统计数据
        sleep_durations = [r.get('sleep_duration') for r in records if r.get('sleep_duration')]
        hrvs = [r.get('hrv') for r in records if r.get('hrv')]
        resting_hrs = [r.get('resting_heart_rate') for r in records if r.get('resting_heart_rate')]

        stats = []

        # 睡眠统计
        if sleep_durations:
            avg_sleep = sum(sleep_durations) / len(sleep_durations)
            stats.append(f"- 睡眠质量：平均{avg_sleep:.1f}小时")

        # HRV 统计
        if hrvs:
            avg_hrv = sum(hrvs) / len(hrvs)
            hrv_range = f"{min(hrvs)}-{max(hrvs)}ms"
            stats.append(f"- HRV趋势：平均{avg_hrv:.0f}ms（范围 {hrv_range}）")

        # 心率统计
        if resting_hrs:
            avg_hr = sum(resting_hrs) / len(resting_hrs)
            stats.append(f"- 心率状态：静息{avg_hr:.0f} bpm")

        summary = f"""### 近{days}天概况
{chr(10).join(stats)}

详细分析：[[Health/分析/{datetime.now().strftime('%Y-%m')} 健康分析]]"""

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

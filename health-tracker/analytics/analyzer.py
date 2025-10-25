"""
健康数据分析器

整合Claude AI进行深度数据分析和个性化建议生成
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json


class HealthAnalyzer:
    """健康数据分析器"""

    def __init__(self, extractor, database):
        """
        初始化分析器

        Args:
            extractor: HealthDataExtractor实例
            database: HealthDatabase实例
        """
        self.extractor = extractor
        self.db = database

    def generate_daily_summary(self, date: str) -> Optional[str]:
        """
        生成每日健康总结

        Args:
            date: 日期 (YYYY-MM-DD)

        Returns:
            总结文本
        """
        record = self.db.get_record_by_date(date)
        if not record:
            return f"未找到{date}的健康记录"

        # 让Claude生成总结
        prompt = self._build_daily_summary_prompt(record)
        analysis = self.extractor.analyze_trends([record], prompt)

        # 保存分析结果
        self.db.save_insight(
            analysis=analysis,
            start_date=date,
            end_date=date,
            insight_type="daily_summary"
        )

        return analysis

    def generate_weekly_report(self, end_date: Optional[str] = None) -> str:
        """
        生成周报

        Args:
            end_date: 结束日期，默认为今天

        Returns:
            周报文本
        """
        if not end_date:
            end_date = datetime.now().date().isoformat()

        # 获取最近7天的数据
        records = self.db.get_recent_records(days=7)

        if not records:
            return "最近7天没有健康记录"

        # 计算统计数据
        stats = self.db.get_statistics(days=7)

        # 让Claude生成周报
        prompt = self._build_weekly_report_prompt(stats)
        analysis = self.extractor.analyze_trends(records, prompt)

        # 保存分析结果
        start_date = (datetime.fromisoformat(end_date) - timedelta(days=6)).isoformat()
        self.db.save_insight(
            analysis=analysis,
            start_date=start_date,
            end_date=end_date,
            insight_type="weekly_report"
        )

        return analysis

    def generate_monthly_report(self, year: int, month: int) -> str:
        """
        生成月报

        Args:
            year: 年份
            month: 月份

        Returns:
            月报文本
        """
        # 计算日期范围
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)

        # 获取数据
        records = self.db.get_records_by_range(
            start_date.isoformat(),
            end_date.isoformat()
        )

        if not records:
            return f"{year}年{month}月没有健康记录"

        # 计算统计数据
        days_in_month = (end_date - start_date).days + 1
        stats = self.db.get_statistics(days=days_in_month)

        # 让Claude生成月报
        prompt = self._build_monthly_report_prompt(year, month, stats)
        analysis = self.extractor.analyze_trends(records, prompt)

        # 保存分析结果
        self.db.save_insight(
            analysis=analysis,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            insight_type="monthly_report"
        )

        return analysis

    def answer_question(self, question: str, days: int = 30) -> str:
        """
        回答用户关于健康数据的问题

        Args:
            question: 用户问题
            days: 查询最近多少天的数据

        Returns:
            Claude的回答
        """
        # 获取相关数据
        records = self.db.get_recent_records(days=days)

        if not records:
            return f"最近{days}天没有健康记录，无法回答问题"

        # 让Claude回答问题
        analysis = self.extractor.analyze_trends(records, question)

        # 保存问答记录
        end_date = datetime.now().date().isoformat()
        start_date = (datetime.now().date() - timedelta(days=days-1)).isoformat()

        self.db.save_insight(
            analysis=analysis,
            start_date=start_date,
            end_date=end_date,
            insight_type="question_answer",
            question=question
        )

        return analysis

    def identify_correlations(self, days: int = 30) -> str:
        """
        识别健康指标之间的相关性

        Args:
            days: 分析天数

        Returns:
            相关性分析结果
        """
        records = self.db.get_recent_records(days=days)

        if not records:
            return f"最近{days}天没有足够的数据进行相关性分析"

        prompt = """请深度分析以下健康数据，找出各指标之间的相关性：

1. **体重与运动的关系**：运动量增加时体重是否有变化？
2. **睡眠与精力的关系**：睡眠质量如何影响第二天的精力水平？
3. **运动与睡眠的关系**：运动是否改善了睡眠质量？
4. **体重与饮食的关系**：饮食模式如何影响体重变化？
5. **情绪与其他指标的关系**：情绪好坏与哪些健康指标相关？

请给出具体的数据支持和建议。
"""

        analysis = self.extractor.analyze_trends(records, prompt)

        # 保存分析结果
        end_date = datetime.now().date().isoformat()
        start_date = (datetime.now().date() - timedelta(days=days-1)).isoformat()

        self.db.save_insight(
            analysis=analysis,
            start_date=start_date,
            end_date=end_date,
            insight_type="correlation_analysis"
        )

        return analysis

    def detect_anomalies(self, days: int = 30) -> str:
        """
        检测异常数据和健康风险

        Args:
            days: 分析天数

        Returns:
            异常检测结果
        """
        records = self.db.get_recent_records(days=days)

        if not records:
            return f"最近{days}天没有数据"

        prompt = """请作为健康顾问，检查以下数据中的异常情况：

1. **体重异常**：是否有急剧增加或减少？
2. **睡眠问题**：是否有持续的睡眠不足或质量下降？
3. **运动缺失**：是否长时间没有运动？
4. **情绪波动**：是否有明显的情绪低落或波动？
5. **其他健康风险**：是否有需要关注的健康指标？

请指出具体的异常数据，分析可能的原因，并提供建议。
"""

        analysis = self.extractor.analyze_trends(records, prompt)

        # 保存分析结果
        end_date = datetime.now().date().isoformat()
        start_date = (datetime.now().date() - timedelta(days=days-1)).isoformat()

        self.db.save_insight(
            analysis=analysis,
            start_date=start_date,
            end_date=end_date,
            insight_type="anomaly_detection"
        )

        return analysis

    def generate_recommendations(self, goal: Optional[str] = None) -> str:
        """
        生成个性化健康建议

        Args:
            goal: 用户的健康目标（如"减重5kg"）

        Returns:
            建议文本
        """
        # 获取最近数据
        records = self.db.get_recent_records(days=30)
        stats = self.db.get_statistics(days=30)

        if not records:
            return "需要更多数据才能生成个性化建议"

        # 构建提示
        goal_text = f"\n用户目标: {goal}\n" if goal else ""

        prompt = f"""作为专业健康顾问，基于用户的历史数据，生成个性化的健康改进建议。
{goal_text}
统计数据:
{json.dumps(stats, ensure_ascii=False, indent=2)}

请提供:
1. **运动建议**: 运动类型、频率、强度
2. **饮食建议**: 饮食结构、卡路里控制
3. **睡眠优化**: 改善睡眠质量的方法
4. **生活方式**: 其他有助于健康的建议
5. **行动计划**: 具体的、可执行的每周计划

建议应该:
- 基于实际数据
- 具体可行
- 循序渐进
- 考虑用户的实际情况和习惯
"""

        analysis = self.extractor.analyze_trends(records, prompt)

        # 保存建议
        self.db.save_insight(
            analysis=analysis,
            start_date=(datetime.now().date() - timedelta(days=29)).isoformat(),
            end_date=datetime.now().date().isoformat(),
            insight_type="recommendations",
            question=goal
        )

        return analysis

    def _build_daily_summary_prompt(self, record: Dict[str, Any]) -> str:
        """构建每日总结的提示"""
        return f"""请为{record['date']}的健康数据生成一个简洁的每日总结：

数据:
- 体重: {record.get('weight', '无')}kg
- 睡眠: {record.get('sleep_duration', '无')}小时
- 运动: {len(record.get('exercises', []))}项
- 整体感受: {record.get('overall_feeling', '无')}

请用1-2段话总结这一天的健康状况，包括：
1. 主要数据点
2. 表现好的方面
3. 需要改进的地方
4. 简短建议

语气要友好鼓励。
"""

    def _build_weekly_report_prompt(self, stats: Dict[str, Any]) -> str:
        """构建周报的提示"""
        return f"""请生成一份详细的健康周报：

统计数据:
{json.dumps(stats, ensure_ascii=False, indent=2)}

周报应包括:
1. **总体表现**: 这周健康管理做得如何
2. **关键指标分析**: 体重、睡眠、运动的变化趋势
3. **亮点**: 做得特别好的地方
4. **需要改进**: 需要关注的问题
5. **下周目标**: 具体可行的改进建议

语气要专业但友好，多用数据支持观点。
"""

    def _build_monthly_report_prompt(
        self,
        year: int,
        month: int,
        stats: Dict[str, Any]
    ) -> str:
        """构建月报的提示"""
        return f"""请生成{year}年{month}月的健康月报：

统计数据:
{json.dumps(stats, ensure_ascii=False, indent=2)}

月报应包括:
1. **月度总结**: 整体健康管理情况
2. **数据趋势**: 各项指标的变化趋势分析
3. **成就**: 本月达成的健康目标
4. **挑战**: 遇到的困难和问题
5. **月度洞察**: 发现的健康规律和相关性
6. **下月计划**: 具体的改进计划和目标

要求:
- 深度分析，不只是简单总结
- 用数据说话
- 提供可执行的建议
- 语气专业且激励人心
"""

    def compare_periods(
        self,
        period1_days: int = 7,
        period2_days: int = 7
    ) -> str:
        """
        比较两个时间段的健康数据

        Args:
            period1_days: 第一个时间段的天数（最近）
            period2_days: 第二个时间段的天数（更早）

        Returns:
            比较分析结果
        """
        # 获取两个时间段的数据
        all_records = self.db.get_recent_records(days=period1_days + period2_days)

        if len(all_records) < period1_days + period2_days:
            return "数据不足，无法进行时间段比较"

        recent_records = all_records[:period1_days]
        earlier_records = all_records[period1_days:period1_days + period2_days]

        prompt = f"""请比较以下两个时间段的健康数据：

**最近{period1_days}天** vs **之前{period2_days}天**

最近时段数据:
{self.extractor._format_data_for_analysis(recent_records)}

之前时段数据:
{self.extractor._format_data_for_analysis(earlier_records)}

请分析:
1. 各项指标的变化（改善/恶化）
2. 可能的原因
3. 趋势的持续性
4. 建议（保持/改进）

提供数据支持的具体结论。
"""

        return self.extractor.analyze_trends(all_records, prompt)

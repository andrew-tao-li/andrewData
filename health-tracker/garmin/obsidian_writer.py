"""
Obsidian 写入器

自动创建和更新 Obsidian 日记，写入健康日志和分析
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class ObsidianWriter:
    """Obsidian 日记写入器"""

    def __init__(self, vault_path: str,
                 health_log_start: str = "（健康日志）",
                 health_log_end: str = "（健康日志结束）"):
        """
        初始化 Obsidian 写入器

        Args:
            vault_path: Obsidian vault 根目录
            health_log_start: 健康日志开始标记
            health_log_end: 健康日志结束标记
        """
        self.vault_path = Path(vault_path)
        self.health_log_start = health_log_start
        self.health_log_end = health_log_end

        if not self.vault_path.exists():
            raise ValueError(f"Vault 路径不存在: {vault_path}")

    def get_daily_note_path(self, date: datetime) -> Path:
        """
        获取日记文件路径（可能包含星期）

        Args:
            date: 日期

        Returns:
            日记文件路径
        """
        date_str = date.strftime("%Y-%m-%d")

        # 可能的文件路径
        possible_paths = [
            self.vault_path / f"{date_str}.md",
            self.vault_path / "Daily" / f"{date_str}.md",
        ]

        # 也支持带星期的格式
        weekday_names = ["一", "二", "三", "四", "五", "六", "日"]
        weekday = weekday_names[date.weekday()]
        possible_paths.extend([
            self.vault_path / f"{date_str} 星期{weekday}.md",
            self.vault_path / f"{date_str} 梦境.md",  # 用户的自定义格式
        ])

        # 检查是否存在
        for path in possible_paths:
            if path.exists():
                return path

        # 默认创建简单格式
        return self.vault_path / f"{date_str}.md"

    def create_daily_note(self, date: datetime) -> Path:
        """
        创建新的日记文件

        Args:
            date: 日期

        Returns:
            创建的文件路径
        """
        note_path = self.get_daily_note_path(date)

        if not note_path.exists():
            # 创建空白日记（不添加日期标题，因为文件名已经是日期）
            content = ""

            note_path.parent.mkdir(parents=True, exist_ok=True)
            with open(note_path, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"✓ 创建新日记: {note_path.name}")

        return note_path

    def read_note(self, note_path: Path) -> str:
        """读取日记内容"""
        with open(note_path, 'r', encoding='utf-8') as f:
            return f.read()

    def write_note(self, note_path: Path, content: str):
        """写入日记内容"""
        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def format_health_log(self, data: Dict[str, Any]) -> str:
        """
        格式化健康日志内容

        Args:
            data: 健康数据字典

        Returns:
            格式化后的健康日志文本
        """
        now = datetime.now()
        log_time = now.strftime("%H:%M")

        # 提取数据（优先使用 Garmin 数据，否则保留占位符）
        sleep = data.get('sleep', {}) or {}
        hrv_data = data.get('hrv', {}) or {}
        heart_rate = data.get('heart_rate', {}) or {}
        activities = data.get('activities', []) or []

        # 格式化睡眠时长
        def format_duration(hours):
            if hours is None:
                return "_（待填写）_"
            h = int(hours)
            m = int((hours - h) * 60)
            return f"{h}时 {m}分 ✓" if hours else "_（待填写）_"

        # 格式化运动记录
        exercise_lines = []
        if activities:
            for act in activities:
                act_type = act.get('activity_name') or act.get('type', '运动')
                duration = act.get('duration', 0)
                distance = act.get('distance', 0)
                avg_hr = act.get('avg_hr')

                line_parts = [f"- {act_type}"]
                if distance > 0:
                    line_parts.append(f"{distance}km")
                if duration > 0:
                    line_parts.append(f"{int(duration)}分钟")
                if avg_hr:
                    line_parts.append(f"(平均心率 {avg_hr}bpm)")

                exercise_lines.append(" ".join(line_parts))
        else:
            exercise_lines.append("- 今日无运动记录")

        exercise_text = "\n".join(exercise_lines)

        # 生成日志内容
        log = f"""{self.health_log_start}
日期：{data.get('date', now.strftime('%Y-%m-%d'))} 时间：{log_time}
**晚餐与睡前**：
体重_kg：{data.get('weight') or '_（待填写）_'}
肌肉_kg：{data.get('muscle_mass') or '_（待填写）_'}
基础代谢：{data.get('basal_metabolism') or '_（待填写）_'}
内脏脂肪等级：{data.get('visceral_fat_level') or '_（待填写）_'}
睡眠时长：{format_duration(sleep.get('sleep_duration'))}
深度睡眠：{format_duration(sleep.get('deep_sleep_duration'))}
REM睡眠：{format_duration(sleep.get('rem_sleep_duration'))}
静息心率_bpm：{heart_rate.get('resting_heart_rate') or '_（待填写）_'}{' ✓' if heart_rate.get('resting_heart_rate') else ''}
夜间平均心率_bpm：{heart_rate.get('avg_heart_rate') or '_（待填写）_'}{' ✓' if heart_rate.get('avg_heart_rate') else ''}
HRV_ms：{hrv_data.get('weekly_avg') or '_（待填写）_'}{' ✓' if hrv_data.get('weekly_avg') else ''}
夜间平均HRV_ms：{hrv_data.get('hrv') or '_（待填写）_'}{' ✓' if hrv_data.get('hrv') else ''}
夜间排尿次数：{data.get('urination_count') or '_（待填写）_'}
跟腱疼痛评分：{data.get('pain_score') or '_（待填写）_'}
晨僵时长_min：{data.get('morning_stiffness_duration') or '_（待填写）_'}
最疼部位：{data.get('pain_location') or '_（待填写）_'}
眼部不适：{data.get('symptoms') or '_（待填写）_'}

**运动记录**：
{exercise_text}
{self.health_log_end}"""

        return log

    def write_health_log(self, date: datetime, data: Dict[str, Any],
                        create_if_missing: bool = True) -> bool:
        """
        写入健康日志到 Obsidian 日记

        Args:
            date: 日期
            data: 健康数据
            create_if_missing: 如果日记不存在是否创建

        Returns:
            是否写入成功
        """
        try:
            # 获取或创建日记
            note_path = self.get_daily_note_path(date)

            if not note_path.exists():
                if create_if_missing:
                    note_path = self.create_daily_note(date)
                else:
                    print(f"✗ 日记不存在: {note_path.name}")
                    return False

            # 读取现有内容
            content = self.read_note(note_path)

            # 生成健康日志
            health_log = self.format_health_log(data)

            # 检查是否已有健康日志
            if self.health_log_start in content:
                # 替换现有日志
                pattern = re.escape(self.health_log_start) + r'.*?' + re.escape(self.health_log_end)
                new_content = re.sub(pattern, health_log, content, flags=re.DOTALL)
                print(f"✓ 更新现有健康日志")
            else:
                # 添加新日志（在文件末尾前）
                new_content = content.rstrip() + "\n\n" + health_log + "\n"
                print(f"✓ 添加新健康日志")

            # 写入文件
            self.write_note(note_path, new_content)
            print(f"✓ 健康日志已写入: {note_path.name}")

            return True

        except Exception as e:
            print(f"✗ 写入健康日志失败: {e}")
            return False

    def append_analysis(self, date: datetime, analysis: str,
                       title: str = "## 📊 健康趋势分析") -> bool:
        """
        在日记末尾添加健康分析

        Args:
            date: 日期
            analysis: 分析内容
            title: 分析标题

        Returns:
            是否添加成功
        """
        try:
            note_path = self.get_daily_note_path(date)

            if not note_path.exists():
                print(f"✗ 日记不存在: {note_path.name}")
                return False

            content = self.read_note(note_path)

            # 检查是否已有分析部分
            if title in content:
                # 替换现有分析
                pattern = re.escape(title) + r'.*?(?=\n##|\Z)'
                new_content = re.sub(pattern, title + "\n\n" + analysis, content, flags=re.DOTALL)
                print(f"✓ 更新现有分析")
            else:
                # 添加新分析
                new_content = content.rstrip() + "\n\n---\n\n" + title + "\n\n" + analysis + "\n"
                print(f"✓ 添加新分析")

            self.write_note(note_path, new_content)
            return True

        except Exception as e:
            print(f"✗ 添加分析失败: {e}")
            return False

    def create_analysis_note(self, period: str, analysis: str,
                           analysis_folder: str = "Health/分析") -> bool:
        """
        创建单独的健康分析笔记

        Args:
            period: 分析周期（如 "2026-02"）
            analysis: 分析内容
            analysis_folder: 分析笔记存放文件夹

        Returns:
            是否创建成功
        """
        try:
            analysis_dir = self.vault_path / analysis_folder
            analysis_dir.mkdir(parents=True, exist_ok=True)

            note_path = analysis_dir / f"{period} 健康分析.md"

            # 生成分析笔记内容
            now = datetime.now()
            content = f"""# {period} 健康分析报告

生成时间：{now.strftime('%Y-%m-%d %H:%M')}

{analysis}

---

*本报告由 Health Tracker AI 自动生成*
"""

            with open(note_path, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"✓ 创建分析笔记: {note_path.name}")
            return True

        except Exception as e:
            print(f"✗ 创建分析笔记失败: {e}")
            return False

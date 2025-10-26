"""
Obsidian笔记解析器

读取Obsidian vault中的健康日志，提取文本和图片
"""

import os
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import frontmatter


class ObsidianParser:
    """Obsidian笔记解析器"""

    def __init__(self, vault_path: str, health_folder: str = "Health",
                 health_section_start: str = None, health_section_end: str = None):
        """
        初始化解析器

        Args:
            vault_path: Obsidian vault的根目录
            health_folder: 健康日志所在的文件夹名称（如果为空或"."则使用根目录）
            health_section_start: 健康内容的开始标记（如"（健康日志）"）
            health_section_end: 健康内容的结束标记（如"（健康日志结束）"）
        """
        self.vault_path = Path(vault_path)
        self.health_folder = health_folder if health_folder and health_folder != "." else ""
        self.health_path = self.vault_path / self.health_folder if self.health_folder else self.vault_path
        self.health_section_start = health_section_start
        self.health_section_end = health_section_end

        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {vault_path}")

    def get_note_path(self, date: datetime) -> Optional[Path]:
        """
        获取指定日期的笔记路径

        支持多种命名格式:
        - YYYY-MM-DD.md
        - YYYY-MM-DD 星期X.md
        - Daily/YYYY-MM-DD.md

        Args:
            date: 日期

        Returns:
            笔记文件路径，如果不存在返回None
        """
        date_str = date.strftime("%Y-%m-%d")

        # 可能的文件路径
        possible_paths = [
            self.health_path / f"{date_str}.md",
            self.health_path / "Daily" / f"{date_str}.md",
            self.vault_path / f"{date_str}.md",
        ]

        # 也支持带星期的格式
        weekday_names = ["一", "二", "三", "四", "五", "六", "日"]
        weekday = weekday_names[date.weekday()]
        possible_paths.extend([
            self.health_path / f"{date_str} 星期{weekday}.md",
            self.vault_path / f"{date_str} 星期{weekday}.md",
        ])

        for path in possible_paths:
            if path.exists():
                return path

        # 如果都不存在，尝试在health文件夹中搜索
        if self.health_path.exists():
            for file in self.health_path.rglob(f"*{date_str}*.md"):
                return file

        return None

    def parse_note(self, date: datetime) -> Optional[Dict[str, Any]]:
        """
        解析指定日期的笔记

        Args:
            date: 日期

        Returns:
            包含笔记内容和元数据的字典，如果笔记不存在返回None
        """
        note_path = self.get_note_path(date)
        if not note_path:
            return None

        return self.parse_file(note_path)

    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        解析单个笔记文件

        Args:
            file_path: 笔记文件路径

        Returns:
            包含笔记内容和元数据的字典
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)

        # 提取健康内容（如果设置了标记）
        content = self._extract_health_section(post.content) if self.health_section_start else post.content

        # 提取图片链接（只从健康内容中提取）
        images = self._extract_images(content, file_path.parent)

        # 提取可能的健康相关标签
        tags = self._extract_tags(content)
        if hasattr(post, 'metadata') and 'tags' in post.metadata:
            tags.extend(post.metadata['tags'])

        return {
            'file_path': str(file_path),
            'content': content,
            'original_content': post.content,  # 保留原始完整内容
            'metadata': dict(post.metadata) if hasattr(post, 'metadata') else {},
            'images': images,
            'tags': list(set(tags)),
            'date': self._extract_date_from_filename(file_path)
        }

    def _extract_health_section(self, content: str) -> str:
        """
        从内容中提取健康日志部分

        Args:
            content: 笔记完整内容

        Returns:
            提取的健康日志内容，如果没有找到标记则返回原内容
        """
        if not self.health_section_start:
            return content

        # 查找开始标记
        start_idx = content.find(self.health_section_start)
        if start_idx == -1:
            # 如果没有找到开始标记，返回原内容
            return content

        # 跳过开始标记本身
        start_idx += len(self.health_section_start)

        # 查找结束标记
        if self.health_section_end:
            end_idx = content.find(self.health_section_end, start_idx)
            if end_idx != -1:
                # 找到了结束标记，提取中间内容
                return content[start_idx:end_idx].strip()

        # 如果没有结束标记或没找到，返回从开始标记到文件末尾的内容
        return content[start_idx:].strip()

    def _extract_images(self, content: str, base_path: Path) -> List[Dict[str, str]]:
        """
        提取笔记中的图片

        支持的格式:
        - ![alt](image.png)
        - ![[image.png]]
        - ![](attachments/image.png)

        Args:
            content: 笔记内容
            base_path: 笔记所在目录

        Returns:
            图片信息列表，包含路径和类型
        """
        images = []

        # Markdown格式: ![alt](path)
        md_pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'
        for match in re.finditer(md_pattern, content):
            alt_text = match.group(1)
            image_path = match.group(2)
            full_path = self._resolve_image_path(image_path, base_path)
            if full_path:
                images.append({
                    'path': str(full_path),
                    'alt_text': alt_text,
                    'type': 'markdown'
                })

        # Obsidian格式: ![[path]]
        ob_pattern = r'!\[\[([^\]]+)\]\]'
        for match in re.finditer(ob_pattern, content):
            image_path = match.group(1)
            full_path = self._resolve_image_path(image_path, base_path)
            if full_path:
                images.append({
                    'path': str(full_path),
                    'alt_text': '',
                    'type': 'obsidian'
                })

        return images

    def _resolve_image_path(self, image_path: str, base_path: Path) -> Optional[Path]:
        """
        解析图片的完整路径

        Args:
            image_path: 相对路径
            base_path: 基础路径

        Returns:
            完整路径，如果文件不存在返回None
        """
        # 尝试多个可能的位置
        possible_paths = [
            base_path / image_path,  # 相对于笔记
            self.vault_path / image_path,  # 相对于vault根目录
            self.vault_path / "attachments" / image_path,  # 常见的附件文件夹
            self.vault_path / "assets" / image_path,
            self.vault_path / "images" / image_path,
        ]

        for path in possible_paths:
            if path.exists() and path.is_file():
                return path

        return None

    def _extract_tags(self, content: str) -> List[str]:
        """
        提取笔记中的标签

        支持: #tag 或 #tag/subtag

        Args:
            content: 笔记内容

        Returns:
            标签列表
        """
        pattern = r'#([\w\u4e00-\u9fff]+(?:/[\w\u4e00-\u9fff]+)*)'
        tags = re.findall(pattern, content)
        return tags

    def _extract_date_from_filename(self, file_path: Path) -> Optional[str]:
        """
        从文件名中提取日期

        Args:
            file_path: 文件路径

        Returns:
            日期字符串 (YYYY-MM-DD)，如果无法提取返回None
        """
        filename = file_path.stem
        # 匹配 YYYY-MM-DD 格式
        date_pattern = r'(\d{4}-\d{2}-\d{2})'
        match = re.search(date_pattern, filename)
        if match:
            return match.group(1)
        return None

    def get_recent_notes(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取最近N天的笔记

        Args:
            days: 天数

        Returns:
            笔记列表
        """
        notes = []
        today = datetime.now()

        for i in range(days):
            date = today - timedelta(days=i)
            note = self.parse_note(date)
            if note:
                notes.append(note)

        return notes

    def search_health_notes(self, keywords: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        搜索包含特定关键词的健康笔记

        Args:
            keywords: 关键词列表，如果为None则返回所有笔记

        Returns:
            符合条件的笔记列表
        """
        if not self.health_path.exists():
            return []

        notes = []
        for md_file in self.health_path.rglob("*.md"):
            try:
                note = self.parse_file(md_file)

                # 如果没有关键词，返回所有笔记
                if not keywords:
                    notes.append(note)
                    continue

                # 检查是否包含任何关键词
                content_lower = note['content'].lower()
                if any(keyword.lower() in content_lower for keyword in keywords):
                    notes.append(note)
            except Exception as e:
                print(f"Error parsing {md_file}: {e}")
                continue

        # 按日期排序
        notes.sort(key=lambda x: x.get('date', ''), reverse=True)
        return notes

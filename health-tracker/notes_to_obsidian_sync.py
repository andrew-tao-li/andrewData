#!/usr/bin/env python3
"""Sync iPhone Notes voice memo content into today's Obsidian daily note."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from difflib import SequenceMatcher
from datetime import datetime
from html import unescape
from pathlib import Path
from typing import Dict, Tuple

ROOT = Path(__file__).resolve().parent
DEFAULT_STATE_FILE = ROOT / "logs" / "notes-sync-state.json"
DEFAULT_CONFIG_FILE = ROOT / "config" / "notes_sync.json"
MAIN_CONFIG_FILE = ROOT / "config" / "config.json"
DEFAULT_ARCHIVE_DIR = ROOT / "logs" / "notes-sync-archive"


def load_json(path: Path) -> Dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def archive_memo_sync(
    archive_dir: Path,
    memo_text: str,
    source_title: str,
    note_path: Path,
    synced_at: datetime,
) -> Path:
    daily_dir = archive_dir / synced_at.strftime("%Y%m%d")
    archive_path = daily_dir / f"{synced_at.strftime('%H%M%S')}.json"
    payload = {
        "synced_at": synced_at.strftime("%Y-%m-%d %H:%M:%S"),
        "source_note_title": source_title,
        "obsidian_note_path": str(note_path),
        "memo_text": memo_text.strip(),
    }
    save_json(archive_path, payload)
    return archive_path


def escape_applescript(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def run_osascript(script: str) -> str:
    proc = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "osascript failed")
    return proc.stdout


def get_or_create_note_html(note_title: str) -> Tuple[str, str]:
    title = escape_applescript(note_title)
    script = f'''
    tell application "Notes"
        set noteTitle to "{title}"
        set targetNote to missing value
        try
            set targetNote to first note whose name is noteTitle
        end try
        if targetNote is missing value then
            set targetNote to make new note with properties {{name:noteTitle, body:"<div></div>"}}
        end if
        return (id of targetNote) & "<<<SEP>>>" & (body of targetNote)
    end tell
    '''
    output = run_osascript(script)
    if "<<<SEP>>>" not in output:
        raise RuntimeError("unexpected Notes output")
    note_id, body = output.split("<<<SEP>>>", 1)
    return note_id.strip(), body.strip()


def clear_note_body_by_id(note_id: str) -> None:
    note_id_escaped = escape_applescript(note_id)
    script = f'''
    tell application "Notes"
        set targetNoteID to "{note_id_escaped}"
        set targetNote to missing value
        try
            set targetNote to first note whose id is targetNoteID
        end try
        if targetNote is missing value then
            error "target note not found by id"
        end if
        set body of targetNote to "<div></div>"
    end tell
    '''
    run_osascript(script)


def html_to_text(body_html: str) -> str:
    text = body_html
    text = re.sub(r"<br\\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</div>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<div[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def get_daily_note_path(vault_path: Path, date_obj: datetime) -> Path:
    date_str = date_obj.strftime("%Y-%m-%d")
    weekday_names = ["一", "二", "三", "四", "五", "六", "日"]
    weekday = weekday_names[date_obj.weekday()]

    candidates = [
        vault_path / f"{date_str}.md",
        vault_path / "Daily" / f"{date_str}.md",
        vault_path / f"{date_str} 星期{weekday}.md",
        vault_path / f"{date_str} 梦境.md",
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


def append_memo_block(
    note_path: Path,
    memo_text: str,
    source_title: str,
    section_start: str,
    section_end: str,
) -> None:
    now = datetime.now()
    stamp = now.strftime("%Y-%m-%d %H:%M")
    chunk = f"[{stamp}]\n{memo_text.strip()}\n"
    analysis_title = "## 📊 健康趋势分析"

    if note_path.exists():
        content = note_path.read_text(encoding="utf-8")
    else:
        note_path.parent.mkdir(parents=True, exist_ok=True)
        content = ""

    start_idx = content.find(section_start)
    end_idx = content.find(section_end)

    if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
        insert_at = end_idx
        updated = content[:insert_at].rstrip() + "\n\n" + chunk + "\n" + content[insert_at:]
    else:
        block = (
            f"\n\n{section_start}\n"
            f"来源：iPhone 备忘录《{source_title}》\n\n"
            f"{chunk}\n"
            f"{section_end}\n"
        )
        analysis_idx = content.find(analysis_title)
        if analysis_idx != -1:
            updated = content[:analysis_idx].rstrip() + block + "\n\n" + content[analysis_idx:].lstrip()
        else:
            updated = content.rstrip() + block

    note_path.write_text(updated, encoding="utf-8")


def as_bool(value: object, default: bool = True) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("1", "true", "yes", "on"):
            return True
        if v in ("0", "false", "no", "off"):
            return False
    return default


def as_float(value: object, default: float) -> float:
    try:
        return float(value)
    except Exception:
        return default


def detect_truncate_reset(
    previous_text: str,
    current_text: str,
    min_shrink_ratio: float,
    max_similarity: float,
) -> bool:
    prev = previous_text.strip()
    cur = current_text.strip()
    prev_len = len(prev)
    cur_len = len(cur)
    if prev_len < 20:
        return False
    if cur_len == 0:
        return True
    if cur_len >= prev_len:
        return False

    shrink_ratio = (prev_len - cur_len) / prev_len
    if shrink_ratio < min_shrink_ratio:
        return False

    similarity = SequenceMatcher(a=prev, b=cur).ratio()
    return similarity <= max_similarity


def sync_once(config_path: Path, state_file: Path) -> int:
    notes_cfg = load_json(config_path)
    main_cfg = load_json(MAIN_CONFIG_FILE)

    if not notes_cfg.get("enabled", True):
        print("notes sync disabled")
        return 0

    source_title = notes_cfg.get("source_note_title", "晨间语音备忘").strip()
    if not source_title:
        raise RuntimeError("source_note_title is empty")

    vault = notes_cfg.get("obsidian_vault_path") or main_cfg.get("obsidian_vault_path")
    if not vault:
        raise RuntimeError("obsidian_vault_path is missing")

    section_start = notes_cfg.get("memo_section_start", "（今日备忘）")
    section_end = notes_cfg.get("memo_section_end", "（今日备忘结束）")
    truncate_reset_enabled = as_bool(notes_cfg.get("truncate_reset_enabled", True), True)
    truncate_reset_min_shrink_ratio = as_float(
        notes_cfg.get("truncate_reset_min_shrink_ratio", 0.35), 0.35
    )
    truncate_reset_max_similarity = as_float(
        notes_cfg.get("truncate_reset_max_similarity", 0.85), 0.85
    )
    clear_source_after_sync = as_bool(notes_cfg.get("clear_source_after_sync", False), False)

    note_id, body_html = get_or_create_note_html(source_title)
    source_text = html_to_text(body_html)
    source_lines = [line.rstrip() for line in source_text.splitlines()]
    # Notes 的 body 在部分系统版本会把标题作为首行返回；这里去掉，避免空内容误导入。
    if source_lines and source_lines[0].strip() == source_title:
        source_lines = source_lines[1:]
    source_text = "\n".join(source_lines).strip()

    state = load_json(state_file)
    last_note_id = state.get("note_id", "")
    last_source_text = state.get("last_source_text")
    delta = ""

    reset_detected = False

    if last_note_id != note_id:
        # Note changed: treat current text as fresh content.
        delta = source_text.strip()
    elif isinstance(last_source_text, str):
        if truncate_reset_enabled and detect_truncate_reset(
            last_source_text,
            source_text,
            truncate_reset_min_shrink_ratio,
            truncate_reset_max_similarity,
        ):
            # User likely cleared/rewrote the source note; treat current body as fresh content.
            reset_detected = True
            delta = source_text.strip()
        else:
            # Robust mode: detect inserted/replaced segments anywhere in note body.
            matcher = SequenceMatcher(a=last_source_text, b=source_text)
            pieces = []
            for tag, _i1, _i2, j1, j2 in matcher.get_opcodes():
                if tag in ("insert", "replace"):
                    seg = source_text[j1:j2].strip()
                    if seg:
                        pieces.append(seg)
            if pieces:
                deduped = []
                for seg in pieces:
                    if not deduped or deduped[-1] != seg:
                        deduped.append(seg)
                delta = "\n\n".join(deduped).strip()
    else:
        # Compatibility mode for old state files that only track last_len.
        last_len = int(state.get("last_len", 0) or 0)
        if 0 <= last_len <= len(source_text):
            delta = source_text[last_len:].strip()
        else:
            delta = source_text.strip()

    if not delta:
        new_state = {
            "note_id": note_id,
            "last_len": len(source_text),
            "last_source_text": source_text,
            "truncate_reset_detected": reset_detected,
            "clear_source_after_sync": clear_source_after_sync,
            "source_cleared_after_sync": False,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_note_title": source_title,
        }
        save_json(state_file, new_state)
        print("no new memo content")
        return 0

    synced_at = datetime.now()
    today_note = get_daily_note_path(Path(vault), synced_at)
    append_memo_block(today_note, delta, source_title, section_start, section_end)
    archive_path = archive_memo_sync(DEFAULT_ARCHIVE_DIR, delta, source_title, today_note, synced_at)
    print(f"memo archived -> {archive_path}")
    source_cleared = False
    if clear_source_after_sync:
        try:
            clear_note_body_by_id(note_id)
            source_cleared = True
            print(f"source note cleared -> {source_title}")
        except Exception as e:
            # Keep sync successful for data path; emit warning for privacy path.
            print(f"warning: source note clear failed: {e}")

    final_source_text = "" if source_cleared else source_text
    new_state = {
        "note_id": note_id,
        "last_len": len(final_source_text),
        "last_source_text": final_source_text,
        "truncate_reset_detected": reset_detected,
        "clear_source_after_sync": clear_source_after_sync,
        "source_cleared_after_sync": source_cleared,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_note_title": source_title,
    }
    save_json(state_file, new_state)
    print(f"memo synced -> {today_note}")
    return 0


def main() -> int:
    config_path = DEFAULT_CONFIG_FILE
    state_file = DEFAULT_STATE_FILE

    try:
        return sync_once(config_path, state_file)
    except Exception as e:
        print(f"notes sync failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/bin/bash
# Install launchd automation for iPhone Notes -> Obsidian sync

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_NAME="com.health-tracker.notes-sync.plist"
PLIST_SRC="$SCRIPT_DIR/$PLIST_NAME"
PLIST_DST="$HOME/Library/LaunchAgents/$PLIST_NAME"
LABEL="com.health-tracker.notes-sync"
UID_TARGET="gui/$(id -u)"

echo "========================================="
echo "Health Tracker - Notes Sync Installer"
echo "========================================="
echo ""

if [ ! -f "$PLIST_SRC" ]; then
    echo "ERROR: plist file not found: $PLIST_SRC"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/notes-sync-guard.sh" ]; then
    echo "ERROR: guard script not found: $SCRIPT_DIR/notes-sync-guard.sh"
    exit 1
fi

chmod +x "$SCRIPT_DIR/notes-sync-guard.sh"
chmod +x "$SCRIPT_DIR/notes_to_obsidian_sync.py"
mkdir -p "$SCRIPT_DIR/logs"
mkdir -p "$HOME/Library/LaunchAgents"

echo "[1/3] Installing LaunchAgent plist..."
cp "$PLIST_SRC" "$PLIST_DST"
chmod 644 "$PLIST_DST"
echo "      -> $PLIST_DST"

echo "[2/3] Reloading notes sync LaunchAgent..."
launchctl bootout "$UID_TARGET/$LABEL" 2>/dev/null || true
launchctl bootstrap "$UID_TARGET" "$PLIST_DST" 2>/dev/null || launchctl load "$PLIST_DST"

echo "[3/3] Verifying service status..."
if launchctl list | grep -q "$LABEL"; then
    echo "SUCCESS: $LABEL is loaded."
else
    echo "ERROR: $LABEL is not shown in launchctl list."
    exit 1
fi

echo ""
echo "Schedule: 19:00, 20:00, 21:00, 22:00 and 23:00 daily."
echo "Source note title: $(/usr/bin/python3 - <<'PY'
import json
from pathlib import Path
cfg = json.loads(Path('/Users/taoli/andrewData/health-tracker/config/notes_sync.json').read_text(encoding='utf-8'))
print(cfg.get('source_note_title','晨间语音备忘'))
PY
)"
echo ""
echo "Useful commands:"
echo "  launchctl list | grep notes-sync"
echo "  tail -f $SCRIPT_DIR/logs/notes-sync-$(date +%Y%m%d).log"
echo "  tail -f $SCRIPT_DIR/logs/launchd-notes-sync-err.log"

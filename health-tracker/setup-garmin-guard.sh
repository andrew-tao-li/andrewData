#!/bin/bash
# Install launchd automation for the guarded "python3 -m cli garmin-sync --date today" workflow.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_NAME="com.health-tracker.garmin-guard.plist"
PLIST_SRC="$SCRIPT_DIR/$PLIST_NAME"
PLIST_DST="$HOME/Library/LaunchAgents/$PLIST_NAME"
LABEL="com.health-tracker.garmin-guard"
UID_TARGET="gui/$(id -u)"

echo "========================================="
echo "Health Tracker - Garmin Guard Installer"
echo "========================================="
echo ""

if [ ! -f "$PLIST_SRC" ]; then
    echo "ERROR: plist file not found: $PLIST_SRC"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/garmin-sync-guard.sh" ]; then
    echo "ERROR: guard script not found: $SCRIPT_DIR/garmin-sync-guard.sh"
    exit 1
fi

chmod +x "$SCRIPT_DIR/garmin-sync-guard.sh"
mkdir -p "$SCRIPT_DIR/logs"
mkdir -p "$HOME/Library/LaunchAgents"

echo "[1/4] Installing LaunchAgent plist..."
cp "$PLIST_SRC" "$PLIST_DST"
chmod 644 "$PLIST_DST"
echo "      -> $PLIST_DST"

echo "[2/4] Reloading guarded LaunchAgent..."
launchctl bootout "$UID_TARGET/$LABEL" 2>/dev/null || true
launchctl bootstrap "$UID_TARGET" "$PLIST_DST" 2>/dev/null || launchctl load "$PLIST_DST"
launchctl kickstart -k "$UID_TARGET/$LABEL" 2>/dev/null || true

echo "[3/4] Disabling legacy schedulers to avoid duplicate writes..."
launchctl bootout "$UID_TARGET/com.health-tracker.scheduler" 2>/dev/null || true
launchctl bootout "$UID_TARGET/com.health-tracker.sync" 2>/dev/null || true

echo "[4/4] Verifying service status..."
if launchctl list | grep -q "$LABEL"; then
    echo "SUCCESS: $LABEL is loaded."
else
    echo "ERROR: $LABEL is not shown in launchctl list."
    exit 1
fi

echo ""
echo "Automation window: 12:00-16:00 every hour."
echo "Command guarded: python3 -m cli garmin-sync --date today"
echo ""
echo "Useful commands:"
echo "  launchctl list | grep health-tracker"
echo "  tail -f $SCRIPT_DIR/logs/garmin-guard-$(date +%Y%m%d).log"
echo "  tail -f $SCRIPT_DIR/logs/launchd-guard-err.log"
echo ""

#!/bin/bash
# Launchd-triggered guard that ensures today's Garmin sync runs once between 12:00 and 18:00.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

LOG_DIR="$SCRIPT_DIR/logs"
STATE_DIR="$LOG_DIR/guard-state"
LOCK_DIR="$STATE_DIR/lock"

TODAY="$(date '+%Y-%m-%d')"
TODAY_COMPACT="$(date '+%Y%m%d')"
CURRENT_HOUR_RAW="$(date '+%H')"
CURRENT_HOUR=$((10#$CURRENT_HOUR_RAW))

RUN_LOG="$LOG_DIR/garmin-guard-${TODAY_COMPACT}.log"
MARKER_FILE="$STATE_DIR/success-${TODAY}.flag"

mkdir -p "$LOG_DIR" "$STATE_DIR"

ts() {
    date '+%Y-%m-%d %H:%M:%S'
}

log() {
    printf '%s | %s\n' "$(ts)" "$1" | tee -a "$RUN_LOG"
}

cleanup() {
    rmdir "$LOCK_DIR" 2>/dev/null || true
}

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    log "skip: another guard process is running"
    exit 0
fi
trap cleanup EXIT

# Keep only recent success markers.
find "$STATE_DIR" -name 'success-*.flag' -mtime +30 -delete 2>/dev/null || true

if [ "$CURRENT_HOUR" -lt 12 ] || [ "$CURRENT_HOUR" -gt 18 ]; then
    log "skip: outside allowed window 12:00-18:59 (current_hour=${CURRENT_HOUR_RAW})"
    exit 0
fi

if [ -f "$MARKER_FILE" ]; then
    log "skip: sync already succeeded today (${TODAY})"
    exit 0
fi

if [ ! -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    log "error: missing virtual environment at $SCRIPT_DIR/venv"
    exit 1
fi

OUTPUT_FILE="$(mktemp "${TMPDIR:-/tmp}/garmin-guard.XXXXXX")"
CMD_EXIT=0

log "start: running manual command -> python3 -m cli garmin-sync --date today"

source "$SCRIPT_DIR/venv/bin/activate"
NO_COLOR=1 PYTHONUNBUFFERED=1 python3 -m cli garmin-sync --date today >"$OUTPUT_FILE" 2>&1 || CMD_EXIT=$?
deactivate >/dev/null 2>&1 || true

while IFS= read -r line; do
    log "cmd: $line"
done < "$OUTPUT_FILE"

# 只有“完整成功”才创建当天 marker。
# 若出现数据不完整/关键字段缺失，则继续按小时重试（12:00-18:00）。
HAS_SUCCESS=0
HAS_INCOMPLETE=0

if grep -q "Garmin 数据同步成功" "$OUTPUT_FILE"; then
    HAS_SUCCESS=1
fi

if grep -Eq "数据验证失败|数据不完整，但仍会保存|获取睡眠数据失败|获取 HRV 数据失败" "$OUTPUT_FILE"; then
    HAS_INCOMPLETE=1
fi

if [ "$HAS_SUCCESS" -eq 1 ] && [ "$HAS_INCOMPLETE" -eq 0 ]; then
    {
        echo "date=$TODAY"
        echo "succeeded_at=$(ts)"
        echo "command=python3 -m cli garmin-sync --date today"
        echo "log=$RUN_LOG"
    } > "$MARKER_FILE"
    log "success: marker created -> $MARKER_FILE"
    rm -f "$OUTPUT_FILE"
    exit 0
fi

if [ "$HAS_SUCCESS" -eq 1 ] && [ "$HAS_INCOMPLETE" -eq 1 ]; then
    log "partial-success: sync finished but key fields incomplete, marker not created (will retry next hour)"
    rm -f "$OUTPUT_FILE"
    exit 1
fi

if [ "$CMD_EXIT" -ne 0 ]; then
    log "failed: command exit code = $CMD_EXIT"
else
    log "failed: success marker text not found in command output"
fi

rm -f "$OUTPUT_FILE"
exit 1

#!/bin/bash
# Guard wrapper for syncing iPhone Notes -> Obsidian

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

LOG_DIR="$SCRIPT_DIR/logs"
STATE_DIR="$LOG_DIR/notes-sync-state"
LOCK_DIR="$STATE_DIR/lock"
TODAY="$(date '+%Y-%m-%d')"
TODAY_COMPACT="$(date '+%Y%m%d')"
RUN_LOG="$LOG_DIR/notes-sync-${TODAY_COMPACT}.log"
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
    log "skip: another notes sync process is running"
    exit 0
fi
trap cleanup EXIT

# Keep only recent success markers.
find "$STATE_DIR" -name 'success-*.flag' -mtime +30 -delete 2>/dev/null || true

if [ -f "$MARKER_FILE" ]; then
    log "skip: notes sync already succeeded today (${TODAY})"
    exit 0
fi

OUTPUT_FILE="$(mktemp "${TMPDIR:-/tmp}/notes-sync.XXXXXX")"
CMD_EXIT=0

log "start: syncing iPhone Notes to Obsidian"
PYTHON_BIN="/usr/bin/python3"
if [ -x "$SCRIPT_DIR/venv/bin/python3" ]; then
    PYTHON_BIN="$SCRIPT_DIR/venv/bin/python3"
fi
log "using python: $PYTHON_BIN"
"$PYTHON_BIN" "$SCRIPT_DIR/notes_to_obsidian_sync.py" >"$OUTPUT_FILE" 2>&1 || CMD_EXIT=$?
while IFS= read -r line; do
    log "cmd: $line"
done < "$OUTPUT_FILE"

if [ "$CMD_EXIT" -eq 0 ]; then
    if grep -q "memo synced ->" "$OUTPUT_FILE"; then
        {
            echo "date=$TODAY"
            echo "succeeded_at=$(ts)"
            echo "command=notes-sync-guard.sh"
            echo "log=$RUN_LOG"
        } > "$MARKER_FILE"
        log "success: marker created -> $MARKER_FILE"
    elif grep -q "no new memo content" "$OUTPUT_FILE"; then
        log "success: no new memo content, marker not created (will retry next slot)"
    fi
    rm -f "$OUTPUT_FILE"
    log "success: notes sync finished"
    exit 0
fi

rm -f "$OUTPUT_FILE"
log "failed: notes sync exited with code $CMD_EXIT"
exit 1

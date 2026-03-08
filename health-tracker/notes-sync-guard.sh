#!/bin/bash
# Guard wrapper for syncing iPhone Notes -> Obsidian

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

LOG_DIR="$SCRIPT_DIR/logs"
STATE_DIR="$LOG_DIR/notes-sync-state"
LOCK_DIR="$STATE_DIR/lock"
TODAY_COMPACT="$(date '+%Y%m%d')"
RUN_LOG="$LOG_DIR/notes-sync-${TODAY_COMPACT}.log"

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

OUTPUT_FILE="$(mktemp "${TMPDIR:-/tmp}/notes-sync.XXXXXX")"
CMD_EXIT=0

log "start: syncing iPhone Notes to Obsidian"
/usr/bin/python3 "$SCRIPT_DIR/notes_to_obsidian_sync.py" >"$OUTPUT_FILE" 2>&1 || CMD_EXIT=$?
while IFS= read -r line; do
    log "cmd: $line"
done < "$OUTPUT_FILE"
rm -f "$OUTPUT_FILE"

if [ "$CMD_EXIT" -eq 0 ]; then
    log "success: notes sync finished"
    exit 0
fi

log "failed: notes sync exited with code $CMD_EXIT"
exit 1

# Current Automation Status

Updated: 2026-07-29

This file is the current source of truth for daily automation. Older automation
docs and scripts may still exist for historical context, but should not be used
unless explicitly debugging a legacy path.

## Active Jobs

### Garmin Health Sync

- LaunchAgent: `com.health-tracker.garmin-guard`
- Command guarded by the job: `python3 -m cli garmin-sync --date today`
- Schedule: `12:00`, `13:00`, `14:00`, `15:00`, `16:00`
- Stop condition: once a success flag exists for the date, later runs skip.
- Success flag directory: `logs/guard-state/`
- Required Garmin fields before writing: `sleep_duration`, `hrv`

Write order:

1. Obsidian daily note health block
2. Obsidian local 7-day health analysis
3. SQLite local database
4. Google Sheets

The 7-day health analysis used by daily Garmin sync is local and deterministic.
It does not require OpenRouter or an Anthropic API key.

### Morning Notes Sync

- LaunchAgent: `com.health-tracker.notes-sync`
- Source note title: `晨间备忘录`
- Schedule: `19:00`, `20:00`, `21:00`, `22:00`, `23:00`
- Stop condition: once the note is written and cleared successfully, later runs
  skip or find no content.
- State directory: `logs/notes-sync-state/`

Expected behavior:

1. Read the macOS Notes note titled `晨间备忘录`.
2. Write real dictated content into today's Obsidian daily note.
3. Only after confirmed Obsidian write, clear the note body while keeping the
   note title.

## Do Not Re-Enable

Do not use these legacy launch jobs for daily automation:

- `com.health-tracker.scheduler`
- `com.health-tracker.sync`

Do not use these legacy setup scripts for normal operation:

- `setup-scheduler.sh`
- `setup-and-verify-automation.sh`
- direct manual loading of `com.health-tracker.scheduler.plist`
- direct manual loading of `com.health-tracker.sync.plist`

Reason: the legacy scheduler path used older assumptions, including syncing the
wrong day in some cases and relying on older AI/model configuration. The current
guard-based jobs are narrower and more predictable.

Both legacy scheduler setup scripts now refuse to run unless explicitly invoked
with:

```bash
HEALTH_TRACKER_ALLOW_LEGACY_SCHEDULER=1 ./setup-scheduler.sh
```

That override is only for debugging, not for the normal daily system.

The legacy `sync-auto.sh` script also refuses to run unless explicitly invoked
with:

```bash
HEALTH_TRACKER_ALLOW_LEGACY_SYNC_AUTO=1 ./sync-auto.sh
```

## Manual Safe Commands

Use these when a manual check or backfill is needed:

```bash
cd /Users/taoli/andrewData/health-tracker
source venv/bin/activate
python3 -m cli garmin-sync --date today
python3 -m cli garmin-sync --date 2026-07-29
python3 -m cli sync-one-to-sheets --date 2026-07-29
```

After a successful manual same-day backfill, create or verify the corresponding
success flag in `logs/guard-state/` to prevent a later duplicate automatic run.

## AI Model Configuration

OpenRouter is configured with a primary model and fallbacks:

- Primary: `anthropic/claude-sonnet-5`
- Fallback 1: `anthropic/claude-sonnet-4.6`
- Fallback 2: `anthropic/claude-sonnet-4.5`

The daily Garmin automation does not depend on these models for its local
7-day health brief, but other manual analysis commands may still use them.

# Snapshot Registry

Updated: 2026-07-29 13:25 CST

## Current recommended rollback point
- Tag: `jit-20260729-132547-automation-api-hardening`
- Commit: resolve with `git rev-parse jit-20260729-132547-automation-api-hardening`
- Local backup dir: `backups/20260729-132547-jit-automation-api-hardening`
- Key features:
  - Garmin daily automation with guard window (12:00-16:00).
  - Success chain: Obsidian -> SQLite -> Google Sheets.
  - Daily Obsidian analysis uses local current-day vs prior 7-day baseline and no longer depends on OpenRouter/API availability.
  - OpenRouter model config updated to current Sonnet with fallback models.
  - SQLite exercise writes are deduplicated to tolerate automatic retries and manual reruns.
  - iPhone Notes -> Obsidian auto-sync in the evening (19:00, 20:00, 21:00, 22:00, 23:00).
  - Notes sync stops after the first successful write of the day.
  - Notes content is archived locally before source note clearing.
  - Legacy scheduler/sync-auto paths are blocked by default to avoid re-enabling old behavior.
  - Current automation source of truth documented in `CURRENT_AUTOMATION_STATUS.md`.

## Snapshot list
1. `backup-20260306-1208`
- Commit: `2d4cd0a5462a2d9e148e279f6d3ed09d703385d0`
- Backup dirs:
  - `backups/20260306-1208-baseline`
  - `backups/20260306-1208-baseline-clean`
- Stable milestone:
  - Baseline rollback point requested by user.

2. `milestone-20260307-obsidian-ok`
- Commit: `2d4cd0a5462a2d9e148e279f6d3ed09d703385d0`
- Backup dir: `backups/20260307-161908-milestone-obsidian-ok`
- Stable milestone:
  - Obsidian write path verified stable.

3. `milestone-20260307-obsidian-db-sheets-analysis-ok`
- Commit: `2b2d6f14c5e37abd2a44dba22d1e44a564ca2b3d`
- Backup dir: `backups/20260307-163150-milestone-obsidian-db-sheets-analysis-ok`
- Stable milestone:
  - Enforced write order: Obsidian -> DB -> Google Sheets.
  - Google Sheets sync added with retries.
  - Upgraded daily analysis to same-day + 7-day baseline comparison.

4. `jit-20260308-083945`
- Commit: `2b2d6f14c5e37abd2a44dba22d1e44a564ca2b3d`
- Backup dir: `backups/20260308-083945-jit-snapshot`
- Stable milestone:
  - JIT snapshot before Notes automation implementation.

5. `jit-20260308-084605-notes-sync-ready`
- Commit: `e8142a38574c53207f912253543a2d0362f7d016`
- Backup dir: `backups/20260308-084605-jit-notes-sync-ready`
- Stable milestone:
  - iPhone Notes sync automation installed and tested.

6. `jit-20260308-084749-registry`
- Commit: `8274fc06a0dfd8dda10d8e54c06bc39c6b4ee072`
- Backup dir: `backups/20260308-084841-jit-registry`
- Stable milestone:
  - Added snapshot registry and rollback instructions.

7. `jit-20260317-195516-automation-stable`
- Commit: `19d8b9011cd9883ba2b59118272f58404e34c35c`
- Backup dir: `backups/20260317-195516-jit-automation-stable`
- Stable milestone:
  - Hardened Garmin sleep/HRV parsing against null values.
  - Fixed analysis updates so they no longer delete the Notes memo section.
  - Added local Notes memo archive before source-note clearing.
  - Notes sync runs via the venv Python in launchd.
  - Garmin guard/install files were brought into Git tracking.

8. `jit-20260317-201415-sync-window-update`
- Commit: `d51f1cf9907116b3a12815d3a35c1fbbe2e10861`
- Backup dir: `backups/20260317-201415-jit-sync-window-update`
- Stable milestone:
  - Garmin retry window adjusted to 12:00, 13:00, 14:00, 15:00, 16:00.
  - Notes sync window adjusted to 19:00, 20:00, 21:00.
  - Notes sync now creates a daily success marker after the first actual sync.
  - Installer docs and launchd plists updated to match the new schedule.

9. `jit-20260317-203916-registry-aligned`
- Commit: `07e1922e48cc4b80f6ec66f5c5567111663a09a5`
- Backup dir: `backups/20260317-203916-jit-registry-aligned`
- Stable milestone:
  - Registry alignment snapshot after the sync-window update.
  - Preserved the rollback inventory and local bundle path references.

10. `jit-20260318-131704-garmin-partial-write-fix`
- Commit: `d1fabdb627cbf4fd525d0685580f1d5595ada3da`
- Backup dir: `backups/20260318-131704-jit-garmin-partial-write-fix`
- Stable milestone:
  - Prevented incomplete Garmin data from overwriting already-good logs.
  - Hardened Garmin parsing against partial sleep/HRV responses.
  - Added tests around Garmin partial-write behavior.

11. `jit-20260318-192604-notes-title-stable`
- Commit: `ff2057523517f793a65545f8d69e4c8e2d547e4b`
- Backup dir: `backups/20260318-192604-jit-notes-title-stable`
- Stable milestone:
  - Kept the source iPhone/macOS Notes title stable as `晨间备忘录`.
  - Continued clearing note content after successful Obsidian write without deleting/renaming the note.

12. `jit-20260729-132547-automation-api-hardening`
- Commit: resolve with `git rev-parse jit-20260729-132547-automation-api-hardening`
- Backup dir: `backups/20260729-132547-jit-automation-api-hardening`
- Stable milestone:
  - Consolidated the working July 2026 automation state before further changes.
  - Updated OpenRouter/Claude model defaults and added fallback model handling.
  - Removed OpenRouter dependency from the Garmin daily 7-day brief path.
  - Added SQLite exercise deduplication for retry/manual rerun safety.
  - Added hard stops for legacy scheduler and sync-auto paths.
  - Added `CURRENT_AUTOMATION_STATUS.md` as the current automation reference.

## Rollback commands

### Fast rollback by tag
```bash
git fetch --tags
git checkout <tag>
```

### Full repo restore from local backup bundle
```bash
git clone backups/<backup-dir>/repo-all.bundle /tmp/health-tracker-restore
cd /tmp/health-tracker-restore
git checkout <tag-or-commit>
```

### Restore untracked files snapshot (optional)
```bash
cd /tmp/health-tracker-restore
tar -xzf /Users/taoli/andrewData/health-tracker/backups/<backup-dir>/untracked_files.tgz
```

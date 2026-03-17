# Snapshot Registry

Updated: 2026-03-17 20:15 CST

## Current recommended rollback point
- Tag: `jit-20260317-201415-sync-window-update`
- Commit: `d51f1cf9907116b3a12815d3a35c1fbbe2e10861`
- Local backup dir: `backups/20260317-201415-jit-sync-window-update`
- Key features:
  - Garmin daily automation with guard window (12:00-16:00).
  - Success chain: Obsidian -> SQLite -> Google Sheets.
  - Daily Obsidian analysis uses current-day record vs prior 7-day baseline.
  - iPhone Notes -> Obsidian auto-sync in the evening (19:00, 20:00, 21:00).
  - Notes sync stops after the first successful write of the day.
  - Notes content is archived locally before source note clearing.
  - Garmin and Notes automation files are tracked in Git.

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

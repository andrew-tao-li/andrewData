# Snapshot Registry

Updated: 2026-03-08 08:47 CST

## Current recommended rollback point
- Tag: `jit-20260308-084605-notes-sync-ready`
- Commit: `e8142a38574c53207f912253543a2d0362f7d016`
- Local backup dir: `backups/20260308-084605-jit-notes-sync-ready`
- Key features:
  - Garmin daily automation with guard window (12:00-18:00).
  - Success chain: Obsidian -> SQLite -> Google Sheets.
  - Daily Obsidian analysis uses current-day record vs prior 7-day baseline.
  - iPhone Notes -> Obsidian auto-sync before 18:00 (17:40 and 17:55).

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

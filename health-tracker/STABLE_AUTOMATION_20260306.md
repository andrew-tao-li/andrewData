# Stable macOS Automation (2026-03-06)

## Goal

Run this exact manual command automatically:

```bash
python3 -m cli garmin-sync --date today
```

Schedule rules:
- Run at 12:00.
- Between 12:00 and 16:00, check every hour.
- If today already succeeded, skip (no duplicate write).

## Files

- `garmin-sync-guard.sh`: guarded executor (success marker + lock + logging).
- `com.health-tracker.garmin-guard.plist`: launchd schedule (12:00..16:00 hourly).
- `setup-garmin-guard.sh`: installer for LaunchAgent.

## Install

```bash
cd /Users/taoli/andrewData/health-tracker
chmod +x setup-garmin-guard.sh garmin-sync-guard.sh
./setup-garmin-guard.sh
```

## Verify

```bash
launchctl list | grep health-tracker
tail -f /Users/taoli/andrewData/health-tracker/logs/garmin-guard-$(date +%Y%m%d).log
```

Success marker path:

```text
/Users/taoli/andrewData/health-tracker/logs/guard-state/success-YYYY-MM-DD.flag
```

## Rollback to baseline

Git baseline tag:

```text
backup-20260306-1208
```

Rollback command:

```bash
cd /Users/taoli/andrewData
git checkout backup-20260306-1208
```

Local snapshot (tracked refs + untracked archive):

```text
/Users/taoli/andrewData/health-tracker/backups/20260306-1208-baseline-clean/
```

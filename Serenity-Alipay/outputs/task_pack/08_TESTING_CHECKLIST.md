# 08 Testing Checklist

## Unit Tests

- `test_timezones.py`
  - Beijing slot converts to Australia/Sydney using timezone database.
  - 10 slots exist exactly from 08:30 through 17:30 Beijing time.
- `test_import_alipay.py`
  - Valid CSV imports.
  - Missing required columns fails with useful error.
  - Current weights sum warning works.
- `test_quality.py`
  - Missing > 2 days triggers Manual Review.
  - Official sources < 2 blocks Action-Ready.
  - Aggregated fallback limits grade.
- `test_metrics.py`
  - 1m/3m/10D returns.
  - MDD.
  - Recovery time.
- `test_scoring.py`
  - Score thresholds.
  - Hard gates override score.
- `test_discipline.py`
  - Deviation > 1.00% triggers rebalance candidate.
  - Single position over-expansion > 2 consecutive runs triggers risk alert.
- `test_notification.py`
  - Urgent/Info/Warn templates render required fields.

## Integration Tests

- Create DB, import Alipay CSV, run dry-run slot R7, generate report.
- Simulate missing fee/redemption status and verify No-New-Order.
- Simulate MDD >= 40.00% and verify Block.
- Simulate recovery time >= 365 days and verify Manual Review or Block.
- Simulate Top5 replacement >= 2 and verify Alert.

## Manual Smoke Tests

```bash
python -m app.cli doctor
python -m app.cli init-db
python -m app.cli import-alipay --csv data/imports/alipay_positions.csv
python -m app.cli run --slot R7 --dry-run
python -m app.cli report --run-id <run_id>
python -m app.cli notify --run-id <run_id> --dry-run
python -m app.cli mail-smoke --json
```

## Security Tests

- Search for hardcoded secrets.
- Verify dry-run default.
- Verify no browser cookies or passwords are stored.
- Verify notification failure is logged.
- Verify real Apple Mail send stays blocked unless `SERENITY_MAIL_SEND_ENABLED=true` and `--confirm-real-send SEND` are both present.

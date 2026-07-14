# SQLite Transition Notes

SQLite may remain useful as a local ledger/cache during migration, but the target payroll-grade database should be PostgreSQL-compatible.

## Recommended role for SQLite

| Use | Allowed |
|---|---:|
| Local replay cache | Yes |
| Single-user temporary ledger | Yes |
| Raw manifest index | Yes |
| Multi-user source for payroll baseline | No |
| Shared OneDrive database with concurrent writers | No |

## Transition pattern

```text
OneDrive raw archive
  -> local SQLite replay/index if useful
  -> PostgreSQL raw_import_batch / raw_attendance_result / raw_attendance_detail
  -> derived facts
  -> canonical snapshot
  -> stage-2 consensus
  -> payroll baseline table/view
```

## Cutover rule

Once PostgreSQL ingestion is enabled, stage-2 and payroll baseline artifacts should come from PostgreSQL-backed pipeline outputs. SQLite can still be used for local reconstruction and debugging.

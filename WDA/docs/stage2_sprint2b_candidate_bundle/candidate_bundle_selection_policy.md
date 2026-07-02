# Candidate Bundle Selection Policy

Generated: 2026-07-03T08:13:49+10:00

Included domains:
- `db_storage/message`
- `db_storage/contact`
- `db_storage/session`
- `db_storage/favorite` when non-sensitive and useful for schema/domain context
- `db_storage/general` when non-sensitive and useful for schema/domain context

Selection rules:
- Main candidates come from Sprint 2 `wal_shm_companion_map.csv` rows in the included domains.
- WAL/SHM companions are included only when their main candidate is selected.
- Every selected path must have `schema_opened=false` and `message_or_contact_rows_selected=false` at bundle time.

Always excluded:
- `key_info`
- `login`
- `MMKV`
- `.kvdb`, `.kvdb-wal`, `.kvdb-shm`, and key-value store paths
- `protected_key_info_or_login`
- Any row listed in Sprint 2 `sensitive_skip_list.csv`
- Raw media/cache paths under `msg/file`, `msg/attach`, or `msg/video`
- The abandoned ExFAT partial copy

This bundle is for schema-only read-only probing. It is not evidence that message content is readable.

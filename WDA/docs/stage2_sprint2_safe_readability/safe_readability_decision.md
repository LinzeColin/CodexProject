# Safe Readability Decision

Generated: 2026-07-03T07:50:11+10:00

## Decision

Safe readability status: **container/header classification complete; message readability not proven**.

Raw Gate decision remains: **Conditional Investigation**.

## Classification Summary

| Metric | Count |
|---|---:|
| Manifest file rows | 115200 |
| DB/container candidate rows | 373 |
| Plain SQLite possible | 7 |
| Encrypted or SQLCipher likely | 59 |
| WCDB or unknown | 66 |
| WAL/SHM companion files | 146 |
| Sensitive skip | 95 |

Signature categories:

| Signature category | Count |
|---|---:|
| empty_file | 33 |
| non_sqlite_header | 193 |
| not_read_sensitive_skip | 95 |
| sqlite_header | 7 |
| sqlite_wal_header | 45 |

## Highest-value Domains

| Domain | Candidate rows |
|---|---:|
| `db_storage/message` | 137 |
| `mmkv_or_key_value` | 46 |
| `db_storage/MMKV` | 36 |
| `db_storage/contact` | 23 |
| `db_storage/session` | 20 |
| `app_data/radium_db` | 19 |
| `db_storage/favorite` | 18 |
| `protected_key_info_or_login` | 13 |
| `db_storage/hardlink` | 9 |
| `db_storage/head_image` | 9 |
| `db_storage/sns` | 9 |
| `db_storage/general` | 9 |

## What This Does Not Prove

- It does not prove messages are readable.
- It does not prove contacts are readable.
- It does not prove WDA Raw Gate is Go.
- It does not prove encrypted/WCDB containers can be parsed.
- It does not authorize schema opening or message/contact row selection.

## Recommendation

Proceed only to a separately approved Sprint 2B schema-only probe on a copied candidate bundle, prioritizing non-sensitive `db_storage/message`, `db_storage/contact`, and `db_storage/session` domains. Keep `key_info`, login paths, and MMKV/key-value stores as skip/no-open.

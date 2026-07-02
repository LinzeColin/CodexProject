# Schema Probe Scope

Generated: 2026-07-03T08:15:45+10:00

Allowed in this pass:
- Open only copied local `main_candidate` files listed in the candidate bundle manifest.
- Use SQLite read-only URI mode: `mode=ro&immutable=1`.
- Run `PRAGMA database_list`, `PRAGMA page_count`, `PRAGMA page_size`.
- Read `sqlite_master` object names/types.
- Run `PRAGMA table_info(table_name)` for schema columns only.

Forbidden and not performed:
- Decrypt, key extract, SQLCipher key attempts, protected-store bypass.
- Open or parse `key_info`, `login`, MMKV, KVDB, or key-value stores.
- Select message/contact/business rows.
- Parse message text, contacts, media, attachments, or chat exports.
- Upload raw data.

This pass can classify schema readability only. It cannot prove message readability.

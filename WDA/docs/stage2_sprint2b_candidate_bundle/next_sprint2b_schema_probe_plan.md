# Next Sprint 2B-B Schema Probe Plan

Generated: 2026-07-03T08:13:49+10:00

Input:
- Local bundle: `/Users/linzezhang/Downloads/WDA_MetaData/raw_ferry/sprint2b_candidate_db_bundle_20260703`
- Manifest: `WDA/docs/stage2_sprint2b_candidate_bundle/candidate_bundle_manifest.csv`

Allowed operations:
- Open only main candidate DB files from the manifest.
- Use SQLite read-only mode only.
- Read `sqlite_master` object names/types.
- Run `PRAGMA database_list`, `PRAGMA table_info(table_name)`, `PRAGMA page_count`, and `PRAGMA page_size`.

Forbidden operations:
- Decryption, key extraction, SQLCipher key attempts, protected-store bypass.
- Opening `key_info`, `login`, MMKV, KVDB, or key-value stores.
- Selecting message/contact/business rows.
- Parsing text, contacts, media, attachments, or chat exports.
- Uploading raw data.

Stop conditions:
- Any manifest row is later found to include a denied path.
- Any SQLite operation would require a key, bypass, or content row read.
- Any external-drive dependency appears during Sprint 2B-B.

Expected decision output:
- Classify plain SQLite schema-readable candidates versus encrypted/unknown candidates.
- Keep message readability unproven unless a later approved content-safe step produces explicit evidence.
- Keep Raw Gate at Conditional Investigation.

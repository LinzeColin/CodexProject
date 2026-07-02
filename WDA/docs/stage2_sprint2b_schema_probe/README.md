# WDA Stage 2 Sprint 2B-B Schema-Only Probe

Generated: 2026-07-03T08:15:45+10:00

Purpose: determine whether copied non-sensitive DB candidates can be opened as plain SQLite in read-only mode and whether schema names suggest message/contact/session relevance.

Input used:
- Local bundle only: `/Users/linzezhang/Downloads/WDA_MetaData/raw_ferry/sprint2b_candidate_db_bundle_20260703`
- Manifest: `WDA/docs/stage2_sprint2b_candidate_bundle/candidate_bundle_manifest.csv`

Result summary:
- Main candidates probed: 91
- Plain SQLite read-only open successes: 0
- Read-only open failures: 91
- Schema objects recorded: 0
- Table column metadata rows: 0
- Possible message-domain schema candidates: 0

Boundary:
- No external hard drive was needed or accessed.
- No decryption, key extraction, SQLCipher key attempt, protected-store bypass, or third-party export tool was used.
- No message/contact/business content rows were selected.
- Message readability is still not proven.
- Raw Gate remains Conditional Investigation.

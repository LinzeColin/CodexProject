# Next Sprint 2B or Raw Import Plan

Generated: 2026-07-03T07:50:11+10:00

## Recommended Next Step

Run Sprint 2B as a schema-only, read-only probe on a copied candidate DB bundle. Do not query message rows or contact rows.

## Candidate Bundle Scope

1. Include only selected non-sensitive candidates from `db_storage/message`, `db_storage/contact`, and `db_storage/session` plus needed `.db-wal` / `.db-shm` companions.
2. Exclude `key_info.db`, `all_users/login/**`, MMKV, protected-store-adjacent files, and unrelated media payloads.
3. Keep a manifest with relative path, size, mtime, SHA-256, domain, and source sparseimage reference.
4. Store bundle under local WDA metadata, not under the repo, and do not commit raw DB files.

## Sprint 2B Allowed Actions If Approved

- Verify copied file hashes.
- Open non-sensitive DB containers read-only for schema-only metadata.
- Record table names/counts only if explicitly allowed by the Sprint 2B contract.
- Still do not select or parse message/contact rows.

## Stop Conditions

- Any need for decryption, key extraction, Keychain access, protected-store bypass, or third-party WeChat decrypt/export tools.
- Any need to open `key_info.db`, MMKV, or login/key-material-adjacent stores.
- Any query that selects message content, contact content, media payloads, or raw user-generated content.
- Any attempt to commit raw DB files, sparseimage contents, message files, or extracted raw data.

## Raw Import Position

Raw import is not approved from Sprint 2 first pass. The earliest safe escalation is Sprint 2B schema-only probe. Raw Gate remains Conditional Investigation until a later explicit gate proves readability under approved constraints.

# Raw Gate Decision

Generated: 2026-07-03T09:04:48+10:00

Decision: **Raw Gate remains Conditional Investigation.**

Raw Gate is **not Go**.

## Basis

- Sprint 2 classified DB/container candidates without proving message readability.
- Sprint 2B-A created a local copied non-sensitive candidate bundle and excluded sensitive/key-value/cache paths.
- Sprint 2B-B probed 91 main candidates with SQLite read-only mode.
- Sprint 2B-B produced 0 plain SQLite schema-open successes.
- No message, contact, or business rows were selected.
- No `messages.jsonl` has been produced in WDA stage outputs.

## Consequence

WDA cannot start RAG/Web/Matrix implementation that depends on message-level data. The next step must be a route decision and owner authorization step, not raw import.

## Non-Negotiable Limits

The following remain forbidden:
- Decryption or key extraction.
- SQLCipher key attempts.
- Protected-store bypass.
- Opening `key_info`, login paths, MMKV, KVDB, or key-value stores.
- Selecting message/contact/business rows before a dedicated approved content-read contract.
- Running third-party WeChat export/decrypt tools.
- Uploading raw data.

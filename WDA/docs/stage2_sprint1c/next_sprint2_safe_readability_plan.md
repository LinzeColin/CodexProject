# WDA Stage 2 Sprint 2 Safe Readability Plan

## Goal

Classify whether a small copied candidate DB bundle can be safely inspected on the new computer without decrypting, extracting keys, bypassing protected stores, opening message content, or copying the full old WeChat cache.

## Recommended Host Split

- Old computer: source for selected candidate DB files only.
- New computer: WDA Control Plane, WDA_HOME, staging area, database/RAG/Web host, and all heavy analysis.

## Input Strategy

Do not copy the full old WeChat cache. Instead, create a minimal copied candidate DB bundle from the old computer, using the Sprint 1C inventory as the manifest source.

Initial bundle priority:

1. `db_storage/message` candidate files from old computer.
2. Required adjacent SQLite companion files when present: `.db`, `.db-wal`, `.db-shm` for the same basename.
3. Minimal manifest CSV with source path, copied filename, size, mtime, hash, and account bucket.
4. Exclude `key_info.db`, MMKV/key-material-adjacent stores, protected-store artifacts, and unrelated media/document cache.

## Safe Classification Levels

| Level | Name | Allowed action | Message readability claim |
|---|---|---|---|
| L0 | manifest-only | Verify copied file existence, size, mtime, hash against manifest. | No |
| L1 | file-signature-only | Check file magic/header bytes and extension class. | No |
| L2 | SQLite-openability-only | If explicitly approved, test whether copied DB opens as SQLite without listing schema or querying tables. | No |
| L3 | schema-readability | Requires a separate approval gate because current Sprint 1C scope forbids DB schema opening. | No message content |
| L4 | content-readability | Out of scope until a future explicit owner gate. | Yes, but not allowed now |

## Acceptance for Sprint 2

- Uses copied candidate DB bundle only, not source directories.
- Does not decrypt or extract keys.
- Does not parse message content.
- Does not upload raw data.
- Produces a readability classification matrix by file family and account bucket.
- Keeps Raw Gate at Conditional Investigation unless safe readability is explicitly proven by approved checks.

## Stop Conditions

- Any step requires scanning old computer WeChat source directories from the new computer.
- Any step requires copying the full old cache.
- Any step requires key extraction, protected-store bypass, or third-party decrypt/export tools.
- Any step would parse or expose message content before an explicit future gate.

## Expected Output Files

- `sprint2_candidate_db_bundle_manifest.csv`
- `sprint2_safe_readability_matrix.csv`
- `sprint2_readability_gate_summary.md`
- `sprint2_raw_gate_recommendation.md`

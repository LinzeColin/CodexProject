# Recommended Next Route

Generated: 2026-07-03T09:04:48+10:00

Recommendation: prepare Sprint 2C as an **owner-authorized readable artifact intake contract**.

Do not execute the route in Sprint 2B-C.

## Why This Route

The safe plain-SQLite route has been tested and did not produce readable schema evidence for the 91 main candidates. Continuing against copied WeChat DB containers would either repeat the same negative path or move toward forbidden methods.

The highest-ROI next route is to ask the owner to provide a readable message-level artifact through an authorized process. WDA can then validate the artifact shape without decrypting, bypassing protected stores, opening key material, or parsing unsupported raw containers.

## Proposed Sprint 2C Scope

Sprint 2C should define:
- Accepted artifact types, for example a user-provided `messages.jsonl` or equivalent structured export.
- Required manifest fields: source owner, export method, time range, account/device scope, redaction policy, checksum, and allowed storage path.
- Minimal schema contract for message-level import.
- Validation-only first pass: count rows, validate required fields, check encoding, and confirm no secrets are present.
- Stop conditions before any RAG/Web/Matrix ingestion.

## Stop Conditions

Stop if the route requires:
- Decryption or key extraction.
- SQLCipher key attempts.
- Protected-store bypass.
- Opening `key_info`, login paths, MMKV, KVDB, or key-value stores.
- Third-party WeChat export/decrypt tools.
- Raw data upload.
- Message/contact/business row selection from the protected DB bundle.

## Gate

Raw Gate stays `Conditional Investigation` until an approved readable artifact exists and a later validation run proves message-level data can be safely imported.

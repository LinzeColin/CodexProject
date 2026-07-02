# Artifact Validation Rules

Generated: 2026-07-03T09:12:39+10:00

Sprint 2C defines these rules only. It does not run them against a real artifact.

## Validation Order

1. Confirm owner authorization is present in `import_manifest.json`.
2. Confirm the artifact is local and no upload is required.
3. Verify required file presence.
4. Verify checksums and file sizes.
5. Validate JSON/JSONL/CSV syntax.
6. Validate required fields and primitive types.
7. Validate cross-file references: messages to conversations, messages to contacts, and messages to media refs.
8. Produce a validation report that does not include message text or contact values unless explicitly approved.

## First Sample Limits

Recommended first Sprint 2D sample:
- Maximum messages: 100
- Maximum conversations: 20
- Maximum contacts: 50
- Maximum media rows: 20
- Media files: optional and disabled by default

## Stop Conditions

Stop validation immediately if:
- Any step requires decryption, key extraction, SQLCipher keys, or protected-store bypass.
- Any file appears to be `key_info`, login, MMKV, KVDB, key-value store, protected DB, WAL, SHM, or raw WeChat cache.
- Any path points to an external hard drive or protected WeChat source directory.
- Any artifact lacks owner authorization.
- Any validation would upload raw data.

## Output Boundary

A future validation report may include counts, checksums, schema/field errors, and pass/fail status. It must not include raw message text, contact values, or media payloads unless the user explicitly approves a content-level validation contract.

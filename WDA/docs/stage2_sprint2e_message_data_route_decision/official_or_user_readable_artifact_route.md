# Official Or User-Readable Artifact Route

Generated: 2026-07-03T09:43:38+10:00

Recommended route for Sprint 2F.

Goal: obtain a message-level readable artifact through an official, user-controlled, or owner-provided path that already produces readable files. WDA should not decrypt, bypass, or probe protected stores.

Sprint 2F should define:
- Acceptable source methods.
- Required artifact package shape from Sprint 2C.
- Local storage path for the provided artifact.
- Owner authorization statement.
- Checksum and manifest requirements.
- Validation-only first pass.

Allowed future validation:
- Read `import_manifest.json`.
- Verify checksums and file sizes.
- Validate JSONL/CSV shape.
- Count rows.
- Validate cross-file IDs.

Not allowed:
- Protected DB access.
- SQLCipher key attempts.
- `key_info`, login, MMKV, KVDB, or key-value store opening.
- Third-party export/decrypt tool execution.
- Raw upload.

Reason: this is the only route that can plausibly produce message-level input without violating the current safety boundary.

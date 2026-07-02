# Artifact Validation Gate

Generated: 2026-07-03T09:51:08+10:00

Sprint 2G should validate only a provided or approved readable artifact.

Validation order:
1. Confirm artifact lives under the approved storage root.
2. Confirm owner authorization.
3. Confirm allowed file types.
4. Reject protected DB/key/cache files.
5. Verify file checksums and sizes.
6. Validate `import_manifest.json`.
7. Validate JSONL/CSV syntax and required fields.
8. Count rows.
9. Validate cross-file IDs.
10. Produce a local validation report with no raw message text.

Immediate stop conditions:
- Missing owner authorization.
- Artifact outside approved storage root.
- Any protected DB, WAL/SHM, key store, MMKV, KVDB, or raw WeChat cache file.
- Any required decryption, key extraction, protected-store bypass, third-party export/decrypt tool, or upload.
- Any request to implement RAG/Web/Matrix before validation completes.

Validation does not make Raw Gate Go by itself. A separate gate decision is required.

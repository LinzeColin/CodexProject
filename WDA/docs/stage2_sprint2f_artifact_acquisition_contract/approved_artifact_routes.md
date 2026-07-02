# Approved Artifact Routes

Generated: 2026-07-03T09:51:08+10:00

Approved route for future Sprint 2G: **owner-provided or official/user-readable artifact**.

Acceptable source patterns:
- User provides readable files already exported outside WDA.
- Official/user-controlled export produces readable files without WDA decrypting or bypassing protected stores.
- User provides a manually curated or redacted sample artifact.
- User provides a zip package containing only acceptable readable files.

Acceptable file types:
- `.jsonl`
- `.json`
- `.csv`
- `.txt`
- `.md`
- `.html`
- `.zip` containing only the above plus an `import_manifest.json`

Rejected routes:
- Protected DB bundle probing.
- `key_info`, login, MMKV, KVDB, or key-value store access.
- Third-party WeChat export/decrypt tool execution.
- High-risk raw adapter development.
- Raw upload.

Sprint 2F selects the route only. It does not acquire, validate, or import real data.

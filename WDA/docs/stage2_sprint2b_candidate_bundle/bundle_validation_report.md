# Bundle Validation Report

Generated: 2026-07-03T08:13:49+10:00

Validation summary:
- Local bundle exists: true
- Manifest rows: 169
- File count under `files/`: 169
- Checksum rows: 169
- Total copied size: 959938032 bytes (915.47 MiB)
- Main/WAL/SHM counts: 91/39/39
- Deny-marker violations in selected manifest: 0
- Sensitive skip paths copied: 0
- `key_info`/`login`/`MMKV`/`KVDB` paths copied: 0
- `msg/file`, `msg/attach`, `msg/video` cache paths copied: 0
- Local pruned files documented in exclusions: 38

Source modification status:
- No APFS source write was performed.
- No schema was opened in Sprint 2B-A.
- No message/contact rows were selected.
- No copied DB/WAL/SHM files are intended for git.

Decision:
- Sprint 2B-B may proceed using only the local copied bundle.
- Raw Gate remains Conditional Investigation.

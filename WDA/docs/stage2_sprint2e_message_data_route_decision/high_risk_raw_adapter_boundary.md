# High-Risk Raw Adapter Boundary

Generated: 2026-07-03T09:43:38+10:00

Decision: reject for current WDA Stage 2.

High-risk raw adapter work includes any route that would require:
- Decryption.
- Key extraction.
- SQLCipher key attempts.
- Protected-store bypass.
- Opening `key_info`, login, MMKV, KVDB, or key-value stores.
- Opening protected DB schema after the safe SQLite route failed.
- Selecting message/contact/business rows from protected DB bundles.
- Running third-party WeChat export/decrypt tools on real data.

Reason: Sprint 2B-B already showed the copied main DB candidates are not plain SQLite-readable through the approved safe path. Continuing at raw-container level would move toward forbidden methods.

Boundary: no raw adapter implementation should begin unless the owner creates a new explicit safety/legal run contract that supersedes the current boundary.

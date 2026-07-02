# WDA Stage 2 Sprint 2C Readable Artifact Contract

Generated: 2026-07-03T09:12:39+10:00

Purpose: define the owner-authorized readable artifact intake contract for future WeChat message imports.

Sprint 2C is contract-only:
- It does not need the external hard drive.
- It does not produce `messages.jsonl`.
- It does not execute export, decryption, key extraction, database probing, or message parsing.
- It does not implement RAG, Web, or Matrix.

Current gate:
- Raw Gate remains `Conditional Investigation`.
- WDA remains blocked for message-level RAG/Web/Matrix until a real readable artifact exists and passes a later approved validation run.

Required artifact family for a future Sprint 2D sample:
- `import_manifest.json`
- `messages.jsonl`
- `conversations.jsonl`
- `contacts.jsonl`
- `media_index.csv` when media references are included

Next executable step: validate a small owner-authorized sample artifact only if the user provides or approves one.

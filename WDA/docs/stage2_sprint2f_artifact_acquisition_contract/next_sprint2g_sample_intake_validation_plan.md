# Next Sprint 2G Sample Intake Validation Plan

Generated: 2026-07-03T09:51:08+10:00

Sprint 2G is the only next executable step after Sprint 2F, and only if the user provides or approves a real owner-authorized readable artifact.

Sprint 2G goal:
- Validate a sample artifact package against the Sprint 2C and Sprint 2F contracts.

Sprint 2G inputs:
- Artifact under `/Users/linzezhang/Downloads/WDA_MetaData/stage2_inputs/owner_authorized_readable_artifacts/`.
- `import_manifest.json` or approval to create one locally.
- Optional readable files: `.jsonl`, `.json`, `.csv`, `.txt`, `.md`, `.html`, or `.zip` containing these.

Sprint 2G allowed operations:
- Read manifest and metadata.
- Verify checksums.
- Validate file types.
- Validate JSONL/CSV/JSON syntax and required fields.
- Count rows.
- Produce a validation report.

Sprint 2G forbidden operations:
- Decrypt, extract keys, or bypass protected stores.
- Open `key_info`, login, MMKV, KVDB, or key-value stores.
- Select message/contact/business rows from protected DB bundles.
- Parse protected DB content.
- Run third-party WeChat export/decrypt tools.
- Upload raw data.
- Implement RAG/Web/Matrix.

Sprint 2G output should not include raw private message text or contact values.

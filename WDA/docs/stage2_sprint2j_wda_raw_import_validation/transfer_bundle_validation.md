# Transfer Bundle Validation

## Bundle

- Expected path exists: false
- Validated path:
  `/Users/linzezhang/Downloads/WDA_MetaData/stage2_outputs/sprint2j_transfer_bundle/sprint2j_transfer_bundle.zip`
- Bundle size: `11792` bytes
- Bundle SHA-256:
  `10dbe9b40c13f5a8d09ded87c6f23fa340f4f4edbec8e25da6ff52d21ab76be4`

## Included Files

The bundle contains 14 files:

- 7 manifest files
- 1 full-sensitive minimal message-level JSONL artifact
- 6 Sprint 2I-B report/inventory files

## Sensitive Material Boundary

Confirmed absent from the zip listing:

- `sensitive_local_state/`
- key config files
- `key_info`
- login stores
- MMKV/key-value stores
- decrypted DBs
- `.db`, `.db-wal`, `.db-shm`
- full contact exports
- broad logs
- `tool_work/`
- full export outputs

Included by design:

- `raw_sensitive_minimal/minimal_export_limit1_raw.jsonl`

This raw minimal message-level artifact was authorized for local validation and
was not committed to git.


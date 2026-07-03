# Transfer Bundle Validation

## Bundle

- Expected path exists: false
- Validated path:
  `/Users/linzezhang/Downloads/WDA_MetaData/stage2_inputs/sprint2k_transfer_bundle/sprint2k_a_bounded_repeatability_export/sprint2k_transfer_bundle.zip`
- Bundle size: `108387` bytes
- Bundle SHA-256:
  `e97cf341fc5905372b2d76546a4270bb54b515d1f1b6850b2ab7815089123b56`
- Payload checksum manifest: `manifest/sprint2k_payload_checksums.sha256`
- Payload checksum status: pass

## Included Files

The bundle contains 18 files:

- 3 transfer manifest files
- 5 raw-sensitive bounded export JSONL files
- 10 Sprint 2K-A report or shape files

## Sensitive Material Boundary

Confirmed absent from the zip listing:

- `sensitive_local_state/`
- broad `logs/`
- `tool_work/`
- key config files
- `key_info`
- login stores
- MMKV/key-value stores
- decrypted DBs
- `.db`, `.db-wal`, `.db-shm`

Included by design:

- 5 bounded raw-sensitive message-level JSONL exports

These raw exports were authorized for local validation and were not committed to
git.


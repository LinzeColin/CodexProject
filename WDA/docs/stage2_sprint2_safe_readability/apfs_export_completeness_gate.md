# APFS Export Completeness Gate

Generated: 2026-07-03T07:50:11+10:00

## Decision

Completeness gate: **Pass for non-content Sprint 2 classification**.

This does not mean Raw Gate Go. It only means the authoritative APFS export is available and sufficiently verified for metadata/header-only classification.

## APFS Image and Mount

- Sparseimage: `/Volumes/My Passport/WDA_MetaData/raw_ferry/old_mac_wechat_full_export_20260702_apfs.sparseimage`
- Image format: APFS sparseimage; encrypted=false; total bytes 128849018880; non-empty bytes 48142221312.
- Mount: `/Volumes/WDA_WECHAT_APFS`
- Mount mode: read-only, from observed mount line.
- Export root: `/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702`
- Raw copy root: `/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702/raw/Data_Documents`

## Export Evidence

| Evidence | Result |
|---|---:|
| Segment plan rows | 1194 |
| Segment status rows | 1194 |
| Segment success rows | 1194 |
| Segment failed rows | 0 |
| Max attempts | 2 |
| Manifest lines | 115201 |
| Manifest file rows | 115200 |
| Dry-run verify exit code | 0 |
| Dry-run delete exit code | 0 |
| Dry-run delete item count | 0 |
| Dry-run transferred files | 0 |
| Dry-run transferred size | 0 B |
| Dry-run delete transferred files | 0 |
| Dry-run delete transferred size | 0 B |

## Residual Notes

Both dry-run logs show only two directory timestamp differences under `msg/file/` and `msg/video/`. They are directory metadata differences, not file-content gaps, because both dry-runs transferred 0 files and 0 bytes.

## Stop Line

If a future run cannot mount this sparseimage read-only or cannot verify the manifest/segment evidence, it must stop before any DB or raw import step.

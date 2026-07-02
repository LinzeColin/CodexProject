# Source Path Contract

Generated: 2026-07-03T07:50:11+10:00

## Roots

| Root label | Path | Status |
|---|---|---|
| Codex dev root | `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/WDA` | verified git root |
| Local metadata root | `/Users/linzezhang/Downloads/WDA_MetaData` | exists |
| External metadata root | `/Volumes/My Passport/WDA_MetaData` | exists |
| Authoritative APFS sparseimage | `/Volumes/My Passport/WDA_MetaData/raw_ferry/old_mac_wechat_full_export_20260702_apfs.sparseimage` | exists; imageinfo says encrypted=false |
| Expected APFS mount | `/Volumes/WDA_WECHAT_APFS` | mounted read-only |
| Export root | `/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702` | exists |
| Raw copy root | `/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702/raw/Data_Documents` | exists; read-only mounted export |
| Export metadata | `/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702/metadata` | exists |
| Export logs | `/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702/logs` | exists |

## Mount Evidence

`/dev/disk6s1 on /Volumes/WDA_WECHAT_APFS (apfs, local, nodev, nosuid, read-only, journaled, noowners, nobrowse, mounted by linzezhang)`

## Explicit Rejection

The abandoned direct ExFAT partial copy is not authoritative and was not used for classification:

`/Volumes/My Passport/WDA_MetaData/raw_ferry/old_mac_full_wechat_export_20260702/raw/Data_Documents`

## Safety Contract

No source data was modified. This Sprint 2 pass used manifest metadata plus small non-sensitive header signatures only. No decryption, key extraction, protected-store bypass, DB schema opening, message/contact row selection, or raw upload was performed.

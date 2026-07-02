# WDA Stage 2 Sprint 1D Completion Report

Generated: 2026-07-02 22:30 Australia/Sydney

## 1. Final Status

Stage 2 Sprint 1D is completed under the updated user scope.

Original Sprint 1D goal was a minimal read-only candidate DB bundle for transfer. During execution, the user changed the requirement to full export: "需要全部导出，需要完整的数据", with the persistent external destination renamed to:

`/Volumes/<真实盘名>/WDA_MetaData`

The real mounted disk used in this run was:

`/Volumes/My Passport`

Final authoritative export is not the earlier direct ExFAT partial copy. The authoritative export is the APFS sparseimage route:

- Sparseimage on external disk: `/Volumes/My Passport/WDA_MetaData/raw_ferry/old_mac_wechat_full_export_20260702_apfs.sparseimage`
- Mounted APFS volume: `/Volumes/WDA_WECHAT_APFS`
- Export bundle root: `/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702`
- Full raw copy: `/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702/raw/Data_Documents`
- Metadata: `/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702/metadata`
- Logs: `/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702/logs`

Safety constraints kept:

- Source directories were read only.
- No decrypt.
- No key extraction.
- No protected-store bypass.
- No DB schema opening.
- No message-content parsing.
- No third-party WeChat export/decrypt tool.
- No raw-data upload.
- No source-directory writes.

## 2. Final Verification Evidence

Segmented full export run:

- Run id: `20260702_213507`
- Source: `/Users/linzezhang/Library/Containers/com.tencent.xinWeChat/Data/Documents`
- Destination: `/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702/raw/Data_Documents`
- Export state: `segments_complete`
- Ended at: `2026-07-02T22:12:04+10:00`
- Segment plan rows: `1194`
- Segment success: `1194`
- Segment failed: `0`
- Max attempts needed by any segment: `2`

Latest full-tree read-only `rsync` dry-run:

- Summary: `/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702/metadata/rsync_dry_run_verify_20260702_222201.env`
- Log: `/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702/logs/rsync_dry_run_verify_20260702_222201.log`
- Exit code: `0`
- Number of files: `128096`
- Number of files transferred: `0`
- Total file size: `47148274678 B`
- Total transferred file size: `0 B`

Latest read-only `rsync --dry-run --delete` reconciliation:

- Summary: `/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702/metadata/rsync_dry_run_delete_verify_20260702_222414.env`
- Log: `/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702/logs/rsync_dry_run_delete_verify_20260702_222414.log`
- Exit code: `0`
- Delete item count: `0`
- Number of files transferred: `0`
- Total transferred file size: `0 B`

Destination file manifest:

- Manifest: `/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702/metadata/full_export_destination_file_manifest.csv`
- Manifest lines: `115201`
- Destination file rows: `115200`

Disk state at verification:

- APFS mounted volume: `/Volumes/WDA_WECHAT_APFS`
- APFS image capacity: `120Gi`
- APFS used: `45Gi`
- APFS available: `75Gi`
- External disk: `/Volumes/My Passport`
- External disk used: `893Gi`
- External disk available: `3.7Ti`

Important residual note:

The final dry-run still showed two directory-level timestamp differences:

- `xwechat_files/wxid_rtkga2i8r63812_7865/msg/file/`
- `xwechat_files/wxid_rtkga2i8r63812_7865/msg/video/`

These are directory metadata differences only. They are not file-content gaps. Both latest dry-runs reported `Number of files transferred: 0` and `Total transferred file size: 0 B`.

## 3. What Went Wrong Before the Final Route

### 3.1 Direct ExFAT Copy Was Unstable

The first full-export attempt copied directly into the ExFAT external disk path under:

`/Volumes/My Passport/WDA_MetaData/raw_ferry/old_mac_full_wechat_export_20260702/raw/Data_Documents`

That route repeatedly hit:

`Interrupted system call`

This happened across many small WeChat files. A later `rsync -aE` attempt was also not stable because macOS extended-attribute / AppleDouble handling on ExFAT added more fragile file operations.

Diagnosis:

- The failure pattern was not a single corrupt file.
- It appeared during broad traversal and many-small-file copy.
- ExFAT was a poor target filesystem for this workload.
- The direct ExFAT partial copy should not be treated as the authoritative export.

Action taken:

- The unstable process was interrupted.
- A diagnosis report was written.
- The external disk was synced and safely ejected.
- The user reconnected the disk and requested a better route balancing time, quality, performance, stability, and deliverable completeness.

### 3.2 Probe on APFS Still Saw Transient EINTR

After reconnect, the chosen route was to create and mount an APFS sparseimage stored on the ExFAT disk, then copy into the APFS volume.

Initial probe copied a representative WeChat attachment directory. The first batch returned rsync exit code `23` because a very small number of files saw `Interrupted system call`.

Diagnosis:

- A single failed file was retried immediately.
- The retry succeeded.
- This proved the remaining issue was transient source traversal / file-read instability, not an unreadable permanent file and not an APFS target failure.

Action taken:

- The script was patched so a probe warning would not block the full run.
- Full export switched to a segmented plan with retry.
- Each segment had a marker file for resume safety.
- The workflow avoided parsing raw data and did not open DB schemas.

### 3.3 Long-Running Optional Directory-Metadata Settle Was Interrupted

After the main export completed, a normal non-delete `rsync -a --stats` was attempted to settle directory mtimes.

Observation:

- It ran for several minutes with no material data movement.
- It was holding only directory-level metadata work.
- Prior dry-run evidence already showed no file data remained to transfer.

Action taken:

- The optional settle was interrupted.
- No raw data was deleted or modified.
- Final verification relied on fresh dry-run and dry-run-delete reconciliation instead.

### 3.4 `find` File Count Also Hit `Interrupted system call`

A later source-side `find` count hit:

`find: fts_read: Interrupted system call`

Diagnosis:

- This matched the earlier old-machine/source traversal instability.
- It was not used as final proof.

Action taken:

- Final proof used `rsync` full-tree dry-run and dry-run-delete reconciliation, because they completed with exit code `0` and provided transfer/delete counts.

## 4. Final Method That Worked

The stable route was:

1. Keep the physical external disk destination standard as `/Volumes/My Passport/WDA_MetaData`.
2. Store an APFS sparseimage inside that destination:
   `/Volumes/My Passport/WDA_MetaData/raw_ferry/old_mac_wechat_full_export_20260702_apfs.sparseimage`
3. Mount it as:
   `/Volumes/WDA_WECHAT_APFS`
4. Copy the WeChat `Data/Documents` tree into the mounted APFS volume.
5. Split the copy into 1194 segments, especially for large `msg/attach`, `msg/file`, and `msg/video` branches.
6. Retry failed segments once or more when transient `Interrupted system call` appears.
7. Record success markers and a central status CSV.
8. Verify with full-tree read-only `rsync --dry-run`.
9. Verify again with full-tree read-only `rsync --dry-run --delete`.
10. Generate a destination file manifest and control checksums.

This route avoided reformatting the external disk while also avoiding direct ExFAT handling of the full WeChat small-file tree.

## 5. Produced Artifacts

Workspace artifacts:

- `/Users/linzezhang/Documents/Codex/2026-07-01/users-linzezhang-library-containers-com-tencent/outputs/wda_apfs_full_export_20260702/run_apfs_segmented_export.sh`
- `/Users/linzezhang/Documents/Codex/2026-07-01/users-linzezhang-library-containers-com-tencent/outputs/wda_apfs_full_export_20260702/stage2_sprint1d_completion_report.md`

External APFS metadata artifacts:

- `/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702/metadata/segment_plan.tsv`
- `/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702/metadata/segment_copy_status.csv`
- `/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702/metadata/export_run_state.env`
- `/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702/metadata/full_export_destination_file_manifest.csv`
- `/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702/metadata/rsync_dry_run_verify_20260702_222201.env`
- `/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702/metadata/rsync_dry_run_delete_verify_20260702_222414.env`
- `/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702/metadata/control_checksums.sha256`
- `/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702/metadata/stage2_sprint1d_completion_report.md`

External destination contract:

- `/Volumes/My Passport/WDA_MetaData/AGENT_README_WDA_DESTINATION.md`

## 6. Non-Authoritative / Do Not Use as Final Export

The earlier direct ExFAT partial tree under this path is not authoritative:

`/Volumes/My Passport/WDA_MetaData/raw_ferry/old_mac_full_wechat_export_20260702/raw/Data_Documents`

Reason:

- It was created during the unstable direct-ExFAT route.
- It encountered repeated `Interrupted system call` failures.
- It was superseded by the APFS sparseimage export.

For all downstream agents, the authoritative full export is:

`/Volumes/My Passport/WDA_MetaData/raw_ferry/old_mac_wechat_full_export_20260702_apfs.sparseimage`

When mounted, use:

`/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702`

## 7. Recommended Next Step

Next pursuing goal should be Stage 2 Sprint 2 safe readability classification on the new computer, using the APFS sparseimage export as the raw evidence source.

Recommended constraints for Sprint 2:

- Mount APFS sparseimage read-only if possible.
- Do not decrypt.
- Do not extract keys.
- Do not bypass protected stores.
- Do not parse message content in the first readability probe.
- First classify DB/container readability, file signatures, WAL/SHM companions, and platform version risk.
- Use the manifest and segment status as the completeness gate before any deeper analysis.

Estimated remaining work:

- Sprint 1D delivery: complete.
- Optional cleanup of the abandoned direct ExFAT partial copy: one separate cleanup run, only after user approval.
- Sprint 2 safe readability classification: 1 focused run for probe design and non-content classification, then 1 run for results/report.


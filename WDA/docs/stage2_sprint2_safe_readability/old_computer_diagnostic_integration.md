# Old Computer Diagnostic Integration

Generated: 2026-07-03T07:50:11+10:00

The old computer Sprint 1D completion report has been copied into this Sprint 2 output set:

- `references/stage2_sprint1d_completion_report.md`
- SHA-256: `a602a19e0a76cab594d18b1aa3a506d545fc836179e87b999eca08471c2ee101`

## Preserved Diagnostic Facts

- Direct ExFAT full export was unstable and repeatedly hit `Interrupted system call`.
- Final authoritative export is APFS sparseimage stored on the external disk.
- Mounted APFS export path is `/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702`.
- Segmented export completed 1194/1194 segments successfully.
- Latest full-tree `rsync --dry-run` exited 0 and transferred 0 files / 0 bytes.
- Latest `rsync --dry-run --delete` exited 0 and delete count was 0.
- Destination manifest has 115200 file rows.
- Two remaining directory timestamp differences are not file-content gaps.
- The earlier direct ExFAT partial tree is not authoritative and was not used.

## Integration Decision

Sprint 2 uses the APFS sparseimage route as the only authoritative old-computer export source. Old-computer workspace paths are treated as historical evidence only and are not assumed to exist on the new computer.

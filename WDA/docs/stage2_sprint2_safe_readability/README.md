# WDA Stage 2 Sprint 2 Safe Readability

Generated: 2026-07-03T07:50:11+10:00

## Purpose

This output set performs the first Sprint 2 safe readability classification on the new computer using the old computer authoritative APFS sparseimage full export.

## Source Decision

- Authoritative source: `/Volumes/My Passport/WDA_MetaData/raw_ferry/old_mac_wechat_full_export_20260702_apfs.sparseimage`
- Mounted read-only at: `/Volumes/WDA_WECHAT_APFS`
- Export root: `/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702`
- Raw copy root: `/Volumes/WDA_WECHAT_APFS/old_mac_full_wechat_export_20260702/raw/Data_Documents`
- Non-authoritative ExFAT partial copy: explicitly rejected and not used.

## Outputs

- `source_path_contract.md`
- `old_computer_diagnostic_integration.md`
- `apfs_export_completeness_gate.md`
- `db_container_readability_classification.csv`
- `wal_shm_companion_map.csv`
- `sensitive_skip_list.csv`
- `candidate_domain_summary.csv`
- `safe_readability_decision.md`
- `next_sprint2b_or_raw_import_plan.md`
- `sprint2_validation_report.md`
- `references/stage2_sprint1d_completion_report.md`

## Gate Status

- APFS export completeness gate: pass for non-content classification.
- Safe readability: container/header classification only.
- Message readability: not proven.
- Raw Gate: Conditional Investigation; not Go.

## Safety

No source data was modified. No raw data was committed. No decryption, key extraction, protected-store bypass, DB schema opening, message/contact row selection, message parsing, or raw upload was performed.

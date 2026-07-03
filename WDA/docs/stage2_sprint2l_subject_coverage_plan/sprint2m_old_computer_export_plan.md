# Sprint 2M Old-Computer Export Plan

## Host Decision

Sprint 2M should run on the old computer.

Reason: the old computer is the live WeChat data source and has the proven
export route. The new computer remains the WDA Control Plane and validation
host.

## Command Boundary

Use the already proven local exporter route only. Do not introduce a new exporter
family in Sprint 2M.

Commands must be bounded to:

- session/contact lookup for the five subject seeds
- selected conversation export only
- `limit <= 100` per selected conversation
- total rows `<= 500`
- `include_media_paths=false`
- output root under WDA_MetaData

## Suggested Run Sequence

1. Verify readiness: local tool reports ready and live read OK.
2. Generate a subject lookup report using the five subject seeds.
3. Select at most five conversation targets.
4. Export each selected conversation with `limit=100` and
   `include_media_paths=false`.
5. Stop when total exported rows reach `500`.
6. Generate non-sensitive shape reports:
   - selected subject matrix
   - row counts
   - field names/types
   - conversion precheck
   - excluded sources
7. Package bounded raw exports for new-computer validation.

## Required 2M Output Bundle Shape

The transfer bundle should contain:

- `manifest/sprint2m_payload_checksums.sha256`
- `manifest/sprint2m_transfer_manifest.csv`
- `manifest/sprint2m_transfer_bundle_readme.md`
- `raw_sensitive_subject_exports/*.jsonl`
- `reports/subject_selection_report.md`
- `reports/row_count_summary.csv`
- `reports/bounded_export_shape_report.md`
- `reports/privacy_safety_report.md`
- `reports/sprint2m_a_decision.md`
- `reports/next_sprint2m_b_transfer_and_validation_plan.md`

Do not include keys, configs, DBs, broad logs, `tool_work/`,
`sensitive_local_state/`, full contact exports, media files, or all-history
exports.


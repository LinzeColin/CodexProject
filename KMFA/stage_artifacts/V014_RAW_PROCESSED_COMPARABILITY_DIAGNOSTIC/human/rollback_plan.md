# Rollback Plan

- Remove `KMFA/stage_artifacts/V014_RAW_PROCESSED_COMPARABILITY_DIAGNOSTIC/`.
- Remove metadata copies under `KMFA/metadata/quality/v014_raw_processed_comparability_diagnostic_*`.
- Remove ignored private runtime diagnostic under `KMFA/.codex_private_runtime/v014_raw_processed_comparability_diagnostic/`.
- Revert governance and status entries for this phase.
- Do not modify the raw data inbox.

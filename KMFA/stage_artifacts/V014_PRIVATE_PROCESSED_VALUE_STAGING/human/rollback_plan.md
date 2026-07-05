# Rollback Plan

- Remove `KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_STAGING/`.
- Remove `KMFA/metadata/quality/v014_private_processed_value_staging_*`.
- Remove `KMFA/tools/v014_private_processed_value_staging.py` and validator/test files.
- Remove ignored private runtime staging under `KMFA/.codex_private_runtime/v014_private_processed_value_staging/`.
- Do not modify raw inbox.

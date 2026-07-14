# Rollback Plan

- Revert the S06-P3 commit.
- Remove `KMFA/stage_artifacts/V014_S06_P3_VALIDATION_EVIDENCE/` if the phase is abandoned before commit.
- Remove the S06-P3 records appended to `KMFA/metadata/quality` only by reverting the same commit.
- Keep the operator-designated local raw/private inbox untouched.

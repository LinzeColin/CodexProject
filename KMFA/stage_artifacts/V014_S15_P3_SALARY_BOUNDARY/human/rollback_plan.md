# KMFA v0.1.4 S15-P3 Rollback Plan

- Revert the local S15-P3 commit if validation fails before any later stage review.
- Remove only `KMFA/stage_artifacts/V014_S15_P3_SALARY_BOUNDARY/` and v0.1.4 S15-P3 governance references if this phase is discarded.
- Do not modify the operator-designated raw/private inbox during rollback.

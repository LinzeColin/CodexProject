# KMFA v0.1.4 Stage 13 Review Rollback Plan

- Remove `KMFA/stage_artifacts/V014_S13_STAGE_REVIEW/` if review evidence is invalid.
- Revert `KMFA/tools/v014_s13_stage_review.py`, `KMFA/tools/check_v014_s13_stage_review.py` and `KMFA/tests/test_v014_s13_stage_review.py` if review validation is invalid.
- Restore governance/status files to the prior S13-P3 handoff state if review validation fails.

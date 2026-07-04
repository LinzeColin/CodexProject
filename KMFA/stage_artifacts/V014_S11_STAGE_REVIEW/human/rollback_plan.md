# KMFA v0.1.4 Stage 11 Review Rollback Plan

- Remove `KMFA/stage_artifacts/V014_S11_STAGE_REVIEW/` if review evidence is invalid.
- Revert `KMFA/tools/v014_s11_stage_review.py`, `KMFA/tools/check_v014_s11_stage_review.py` and `KMFA/tests/test_v014_s11_stage_review.py` if review validation is invalid.
- Revert the narrow `reviewed_head` policy change in `KMFA/tools/check_v014_s11_p3_project_cost_page.py` if a stricter phase evidence policy is later adopted.
- Restore governance/status files to the prior S11-P3 handoff state if review validation fails.

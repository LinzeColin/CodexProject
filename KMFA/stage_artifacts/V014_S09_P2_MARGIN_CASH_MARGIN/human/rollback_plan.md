# KMFA v0.1.4 S09-P2 Rollback Plan

- task_id: `KMFA-V014-S09-P2-MARGIN-CASH-MARGIN-20260704`
- rollback_scope: `V014_S09_P2_MARGIN_CASH_MARGIN artifacts, validator, unit test and governance rows only`
- raw_data_action: `none`
- github_action: `none; no push was performed by this phase`

## Steps

1. Revert `KMFA/stage_artifacts/V014_S09_P2_MARGIN_CASH_MARGIN/`.
2. Revert `KMFA/tools/v014_s09_p2_margin_cash_margin.py` and `KMFA/tools/check_v014_s09_p2_margin_cash_margin.py`.
3. Revert `KMFA/tests/test_v014_s09_p2_margin_cash_margin.py`.
4. Revert S09-P2 rows in KMFA governance, traceability, model parameter and project record files.
5. Re-run S09-P1 validator to confirm the next allowed phase returns to S09-P2.

Rollback must not read, list, copy, move, rename, delete, overwrite, write or mutate the operator-designated raw/private finance inbox.

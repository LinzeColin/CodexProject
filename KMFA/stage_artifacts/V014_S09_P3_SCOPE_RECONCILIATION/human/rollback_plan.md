# KMFA v0.1.4 S09-P3 Rollback Plan

- task_id: `KMFA-V014-S09-P3-SCOPE-RECONCILIATION-20260704`
- Remove `KMFA/stage_artifacts/V014_S09_P3_SCOPE_RECONCILIATION/`.
- Remove `KMFA/tools/v014_s09_p3_scope_reconciliation.py` and `KMFA/tools/check_v014_s09_p3_scope_reconciliation.py`.
- Remove `KMFA/tests/test_v014_s09_p3_scope_reconciliation.py`.
- Revert S09-P3 entries in KMFA governance records and three Chinese project records.
- Re-run S09-P2 validator and governance sync to confirm the tree returns to the S09-P2 stop point.

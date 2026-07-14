# v0.1.4 S12-P3 Rollback Plan

1. Remove `KMFA/stage_artifacts/V014_S12_P3_MANUAL_RERUN_MECHANISM/`.
2. Revert `KMFA/tools/v014_s12_p3_manual_rerun_mechanism.py`, `KMFA/tools/check_v014_s12_p3_manual_rerun_mechanism.py`, and the focused test.
3. Revert S12-P3 governance/status updates.
4. Re-run S12-P2 validator to confirm the previous boundary remains intact.

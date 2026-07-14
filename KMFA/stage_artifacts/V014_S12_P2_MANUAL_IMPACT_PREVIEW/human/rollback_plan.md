# v0.1.4 S12-P2 Rollback Plan

1. Remove `KMFA/stage_artifacts/V014_S12_P2_MANUAL_IMPACT_PREVIEW/`.
2. Revert `KMFA/tools/v014_s12_p2_manual_impact_preview.py`, `KMFA/tools/check_v014_s12_p2_manual_impact_preview.py`, and focused test changes.
3. Revert S12-P2 governance/status updates.
4. Re-run S12-P1 validator to confirm the previous boundary remains intact.

# KMFA v0.1.4 S10-P1 Rollback Plan

1. Remove `KMFA/stage_artifacts/V014_S10_P1_REPORT_TEMPLATES/`.
2. Revert governance rows for `KMFA-V014-S10-P1-REPORT-TEMPLATES-20260704`.
3. Re-run Stage 9 review validator to confirm the previous gate still points to S10-P1.
4. Do not modify, move, rename, delete, overwrite, or write files inside the operator-designated raw/private inbox during rollback.

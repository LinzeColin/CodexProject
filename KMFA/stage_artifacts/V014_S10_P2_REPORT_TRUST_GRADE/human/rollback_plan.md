# KMFA v0.1.4 S10-P2 Rollback Plan

1. Revert `KMFA/tools/v014_s10_p2_report_trust_grade.py`.
2. Revert `KMFA/tools/check_v014_s10_p2_report_trust_grade.py`.
3. Revert `KMFA/tests/test_v014_s10_p2_report_trust_grade.py`.
4. Remove `KMFA/stage_artifacts/V014_S10_P2_REPORT_TRUST_GRADE/`.
5. Revert governance and Chinese entry rows for `KMFA-V014-S10-P2-REPORT-TRUST-GRADE-20260704`.
6. Re-run S10-P1 validator to confirm the prior phase remains intact.

- rollback_target: `7913a85c3f18611cb21373dd059b8d9a99dfc647`
- raw/private data directory must not be modified during rollback.

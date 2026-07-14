# KMFA v0.1.4 S16-P3 Rollback Plan

Rollback is limited to public-safe S16-P3 evidence, validator, focused test, and governance rows.

1. Revert `KMFA/stage_artifacts/V014_S16_P3_CUSTOMER_BUSINESS_ANALYSIS/`.
2. Revert `KMFA/tools/v014_s16_p3_customer_business_analysis.py`.
3. Revert `KMFA/tools/check_v014_s16_p3_customer_business_analysis.py`.
4. Revert `KMFA/tests/test_v014_s16_p3_customer_business_analysis.py`.
5. Revert S16-P3 governance/status/model/traceability rows added in this phase.
6. Leave the raw/private inbox untouched; ignored private diagnostics may be deleted locally if needed.

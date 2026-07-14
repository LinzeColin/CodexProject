# KMFA v0.1.4 S08-P2 Rollback Plan

Rollback is limited to public-safe S08-P2 evidence, validator, focused test, and governance rows.

1. Revert `KMFA/stage_artifacts/V014_S08_P2_BUSINESS_ENTITY_MODEL/`.
2. Revert `KMFA/tools/v014_s08_p2_business_entity_model.py`.
3. Revert `KMFA/tools/check_v014_s08_p2_business_entity_model.py`.
4. Revert `KMFA/tests/test_v014_s08_p2_business_entity_model.py`.
5. Revert S08-P2 governance/status/model/traceability rows added in this phase.
6. Do not modify, move, delete, hash, or copy the raw/private inbox as part of rollback.

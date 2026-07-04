# KMFA v0.1.4 S08-P3 Rollback Plan

Rollback is limited to public-safe S08-P3 evidence, validator, focused test, and governance rows.

1. Revert `KMFA/stage_artifacts/V014_S08_P3_ENTITY_MATCHING_QUALITY/`.
2. Revert `KMFA/tools/v014_s08_p3_entity_matching_quality.py`.
3. Revert `KMFA/tools/check_v014_s08_p3_entity_matching_quality.py`.
4. Revert `KMFA/tests/test_v014_s08_p3_entity_matching_quality.py`.
5. Revert S08-P3 governance/status/model/traceability rows added in this phase.
6. Do not modify, move, delete, hash, or copy the raw/private inbox as part of rollback.

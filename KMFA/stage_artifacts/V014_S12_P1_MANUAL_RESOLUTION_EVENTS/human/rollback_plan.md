# v0.1.4 S12-P1 Rollback Plan

1. Revert the local commit for this phase if validation fails after commit.
2. Remove `KMFA/stage_artifacts/V014_S12_P1_MANUAL_RESOLUTION_EVENTS/` if evidence must be regenerated.
3. Re-run legacy S12-P1 validator and v0.1.4 Stage 11 review validator before regenerating.
4. Do not edit raw/private source files or approved legacy event rows in place.

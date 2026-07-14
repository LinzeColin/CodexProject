# Rollback Plan

1. Revert the local commit that adds `V014_RAW_SOURCE_IDENTITY_DECISION_APPLICATION` evidence.
2. Remove metadata copies for this phase under `KMFA/metadata/quality/` and `KMFA/metadata/approvals/`.
3. Keep the prior owner decision intake NO_GO state active.
4. Do not modify the private source inbox during rollback.

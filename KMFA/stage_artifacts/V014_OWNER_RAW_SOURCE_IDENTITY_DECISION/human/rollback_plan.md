# Rollback Plan

1. Revert the local commit that adds `V014_OWNER_RAW_SOURCE_IDENTITY_DECISION` evidence.
2. Remove metadata copies under `KMFA/metadata/quality/` and `KMFA/metadata/approvals/` for this phase.
3. Keep the prior `V014_RAW_ALIGNMENT_REMEDIATION` NO_GO state active.
4. Do not modify the raw inbox during rollback.

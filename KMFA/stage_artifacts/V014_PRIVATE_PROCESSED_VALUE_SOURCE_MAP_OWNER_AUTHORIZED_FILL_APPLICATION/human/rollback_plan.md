# Rollback Plan

1. Revert the local commit that adds this owner-authorized fill application phase.
2. Remove metadata copies for this phase under `KMFA/metadata/quality/` and `KMFA/metadata/approvals/`.
3. Keep the prior owner-authorized fill intake NO_GO state active.
4. Do not modify the raw source inbox during rollback.

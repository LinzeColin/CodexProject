# KMFA v0.1.4 Stage 9 Review Rollback Plan

1. Revert the local commit that introduced `V014_S09_STAGE_REVIEW` evidence, validator, focused unit test and governance rows.
2. Restore current phase to `S09-P3 completed / Stage 9 review pending` if review evidence is invalidated.
3. Do not modify, delete, move, rename, overwrite or write the raw inbox during rollback.

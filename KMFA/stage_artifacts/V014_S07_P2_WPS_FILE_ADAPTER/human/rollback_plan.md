# KMFA v0.1.4 S07-P2 Rollback Plan

1. Revert the local commit containing `V014_S07_P2_WPS_FILE_ADAPTER` artifacts and v014 WPS metadata rows.
2. Restore the active next phase to `S07-P2` if the validator is invalidated.
3. Do not modify, delete, move, rename, overwrite or write the raw inbox during rollback.

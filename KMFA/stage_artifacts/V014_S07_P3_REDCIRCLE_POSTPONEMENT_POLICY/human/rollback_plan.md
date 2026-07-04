# KMFA v0.1.4 S07-P3 Rollback Plan

1. Revert the local commit containing `V014_S07_P3_REDCIRCLE_POSTPONEMENT_POLICY` artifacts and v014 Redcircle metadata rows.
2. Re-run S07-P1 and S07-P2 validators to confirm dependency evidence is unchanged.
3. Re-run S07-P3 after the reserved template contract or connector postponement policy is corrected.

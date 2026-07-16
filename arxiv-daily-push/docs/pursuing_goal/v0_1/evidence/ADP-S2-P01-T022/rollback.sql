-- ADP-S2-P01-T022 rollback: drop the artifact ledger (SHADOW feature; safe -- no publish-chain dependency)
DROP TABLE IF EXISTS cn_artifacts;
-- (R2 objects, if any, are immutable content-addressed; delete the bucket's raw/ prefix out-of-band if fully rolling back)

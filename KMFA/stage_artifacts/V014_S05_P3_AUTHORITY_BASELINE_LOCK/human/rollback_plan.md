# KMFA v0.1.4 S05-P3 Rollback Plan

- Remove only v0.1.4 S05-P3 files introduced in this phase if validation fails before commit.
- Keep S05-P1/S05-P2 public-safe evidence unchanged.
- Do not touch `/Users/linzezhang/Downloads/KMFA_MetaData` during rollback.
- Re-run S05-P2 and S05-P3 validators after rollback.

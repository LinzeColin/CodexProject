# KMFA v1.4 S01-P1 Rollback Plan

Rollback is limited to public-safe phase evidence and governance records.

## Revert Scope

- Remove `KMFA/stage_artifacts/V014_S01_P1_READ_ONLY_SCOPE_LOCK/`.
- Remove `KMFA/tools/check_v014_s01_p1_read_only_scope_lock.py`.
- Remove `KMFA/tests/test_v014_s01_p1_read_only_scope_lock.py`.
- Revert S01-P1 governance/status rows added for `KMFA-V014-S01-P1-READ-ONLY-SCOPE-LOCK-20260703`.

## Protected Scope

- Do not touch `/Users/linzezhang/Downloads/KMFA_MetaData`.
- Do not remove or rewrite v0.1.3 upload evidence.
- Do not alter raw/private local files.

## Trigger

Rollback if validation detects raw/private file leakage, committed raw filenames, incorrect canonical path routing, or accidental S01-P2 implementation in this phase.

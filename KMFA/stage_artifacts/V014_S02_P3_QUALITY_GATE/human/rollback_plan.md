# v0.1.4 S02-P3 Rollback Plan

Rollback scope is limited to public-safe protocol artifacts from this phase:

- Remove `KMFA/metadata/protocol/quality_gate_lock_v1_4.json`.
- Remove `KMFA/stage_artifacts/V014_S02_P3_QUALITY_GATE/`.
- Remove `KMFA/tools/check_v014_s02_p3_quality_gate.py`.
- Remove `KMFA/tests/test_v014_s02_p3_quality_gate.py`.
- Revert S02-P3 governance rows in KMFA Chinese entries and `KMFA/docs/governance/`.

Rollback must not touch `/Users/linzezhang/Downloads/KMFA_MetaData` or any raw/private file.

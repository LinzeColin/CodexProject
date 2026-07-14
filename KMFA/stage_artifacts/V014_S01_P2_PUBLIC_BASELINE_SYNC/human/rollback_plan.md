# KMFA v0.1.4 S01-P2 Rollback Plan

To roll back S01-P2, revert the local commit containing `KMFA-V014-S01-P2-PUBLIC-BASELINE-SYNC-20260703`.

If manual rollback is required before commit, remove only these public-safe outputs:

- `KMFA/taskpack/v1_4/`
- `KMFA/metadata/baseline/source_package_v1_4.json`
- `KMFA/stage_artifacts/V014_S01_P2_PUBLIC_BASELINE_SYNC/`
- `KMFA/tools/check_v014_s01_p2_public_baseline_sync.py`
- `KMFA/tests/test_v014_s01_p2_public_baseline_sync.py`
- S01-P2 governance/status rows appended in this phase.

Do not modify `/Users/linzezhang/Downloads/KMFA_MetaData` during rollback.

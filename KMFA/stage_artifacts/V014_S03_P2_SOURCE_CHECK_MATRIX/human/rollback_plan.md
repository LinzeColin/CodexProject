# KMFA v0.1.4 S03-P2 Rollback Plan

Rollback scope:

- Remove `KMFA/tools/v014_s03_p2_source_check_matrix.py`.
- Remove `KMFA/tools/check_v014_s03_p2_source_check_matrix.py`.
- Remove `KMFA/tests/test_v014_s03_p2_source_check_matrix.py`.
- Remove `KMFA/metadata/sources/v014_s03_p2_source_check_matrix.jsonl`.
- Remove `KMFA/metadata/sources/v014_s03_p2_source_status_events.jsonl`.
- Remove `KMFA/metadata/protocol/source_check_matrix_v1_4_s03_p2.json`.
- Remove `KMFA/stage_artifacts/V014_S03_P2_SOURCE_CHECK_MATRIX/`.
- Revert S03-P2 governance rows and status updates.

Raw data rollback: no action. S03-P2 must not modify raw data.

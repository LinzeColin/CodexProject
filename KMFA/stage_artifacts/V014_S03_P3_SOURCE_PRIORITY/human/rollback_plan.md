# KMFA v0.1.4 S03-P3 Rollback Plan

Rollback scope:

- Remove `KMFA/tools/v014_s03_p3_source_priority.py`.
- Remove `KMFA/tools/check_v014_s03_p3_source_priority.py`.
- Remove `KMFA/tests/test_v014_s03_p3_source_priority.py`.
- Remove `KMFA/metadata/sources/v014_s03_p3_source_priority_records.jsonl`.
- Remove `KMFA/metadata/sources/v014_s03_p3_same_source_rerun_events.jsonl`.
- Remove `KMFA/metadata/quality/v014_s03_p3_cross_source_difference_queue.jsonl`.
- Remove `KMFA/metadata/protocol/source_priority_v1_4_s03_p3.json`.
- Remove `KMFA/stage_artifacts/V014_S03_P3_SOURCE_PRIORITY/`.
- Revert S03-P3 governance rows and status updates.

Raw data rollback: no action. S03-P3 must not modify raw data.

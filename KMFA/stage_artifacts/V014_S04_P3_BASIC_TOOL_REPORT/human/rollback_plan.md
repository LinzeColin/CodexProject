# KMFA v0.1.4 S04-P3 Rollback Plan

- revert_files: `KMFA/tools/v014_s04_p3_basic_tool_report.py`, `KMFA/tools/check_v014_s04_p3_basic_tool_report.py`, `KMFA/tests/test_v014_s04_p3_basic_tool_report.py`, `KMFA/stage_artifacts/V014_S04_P3_BASIC_TOOL_REPORT/`, and S04-P3 governance rows.
- raw_data_action: `none`; `/Users/linzezhang/Downloads/KMFA_MetaData` was not read, listed, hashed, modified, deleted, moved, renamed, overwritten, or written by this phase.
- verification_after_rollback: rerun `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s04_p2_field_standardization.py` and governance validators.
- stop_condition: any raw/private payload, business value, credential, raw filename/hash, raw source header plaintext, or GitHub upload side effect requires immediate rollback and report.

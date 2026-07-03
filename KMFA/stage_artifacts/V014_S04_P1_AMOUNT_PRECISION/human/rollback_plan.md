# KMFA v0.1.4 S04-P1 Rollback Plan

- revert_files: `KMFA/tools/v014_s04_p1_amount_precision.py`, `KMFA/tools/check_v014_s04_p1_amount_precision.py`, `KMFA/tests/test_v014_s04_p1_amount_precision.py`, `KMFA/stage_artifacts/V014_S04_P1_AMOUNT_PRECISION/`, and S04-P1 governance rows.
- raw_data_action: `none`; `/Users/linzezhang/Downloads/KMFA_MetaData` was not read, listed, hashed, modified, deleted, moved, renamed, overwritten, or written by this phase.
- verification_after_rollback: rerun `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s03_stage_review.py` and governance validators.
- stop_condition: any raw/private payload, business value, credential, or GitHub upload side effect requires immediate rollback and report.

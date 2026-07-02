# KMFA v0.1.3 S06-P2 Difference Queue Replay Test Results

- task_id: `KMFA-V013-S06-P2-DIFFERENCE-QUEUE-REPLAY-20260703`
- status: `PASS`
- github_upload_performed: `false`
- raw_dir_read_performed: `false`
- raw_dir_mutation_performed: `false`
- metadata_quality_written: `false`
- stage6_review_performed: `false`

## Command Results

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s06_p2_difference_queue_replay.py` - PASS: queue_items=1, difference_cents=1, report_grade_a_allowed=false, github_upload=false.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s06_p2_difference_queue_replay.py` - PASS: metadata_quality_written=false, github_upload=false.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s06_p2_difference_queue_replay -q` - PASS: 3 tests.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s06_p1_zero_delta_replay.py` - PASS: S06-P1 dependency validated.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s06_p2_difference_queue.py --queue-jsonl KMFA/stage_artifacts/V013_S06_P2_DIFFERENCE_QUEUE_REPLAY/machine/source_difference_queue.jsonl --gate-json KMFA/stage_artifacts/V013_S06_P2_DIFFERENCE_QUEUE_REPLAY/machine/report_grade_gate.json` - PASS: queue_items=1, report_grade_a_allowed=false.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_cross_source_difference_queue -q` - PASS: 6 tests.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s KMFA/tests -q` - PASS: 304 tests.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py` - PASS.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py` - PASS.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA` - PASS.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA` - PASS.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync` - PASS.
- Parameter registry shape, structured JSON/JSONL/CSV parse, structured YAML parse, raw/private artifact path scan, S06-P2 public-safe evidence scan, high-signal secret scan, and `git diff --check -- KMFA scripts` - PASS.

## Scope Confirmation

- S06-P3 validation evidence output: `not_performed`
- Stage 6 review: `not_performed`
- GitHub upload: `not_performed`
- Raw inbox read/list/mutation: `not_performed`
- Metadata/quality runtime write: `not_performed`
- Source difference queue metadata write: `not_performed`
- Raw value matching/formal report/business execution: `not_performed`

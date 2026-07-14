# KMFA v0.1.3 S06-P3 Validation Evidence Replay Test Results

- task_id: `KMFA-V013-S06-P3-VALIDATION-EVIDENCE-REPLAY-20260703`
- status: `passed_local_only_upload_deferred_no_go`
- github_upload_performed: `false`
- raw_dir_read_performed: `false`
- raw_dir_mutation_performed: `false`
- stage6_review_performed: `false`

## Commands

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s06_p3_validation_evidence_replay.py`
  - PASS: metadata quality written, project statuses=2, Q5 allowed=0, Stage 6 review=false, GitHub upload=false.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s06_p3_validation_evidence_replay -q`
  - PASS: 3 tests.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s06_p1_zero_delta_replay.py`
  - PASS: S06-P1 dependency validated.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s06_p2_difference_queue_replay.py`
  - PASS: S06-P2 dependency validated.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s06_p3_validation_evidence.py`
  - PASS: legacy S06-P3 validation evidence check.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_validation_evidence_output -q`
  - PASS: 4 tests.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s KMFA/tests -q`
  - PASS: 307 tests.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
  - PASS.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`
  - PASS.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
  - PASS.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
  - PASS.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
  - PASS.
- parameter registry shape check
  - PASS: 34 columns, 487 rows.
- structured YAML parse check
  - PASS.
- structured JSON/JSONL/CSV parse check
  - PASS.
- changed/untracked raw/private artifact path scan
  - PASS.
- S06-P3 public-safe evidence scan
  - PASS.
- changed-file high-signal secret scan
  - PASS.
- `git diff --check -- KMFA scripts`
  - PASS.

## Boundary Confirmation

- This run did not read, list, modify, delete, move, rename, overwrite, or write generated files inside `/Users/linzezhang/Downloads/KMFA_MetaData`.
- This run did not execute Stage 6 review, GitHub upload, raw value matching, lineage full check, formal report release, live connector, or business execution.

# KMFA v0.1.3 S06-P1 Zero-Delta Replay Test Results

- task_id: `KMFA-V013-S06-P1-ZERO-DELTA-REPLAY-20260703`
- status: `PASS`
- github_upload_performed: `false`
- raw_dir_read_performed: `false`
- raw_dir_mutation_performed: `false`

## Command Results

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s06_p1_zero_delta_replay.py` - PASS: comparisons=8, pass_mismatches=0, one_cent_detected=true, github_upload=false.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s06_p1_zero_delta_replay.py` - PASS: metadata_quality_written=false, github_upload=false.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s06_p1_zero_delta_replay -q` - PASS: 1 test.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s05_stage_review.py` - PASS: S05 dependency validated.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_zero_delta_validator -q` - PASS: 6 tests.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/zero_delta_validator.py --fixture KMFA/metadata/fixtures/a0_project_cost_fixture.json` - PASS: mismatch_count=0.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s KMFA/tests -q` - PASS: 301 tests.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py` - PASS.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py` - PASS.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA` - PASS.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA` - PASS.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync` - PASS.
- Structured changed-file parse, parameter registry shape, raw/private artifact path scan, S06-P1 public-safe evidence scan, high-signal secret scan, and `git diff --check -- KMFA scripts` - PASS.

## Scope Confirmation

- S06-P2 difference queue: `not_performed`
- S06-P3 validation evidence output: `not_performed`
- Stage 6 review: `not_performed`
- GitHub upload: `not_performed`
- Raw inbox read/list/mutation: `not_performed`

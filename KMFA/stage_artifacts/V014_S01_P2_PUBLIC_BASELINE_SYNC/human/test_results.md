# KMFA v0.1.4 S01-P2 Test Results

- task_id: `KMFA-V014-S01-P2-PUBLIC-BASELINE-SYNC-20260703`
- status: `completed_validated_local_only_no_go_upload_deferred`
- raw_inbox_read_by_this_phase: `false`
- raw_inbox_listed_by_this_phase: `false`
- raw_inbox_mutation_performed: `false`
- github_upload_performed: `false`
- stage_review_performed: `false`
- s01_p3_started: `false`

## Command Results

- PASS: `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/check_v014_s01_p2_public_baseline_sync.py KMFA/tests/test_v014_s01_p2_public_baseline_sync.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s01_p1_read_only_scope_lock.py --require-source-package-present`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s01_p2_public_baseline_sync.py --require-source-package-present`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s01_p2_public_baseline_sync -q`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- PASS: structured JSON, JSONL, CSV and YAML parse checks passed for changed/untracked KMFA files; YAML was parsed with Ruby Psych because PyYAML is not installed in the system Python.
- PASS: changed/untracked raw-private path scan passed.
- PASS: strict key-shaped secret scan passed.
- PASS: `git diff --check -- KMFA`
- PASS: Raw inbox was not read, listed, modified, deleted, moved, renamed, overwritten or written by this phase.
- PASS: S01-P3, Stage 1 review, GitHub upload, raw value matching, lineage full check, formal report, live connector, OpMe deep coupling and business execution were not performed.

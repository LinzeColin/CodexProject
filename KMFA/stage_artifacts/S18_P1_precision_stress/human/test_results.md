# KMFA S18-P1 Precision Stress Test Results

generated_at: 2026-07-01T23:59:59+10:00

## TDD Red Evidence

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_precision_stress_validation.py
ModuleNotFoundError: No module named 'KMFA.tools.precision_stress_validation'
```

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_precision_stress_validation.py
FAIL: test_cli_validator_accepts_generated_public_safe_artifacts
can't open file '.../KMFA/tools/check_s18_p1_precision_stress.py': [Errno 2] No such file or directory
```

## Green Evidence

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_precision_stress_validation.py` | PASS: 7 tests |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/precision_stress_validation.py --check-only --generated-at 2026-07-01T23:59:59+10:00` | PASS: scenarios=5, runs=3, large_batch_files=1200, elapsed_ms=348, errors=2, s18_p2=false, s18_p3=false, github_upload=false |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/precision_stress_validation.py --generated-at 2026-07-01T23:59:59+10:00` | PASS: generated S18-P1 precision stress artifacts |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s18_p1_precision_stress.py` | PASS: scenarios=5, runs=3, large_batch_files=1200, elapsed_ms=348, errors=2, s18_p2=false, s18_p3=false, github_upload=false |

## Boundary Result

- `raw_business_data=false`
- `public_safe_synthetic_only=true`
- `three_consecutive_imports_consistent=true`
- `large_batch_performance_within_budget=true`
- `s18_p2=false`
- `s18_p3=false`
- `stage18_review=false`
- `github_upload=false`

## Final Gate Evidence

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_precision_stress_validation.py` | PASS: 7 tests |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s18_p1_precision_stress.py` | PASS: scenarios=5, runs=3, large_batch_files=1200, elapsed_ms=348, errors=2, s18_p2=false, s18_p3=false, github_upload=false |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s KMFA/tests -q` | PASS: 253 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=526, tasks=162, v1.2_html=45+ |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py` | PASS: html=45, core=7 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors=0 warnings=0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors=0 warnings=0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_governance_sync.py --changed-only --enforce-sync` | PASS: errors=0 warnings=0 after adding required governance sync files and event file coverage |
| `json/jsonl/csv parse check` | PASS: json=153, jsonl=103, csv=26 |
| `ruby YAML parse check` | PASS: yaml=30 |
| `TRACEABILITY_MATRIX.csv field count check` | PASS |
| `parameter_registry.csv field count check` | PASS |
| `raw/private path scan` | PASS |
| `NUL-separated high-signal secret scan` | PASS |
| `git diff --check -- KMFA scripts` | PASS |

## Review Findings Fixed

- `validate_governance_sync.py --changed-only --enforce-sync` initially reported missing governance sync files: `OWNER_STATUS.md`, `TRACEABILITY_MATRIX.csv`, and `delivery_tasks.yaml`. These were updated with S18-P1 public-safe local validation status and S18-P2 next gate.
- `development_events.jsonl` initially did not list `KMFA/metadata/model_registry.yaml` in S18-P1 `files_changed`; the event file list was expanded to cover the full worktree diff.
- Text-mode high-signal secret scan was replaced by a NUL-separated file list scan so Chinese file paths are read without escaped-path errors.

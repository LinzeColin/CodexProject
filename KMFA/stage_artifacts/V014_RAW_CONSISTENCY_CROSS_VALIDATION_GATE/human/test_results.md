# KMFA v0.1.4 Raw Consistency Cross-Validation Test Results

- status: `PASS`
- generator: `PASS`
- validator: `PASS`
- focused_unit_test: `PASS`
- governance_validator: `PASS`
- lean_governance_validator: `PASS`
- governance_sync_validator: `PASS`
- no_float_money_check: `PASS`
- no_omission_check: `PASS`
- structured_parse: `PASS`
- yaml_parse: `PASS`
- raw_private_scan: `PASS`
- secret_scan: `PASS`
- public_artifact_boundary_scan: `PASS`
- diff_check: `PASS`
- full_unittest_discovery: `INTERRUPTED_NOT_USED_AS_PASS_EVIDENCE`

## Commands

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_raw_consistency_cross_validation_gate.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_raw_consistency_cross_validation_gate.py --require-private-diagnostic`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_raw_consistency_cross_validation_gate -q`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`
- structured JSON/JSONL/CSV/YAML parse checks
- tracked raw/private artifact scan
- changed/untracked high-signal secret scan
- scoped current-phase public artifact boundary scan
- `git diff --check -- KMFA scripts`

## Notes

- Full unittest discovery was started as an optional broad regression run and manually interrupted after more than three minutes with no failure output; it was waiting inside older v0.1.3 recursive validation and is not claimed as passed.
- Current phase acceptance relies on the focused unit test, phase validator, governance validators and safety scans above.

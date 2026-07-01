# KMFA Part 1 Review Test Results

- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_file_import_register KMFA.tests.test_source_check_matrix KMFA.tests.test_source_priority -q`: PASS, 11 tests.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_part1_stages_01_03_review -q`: PASS, 1 test.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_part1_stages_01_03_review.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s KMFA/tests -q`: PASS, 269 tests.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA`: PASS, errors=0, warnings=0.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA`: PASS, errors=0, warnings=0.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`: PASS, errors=0, warnings=0.
- YAML parse check: PASS.
- JSON/JSONL/CSV parse check: PASS.
- Raw/private path scan: PASS.
- High-signal secret scan: PASS.
- `git diff --check -- KMFA scripts governance docs`: PASS.

# S04-P1 Test Results

## Final Gate Run

| Command | Result |
|---|---|
| `python3 -m unittest KMFA.tests.test_amount_tools -q` | PASS: 6 tests |
| `python3 KMFA/tools/check_no_float_money.py` | PASS: no KMFA Python float money usage found |
| `python3 -m unittest KMFA.tests.test_source_priority -q` | PASS: 4 tests |
| `python3 -m unittest KMFA.tests.test_source_check_matrix -q` | PASS: 4 tests |
| `python3 -m unittest KMFA.tests.test_file_import_register -q` | PASS: 3 tests |
| `python3 KMFA/tools/check_required_html.py` | PASS: html=45, core=7 |
| `python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=237, tasks=162, v1.2_html=45+ |
| `python3 KMFA/tools/check_report_grade_gate.py` | PASS: quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence |
| `python3 KMFA/tools/immutability_policy_check.py` | PASS: raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes |
| `python3 KMFA/tools/metadata_protocol_check.py` | PASS: dirs=8, files=19, identifiers=5 |
| `python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors=0, warnings=0 |
| `python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors=0, warnings=0 |
| `git diff --check -- README.md governance/projects.yaml KMFA` | PASS: no output |
| `find KMFA -type f ... forbidden suffix scan` | PASS: no output |

## Boundary

- No S04-P2 field standardization was performed.
- No S04-P3 overall utility test report was performed.
- No Stage 4 review was performed.
- No GitHub upload was performed.
- No raw business file or sensitive source value was committed.

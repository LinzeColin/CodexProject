# S07-P1 测试结果

## RED

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_finance_file_adapter -q

FAILED: ModuleNotFoundError: No module named 'KMFA.tools.finance_file_adapter'
```

## GREEN

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_finance_file_adapter -q
Ran 2 tests in 0.010s
OK
```

## Phase Validator

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/finance_file_adapter.py --generated-at 2026-06-30T16:00:00+10:00
PASS: KMFA S07-P1 finance adapter built (categories=9, field_candidates=45, field_reports=9, formal_report_allowed=false)

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s07_p1_finance_file_adapter.py
PASS: KMFA S07-P1 finance file adapter check passed (categories=9, field_candidates=45, field_reports=9, source_header_hashes=45, wps_scope=false, redcircle_scope=false, formal_report_allowed=false)
```

## Final Verification

```text
git diff --check -- KMFA
PASS

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_finance_file_adapter -q
Ran 2 tests in 0.010s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q
Ran 71 tests in 1.684s
OK

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s07_p1_finance_file_adapter.py
PASS: KMFA S07-P1 finance file adapter check passed (categories=9, field_candidates=45, field_reports=9, source_header_hashes=45, wps_scope=false, redcircle_scope=false, formal_report_allowed=false)

PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA
CodexProject governance validation
root: checked
projects checked: KMFA
errors: 0
warnings: 0

PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA
CodexProject governance validation
root: checked
projects checked: KMFA
errors: 0
warnings: 0

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py
PASS: KMFA no omission check passed (requirements=20, P0=9, P1=8, status_records=319, tasks=162, v1.2_html=45+)

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py
PASS: no KMFA Python float money usage found

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py
PASS: KMFA immutability policy check passed (raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes)

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py
PASS: KMFA metadata protocol check passed (dirs=8, files=19, identifiers=5)

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py
PASS: KMFA report grade gate check passed (quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence)

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py
PASS: required KMFA v1.2 HTML/UIUX/report samples are present (html=45, core=7).

JSON/JSONL/CSV parse
PASS: JSON/JSONL/CSV parse ok (json=57, jsonl=27, csv=24)

YAML parse
PASS: YAML parse ok (files=28)

S07-P1 raw/private/secret scan
PASS: S07-P1 raw/private/secret scan ok (paths=36, text_files=33, json_records=57)
PASS: no changed Excel/zip/PDF/sqlite/db; no private-looking changed CSV; no forbidden artifact keys; no secret-like patterns
```

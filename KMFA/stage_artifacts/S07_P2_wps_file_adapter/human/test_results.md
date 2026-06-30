# S07-P2 测试结果

## RED

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_wps_file_adapter -q

FAILED: ModuleNotFoundError: No module named 'KMFA.tools.wps_file_adapter'
```

## GREEN

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_wps_file_adapter -q
Ran 3 tests in 0.006s
OK
```

## Phase Validator

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/wps_file_adapter.py --generated-at 2026-06-30T17:00:00+10:00
PASS: KMFA S07-P2 WPS adapter built (exports=4, field_mappings=20, conversion_guidance=4, rule_versions=1, formal_report_allowed=false)

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s07_p2_wps_file_adapter.py
PASS: KMFA S07-P2 WPS file adapter check passed (exports=4, field_mappings=20, conversion_guidance=4, rule_versions=1, source_header_hashes=20, finance_scope=false, redcircle_scope=false, formal_report_allowed=false)
```

## Final Local Verification

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_wps_file_adapter -q
Ran 3 tests in 0.008s
OK

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s07_p2_wps_file_adapter.py
PASS: KMFA S07-P2 WPS file adapter check passed (exports=4, field_mappings=20, conversion_guidance=4, rule_versions=1, source_header_hashes=20, finance_scope=false, redcircle_scope=false, formal_report_allowed=false)

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s07_p1_finance_file_adapter.py
PASS: KMFA S07-P1 finance file adapter check passed (categories=9, field_candidates=45, field_reports=9, source_header_hashes=45, wps_scope=false, redcircle_scope=false, formal_report_allowed=false)

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q
Ran 74 tests in 1.722s
OK

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py
PASS: no KMFA Python float money usage found

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py
PASS: KMFA metadata protocol check passed (dirs=8, files=19, identifiers=5)

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py
PASS: KMFA no omission check passed (requirements=20, P0=9, P1=8, status_records=324, tasks=162, v1.2_html=45+)

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py
PASS: KMFA immutability policy check passed (raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes)

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py
PASS: KMFA report grade gate check passed (quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence)

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py
PASS: required KMFA v1.2 HTML/UIUX/report samples are present (html=45, core=7).

ruby -rjson -e JSON parse over KMFA/**/*.json
PASS: JSON parse ok (files=61)

ruby -rjson -e JSONL parse over KMFA/**/*.jsonl
PASS: JSONL parse ok (files=30, rows=619)

ruby -rcsv -e CSV parse over KMFA/**/*.csv with bom|utf-8
PASS: CSV parse ok (files=24, rows=629)

ruby -ryaml -e YAML parse over KMFA/**/*.yaml
PASS: YAML parse ok (files=29)

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

PYTHONDONTWRITEBYTECODE=1 python3 added-lines/new-files raw/secret scanner for KMFA S07-P2 changed set
PASS: KMFA S07-P2 added-lines/new-files raw/secret scan passed (files=38, forbidden_exts=0, private_csv=0, secret_patterns=0, forbidden_structured_keys=0)

git diff --check -- KMFA
PASS: exit 0, no whitespace errors
```

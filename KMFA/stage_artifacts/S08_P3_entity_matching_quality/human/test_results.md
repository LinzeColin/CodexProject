# S08-P3 Test Results

test_time: `2026-06-30T22:00:00+10:00`
phase: `S08-P3｜匹配质量测试`
result: `PASS_LOCAL_ONLY`

## TDD Red

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_entity_matching_quality -q`
- Expected failure before implementation: `ModuleNotFoundError: No module named 'KMFA.tools.entity_matching_quality'`

## Commands

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_entity_matching_quality -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/entity_matching_quality.py --generated-at 2026-06-30T22:00:00+10:00
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s08_p3_entity_matching_quality.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s08_p1_project_composite_key.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s08_p2_business_entity_model.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
... JSON/JSONL/CSV parse and CSV width checks ...
PY
ruby -ryaml -e 'Dir["KMFA/**/*.{yaml,yml}"].each { |p| YAML.load_file(p) }'
find KMFA -type f \( -iname '*.zip' -o -iname '*.xlsx' -o -iname '*.xls' -o -iname '*.pdf' -o -iname '*.docx' \)
rg -n --hidden -i "BEGIN (RSA|OPENSSH|DSA|EC) PRIVATE KEY|AKIA[0-9A-Z]{16}|sk-proj-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9]{20,}" KMFA
git diff --check -- KMFA
```

## Results

- Unit tests: PASS, 4 tests.
- Artifact generator: PASS, scenarios=4, quality_cases=4, manual_review_queue=3, `formal_report_allowed=false`, `github_upload_allowed=false`.
- Validator: PASS, scenarios=4, quality_cases=4, manual_review_queue=3, `stage8_review_scope=false`, `fact_layer_scope=false`, `formal_report_allowed=false`, `github_upload_allowed=false`.
- Full KMFA tests: PASS, 88 tests.
- S08-P1 validator: PASS, components=8, profiles=4, matches=3, manual_review_queue=2.
- S08-P2 validator: PASS, entities=8, relationships=14, lifecycle_statuses=32.
- Governance validators: PASS, `errors=0`, `warnings=0`.
- Required HTML/no-omission/metadata/immutability/report-grade validators: PASS.
- JSON/JSONL/CSV parse and CSV width checks: PASS, json=75, jsonl=39, csv=24.
- YAML parse checks: PASS, yaml=30.
- Raw file scan: PASS, no zip/xlsx/xls/pdf/docx files under `KMFA`.
- High-signal secret scan: PASS, no private keys or API tokens.
- `git diff --check -- KMFA`: PASS.

## Boundary Checks

- No raw business data, zip, Excel, PDF, private CSV, source header plaintext or field plaintext was generated.
- `entity_matching_report` is a public-safe matching quality report, not a formal operating or project cost report.
- Medium/high mismatch risks enter manual review and cannot auto-merge.
- Stage 8 review, fact layer, lineage full check, formal report, UI, external connector and GitHub upload are out of scope.

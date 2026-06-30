# S08-P2 Test Results

test_time: `2026-06-30T21:00:00+10:00`
phase: `S08-P2｜业务实体模型`
result: `PASS_LOCAL_ONLY`

## TDD Red

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_business_entity_model -q`
- Expected failure before implementation: `ModuleNotFoundError: No module named 'KMFA.tools.business_entity_model'`

## Commands

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_business_entity_model -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/business_entity_model.py --generated-at 2026-06-30T21:00:00+10:00
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s08_p2_business_entity_model.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py
python3 KMFA/tools/metadata_protocol_check.py
python3 KMFA/tools/immutability_policy_check.py
python3 KMFA/tools/check_report_grade_gate.py
python3 KMFA/tools/check_required_html.py
python3 KMFA/tools/no_omission_check.py
python3 scripts/lean_governance.py validate --project KMFA
python3 scripts/validate_project_governance.py --project KMFA
ruby -e 'require "yaml"; ...'
python3 - <<'PY'
# JSON/JSONL/CSV parse and parameter registry shape check.
PY
python3 - <<'PY'
# Raw file scan: no zip/xlsx/xls/xlsm/pdf outside taskpack and no private CSV.
PY
python3 - <<'PY'
# High-signal secret scan.
PY
python3 - <<'PY'
# S08-P2 evidence consistency check.
PY
git diff --check -- README.md governance/projects.yaml KMFA
```

## Results

- Unit tests: PASS, 3 tests.
- Artifact generator: PASS, entities=8, relationships=14, lifecycle_statuses=32, `formal_report_allowed=false`, `github_upload_allowed=false`.
- Validator: PASS, entities=8, relationships=14, lifecycle_statuses=32, `s08_p3_scope=false`, `fact_layer_scope=false`, `formal_report_allowed=false`, `github_upload_allowed=false`.
- Full KMFA test discovery: PASS, 84 tests.
- No-float money scan: PASS.
- Metadata protocol check: PASS, dirs=8, files=19, identifiers=5.
- Immutability policy check: PASS, raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes.
- Report grade gate: PASS, quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence.
- Required HTML/UIUX/report samples: PASS, html=45, core=7.
- No-omission check: PASS, requirements=20, P0=9, P1=8, status_records=343, tasks=162, v1.2_html=45+.
- Root governance validators: PASS, errors=0, warnings=0.
- YAML parse: PASS.
- JSON/JSONL/CSV parse: PASS, parameter_rows=72, columns=34.
- Raw file scan: PASS, no zip/xlsx/xls/xlsm/pdf outside taskpack and no private CSV.
- High-signal secret scan: PASS.
- S08-P2 evidence consistency: PASS.
- `git diff --check`: PASS.

## Boundary Checks

- No raw business data, zip, Excel, PDF, private CSV or field plaintext was generated.
- Entity schema stores only public-safe required fields, hash/ref/status/evidence metadata and controlled relationship names.
- Lifecycle statuses are metadata-only and do not write the raw layer.
- S08-P3 matching quality test, Stage 8 review, fact layer, lineage full check, report, UI, external connector and GitHub upload are out of scope.

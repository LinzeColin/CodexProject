# S08-P1 Test Results

test_time: `2026-06-30T20:00:00+10:00`
phase: `S08-P1｜项目组合键`
result: `PASS_LOCAL_ONLY`

## TDD Red

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_project_composite_key -q`
- Expected failure before implementation: `ModuleNotFoundError: No module named 'KMFA.tools.project_composite_key'`

## Commands

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_project_composite_key -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/project_composite_key.py --generated-at 2026-06-30T20:00:00+10:00
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s08_p1_project_composite_key.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py
python3 KMFA/tools/metadata_protocol_check.py
python3 KMFA/tools/immutability_policy_check.py
python3 KMFA/tools/check_report_grade_gate.py
python3 KMFA/tools/check_required_html.py
python3 KMFA/tools/no_omission_check.py
python3 scripts/lean_governance.py validate --project KMFA
python3 scripts/validate_project_governance.py --project KMFA
```

## Results

- Unit tests: PASS, 4 tests.
- Artifact generator: PASS, profiles=4, matches=3, manual_review_queue=2, `formal_report_allowed=false`, `github_upload_allowed=false`.
- Validator: PASS, components=8, profiles=4, matches=3, manual_review_queue=2, strong_threshold_bps=8500, human_review_threshold_bps=7000, `formal_report_allowed=false`, `github_upload_allowed=false`.
- KMFA test discovery: PASS, 81 tests.
- No-float money scan: PASS.
- Metadata protocol / immutability / report-grade validators: PASS.
- Required HTML and no-omission validators: PASS, html=45+, tasks=162.
- Governance validators: PASS, errors=0, warnings=0.
- YAML, JSON, JSONL and CSV parse checks: PASS.
- Raw artifact scan: PASS, no zip/xlsx/xls/pdf artifacts outside `KMFA/taskpack`.
- Secret scan: PASS, no high-signal credentials.
- S08-P1 evidence consistency: PASS, components=8, profiles=4, matches=3, manual_review_queue=2, upload=false.
- `git diff --check -- README.md governance/projects.yaml KMFA`: PASS.

## Boundary Checks

- No raw business data, zip, Excel, PDF, private CSV or field plaintext was generated.
- Matching records store hash/private-ref/status/evidence metadata only.
- Missing single component does not create total block.
- Below-strong-threshold candidates enter human review and `auto_merge_allowed=false`.
- S08-P2 entity model, S08-P3 matching quality report, fact layer, lineage full check, report, UI, external connector and GitHub upload are out of scope.

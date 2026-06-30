# S13-P1 Test Results

更新时间: 2026-07-01

## Commands

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_financial_operating_report -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/financial_operating_report.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s13_p1_financial_operating_report.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s KMFA/tests -q
PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py
ruby -e 'require "yaml"; ARGV.each { |f| YAML.load_file(f); puts "PASS YAML #{f}" }' KMFA/docs/governance/roadmap.yaml KMFA/docs/governance/project.yaml KMFA/docs/governance/VERSION_MATRIX.yaml KMFA/docs/governance/ASSURANCE_STATUS.yaml KMFA/metadata/project/project.yaml KMFA/metadata/model_registry.yaml KMFA/docs/governance/formula_registry.yaml KMFA/docs/governance/model_registry.yaml
JSON/JSONL/CSV parse check for KMFA excluding taskpack/v1_2
raw forbidden extension scan for zip/xlsx/xls/pdf/sqlite/db excluding taskpack/v1_2
high-signal secret scan excluding taskpack/v1_2 and rendered/docs/csv/private binary extensions
git diff --check -- README.md governance/projects.yaml KMFA
```

## Results

- unit tests: PASS, `Ran 6 tests OK`.
- generator: PASS, `source_lanes=4`, `drafts=2`, `html=2`, `field_mappings=39`, `formal_report_allowed=false`, `s13_p2_scope=false`, `s13_p3_scope=false`, `lineage_full_check_scope=false`, `github_upload=false`.
- validator: PASS, `source_lanes=4`, `drafts=2`, `html=2`, `field_mappings=39`, `pending_reconciliation=12`, `report_grade_visible=D`, `formal_report_allowed=false`, `business_decision_basis=false`, `s13_p2_scope=false`, `s13_p3_scope=false`, `lineage_full_check_scope=false`, `github_upload=false`.
- full KMFA tests: PASS, `Ran 158 tests OK`.
- lean governance validator: PASS, `errors=0`, `warnings=0`.
- project governance validator: PASS, `errors=0`, `warnings=0`.
- no_omission: PASS, `requirements=20`, `P0=9`, `P1=8`, `status_records=431`, `tasks=162`, `v1.2_html=45+`.
- required HTML: PASS, `html=45`, `core=7`.
- no-float money, metadata protocol, immutability policy and report grade gate: PASS.
- YAML parse: PASS for governance roadmap/project/version/assurance metadata and model/formula registries.
- JSON/JSONL/CSV parse: PASS, `json=110`, `jsonl=59`, `csv=10`.
- raw forbidden extension scan: PASS, `hits=0`.
- high-signal secret scan: PASS, `hits=0`.
- git diff check: PASS.

## Boundary Evidence

- No raw business data, zip, Excel workbook, PDF, private CSV, field plaintext, real money values, real account numbers or credentials are included in S13-P1 outputs.
- S13-P1 does not execute S13-P2, S13-P3, Stage 13 review, GitHub upload, lineage full check, formal report, external connector, payment, loan management or tax filing.

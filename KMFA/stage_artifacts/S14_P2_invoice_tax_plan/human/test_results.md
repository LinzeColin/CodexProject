# KMFA S14-P2 Test Results

- phase: `S14-P2｜开票纳税`
- status: `completed_validated_local_only`
- generated_at: `2026-07-01T23:00:00+10:00`
- scope: `only S14-P2 invoice tax planning artifacts; no Stage 14 review, no GitHub upload`

## Target Validation

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_invoice_tax_plan -q` | PASS: 6 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s14_p2_invoice_tax_plan.py` | PASS: source_lanes=3, issue_candidates=3, cash_summaries=3, report_grade_visible=D, formal_report_allowed=false, tax_filing=false, invoice_issuance=false, s14_p3_scope=false, stage14_review=false, github_upload=false |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s KMFA/tests -q` | PASS: 184 tests |

## Governance And Safety Validation

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=455, tasks=162, v1.2_html=45+ |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py` | PASS: html=45, core=7 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py` | PASS: dirs=8, files=19, identifiers=5 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py` | PASS |
| `python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors=0, warnings=0 |
| `python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors=0, warnings=0 |
| YAML parse check for assurance, version matrix, formula registry, model registry, project and roadmap files | PASS |
| JSON/JSONL/CSV parse check for S14-P2 manifests, events, stage status and parameter registry | PASS |
| `git diff --check -- KMFA scripts` | PASS |

## Raw And Secret Scan

| Command | Result |
|---|---|
| `find KMFA -type f \( -name '*.zip' -o -name '*.xlsx' -o -name '*.xls' -o -name '*.pdf' -o -name '*.sqlite' -o -name '*.db' \) -not -path 'KMFA/taskpack/v1_2/*' -not -path 'KMFA/stage_artifacts/S01_REBASE_V12_FULL_TASKPACK/*' -print` | PASS: no forbidden raw/private file types found |
| S14-P2 public output forbidden-token scan | PASS: no private refs, raw values, true amounts, invoice numbers, tax declaration numbers, account identifiers or forbidden file suffixes found |
| high-signal raw/secret scan across `KMFA` excluding taskpack/stage1 replay | PASS_WITH_POLICY_TEXT_MATCHES_ONLY: matches are governance stop-condition or policy text, not credentials or raw business data |

## Boundary Confirmation

- `formal_report_allowed=false`
- `business_decision_basis_allowed=false`
- `tax_filing_allowed=false`
- `invoice_issuance_allowed=false`
- `invoice_operation_allowed=false`
- `payment_or_bank_operation_allowed=false`
- `stage14_review_allowed=false`
- `github_upload_allowed=false`
- `s14_p3_scope_included=false`

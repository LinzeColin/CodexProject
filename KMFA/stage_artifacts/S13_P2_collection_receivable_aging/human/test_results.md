# S13-P2｜回款应收账龄测试结果

## TDD Red

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_collection_receivable_aging -q

ModuleNotFoundError: No module named 'KMFA.tools.collection_receivable_aging'
FAILED (errors=1)
```

## Targeted Green

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_collection_receivable_aging -q

Ran 6 tests in 0.017s
OK
```

## Artifact Generation

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/collection_receivable_aging.py

PASS: KMFA S13-P2 collection receivable aging artifacts generated (source_lanes=5, priority_items=4, responsibility_items=4, html=1, field_mappings=25, formal_report_allowed=false, business_decision_basis=false, payment_or_bank_operation=false, legal_collection_decision=false, s13_p3_scope=false, stage13_review=false, github_upload=false)
```

## Phase Validator

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s13_p2_collection_receivable_aging.py

PASS: KMFA S13-P2 collection receivable aging check passed (source_lanes=5, issue_types=4, priority_items=4, responsibility_items=4, field_mappings=25, pending_reconciliation=12, report_grade_visible=D, formal_report_allowed=false, business_decision_basis=false, legal_collection_decision=false, payment_or_bank_operation=false, s13_p3_scope=false, stage13_review=false, github_upload=false)
```

## Final Verification

```text
git rebase --autostash origin/main
Successfully rebased and updated refs/heads/codex/kmfa.
origin/main: 1ed592aeb0f4345fd9287e46111b4abe9a3187da

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_financial_operating_report -q
Ran 6 tests in 0.015s
OK

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s13_p1_financial_operating_report.py
PASS: KMFA S13-P1 financial operating report check passed (source_lanes=4, drafts=2, html=2, field_mappings=39, pending_reconciliation=12, report_grade_visible=D, formal_report_allowed=false, business_decision_basis=false, s13_p2_scope=false, s13_p3_scope=false, lineage_full_check_scope=false, github_upload=false)

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_collection_receivable_aging -q
Ran 6 tests in 0.016s
OK

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s13_p2_collection_receivable_aging.py
PASS: KMFA S13-P2 collection receivable aging check passed (source_lanes=5, issue_types=4, priority_items=4, responsibility_items=4, field_mappings=25, pending_reconciliation=12, report_grade_visible=D, formal_report_allowed=false, business_decision_basis=false, legal_collection_decision=false, payment_or_bank_operation=false, s13_p3_scope=false, stage13_review=false, github_upload=false)

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s KMFA/tests -q
Ran 164 tests in 1.966s
OK

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py
PASS: KMFA no omission check passed (requirements=20, P0=9, P1=8, status_records=436, tasks=162, v1.2_html=45+)

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py
PASS: required KMFA v1.2 HTML/UIUX/report samples are present (html=45, core=7).

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py
PASS: no KMFA Python float money usage found

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py
PASS: KMFA metadata protocol check passed (dirs=8, files=19, identifiers=5)

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py
PASS: KMFA immutability policy check passed (raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes)

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py
PASS: KMFA report grade gate check passed (quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence)

python3 scripts/lean_governance.py validate --project KMFA
errors: 0
warnings: 0

python3 scripts/validate_project_governance.py --project KMFA
errors: 0
warnings: 0

ruby -ryaml -e 'ARGV.each { |p| YAML.load_file(p); puts "yaml_ok #{p}" }' ...
yaml_ok for S13-P2 governance YAML files

git diff --check -- KMFA scripts
PASS

changed-file raw/secret scan
PASS: changed-file raw/secret scan passed files=33 public_governance_csv_allowlist=1
```

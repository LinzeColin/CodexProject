# S09-P3 Test Results

- project_id: `KMFA`
- stage_phase: `S09-P3`
- evidence_time: `2026-06-30T23:55:00+10:00`
- status: `phase_validated_local_only`
- github_upload_performed: `false`

## TDD Evidence

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_project_scope_reconciliation -q
```

Initial expected failure before implementation:

```text
ModuleNotFoundError: No module named 'KMFA.tools.project_scope_reconciliation'
FAILED (errors=1)
```

Passing result after implementation:

```text
Ran 4 tests in 0.007s
OK
```

## Phase Artifact Generation

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/project_scope_reconciliation.py --generated-at 2026-06-30T23:55:00+10:00
PASS: KMFA S09-P3 scope reconciliation artifacts written (reconciliation_records=12, domain_controls=6, confirmed_resolutions=0, pending_resolutions=12, derived_metric_rerun_allowed=false, formal_report_allowed=false, stage9_review_allowed=false, github_upload_allowed=false)
```

## Check-only Generation

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/project_scope_reconciliation.py --generated-at 2026-06-30T23:55:00+10:00 --check-only
PASS: KMFA S09-P3 scope reconciliation artifacts validated (reconciliation_records=12, domain_controls=6, confirmed_resolutions=0, pending_resolutions=12, derived_metric_rerun_allowed=false, formal_report_allowed=false, stage9_review_allowed=false, github_upload_allowed=false)
```

## Phase Validator

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s09_p3_scope_reconciliation.py
PASS: KMFA S09-P3 scope reconciliation check passed (reconciliation_records=12, domain_controls=6, confirmed_resolutions=0, pending_resolutions=12, derived_metric_rerun_allowed=false, formal_report_allowed=false, stage9_review_allowed=false, github_upload_allowed=false)
```

## Final Validation Matrix

| Check | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_project_scope_reconciliation -q` | `Ran 4 tests in 0.010s / OK` |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s09_p3_scope_reconciliation.py` | `PASS` |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/project_scope_reconciliation.py --generated-at 2026-06-30T23:55:00+10:00 --check-only` | `PASS` |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s09_p1_project_cost_fact_layer.py` | `PASS` |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s09_p2_margin_cash_margin.py` | `PASS` |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q` | `Ran 100 tests in 1.802s / OK` |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA` | `errors: 0 / warnings: 0` |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA` | `errors: 0 / warnings: 0` |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py` | `PASS: requirements=20, P0=9, P1=8, status_records=367, tasks=162, v1.2_html=45+` |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py` | `PASS: dirs=8, files=19, identifiers=5` |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py` | `PASS` |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py` | `PASS` |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py` | `PASS: html=45, core=7` |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py` | `PASS` |
| JSON/JSONL/CSV parse checks | `PASS` |
| `KMFA/docs/governance/parameter_registry.csv` shape check | `PASS: rows=96, columns=34` |
| Changed-file raw/private extension scan | `PASS: changed_files=29` |
| Changed-file high-signal secret scan | `PASS: changed_files=29` |
| `git diff --check -- KMFA` | `PASS` |

## Scope Boundary

- S09-P3 only.
- Stage 9 review is not executed.
- Derived metrics and formal reports are not rerun.
- GitHub upload is not executed.
- Raw/private business artifacts are not committed.

# S09-P2 Test Results

- project_id: `KMFA`
- stage_phase: `S09-P2`
- evidence_time: `2026-06-30T23:45:00+10:00`
- status: `phase_validated_local_only`
- github_upload_performed: `false`

## TDD Evidence

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_project_margin_cash_margin -q
```

Initial expected failure before implementation:

```text
ModuleNotFoundError: No module named 'KMFA.tools.project_margin_cash_margin'
FAILED (errors=1)
```

Passing result after implementation:

```text
Ran 4 tests in 0.007s
OK
```

## Phase Artifact Generation

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/project_margin_cash_margin.py --generated-at 2026-06-30T23:45:00+10:00
PASS: KMFA S09-P2 margin and cash margin artifacts written (margin_records=4, difference_summary=12, s09_p3_scope=false, formal_report_allowed=false, github_upload_allowed=false)
```

## Phase Validator

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s09_p2_margin_cash_margin.py
PASS: KMFA S09-P2 margin and cash margin check passed (margin_records=4, difference_summary=12, upstream_manual_review_queue=3, upstream_unresolved_differences=1, s09_p3_scope=false, formal_report_allowed=false, github_upload_allowed=false)
```

## Final Verification Matrix

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_project_margin_cash_margin -q` | PASS: Ran 4 tests; OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s09_p2_margin_cash_margin.py` | PASS: margin_records=4, difference_summary=12, s09_p3_scope=false, formal_report_allowed=false, github_upload_allowed=false |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q` | PASS: Ran 96 tests; OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors=0, warnings=0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors=0, warnings=0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=362, tasks=162, v1.2_html=45+ |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py` | PASS: dirs=8, files=19, identifiers=5 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py` | PASS: raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py` | PASS: html=45, core=7 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py` | PASS: release_gate=blocked_by_missing_evidence |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py` | PASS: no KMFA Python float money usage found |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s09_p1_project_cost_fact_layer.py` | PASS: fact_records=4, cost_categories=9, unallocated_pool=9, s09_p2_scope=false, s09_p3_scope=false |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_project_cost_fact_layer KMFA.tests.test_project_margin_cash_margin -q` | PASS: Ran 8 tests; OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s05_p2_completion_gate.py --decision KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/owner_decision_records/excel_owner_resolution_decision.json` | PASS: ready, mode=owner_downgrade_to_cross_source_support, decision_code=downgrade_to_cross_source_support |
| `JSON/JSONL/YAML/CSV parse check over KMFA/` | PASS: json=81, jsonl=43, yaml=30, csv=24 |
| `raw/private extension scan over KMFA/` | PASS: no zip/xlsx/xls/pdf/sqlite/db/parquet files found |
| `secret pattern scan over KMFA/` | PASS: no credential patterns found |
| `git diff --check -- README.md governance/projects.yaml KMFA` | PASS: no whitespace errors |

## Validator Note

- `KMFA/tools/check_s05_p2_completion_gate.py` without `--decision` still returns the historical expected BLOCKED state because five Excel fields remain pending in the default no-decision mode.
- The active owner/authorized downgrade decision is the current S05-P2 resolving gate evidence and passes with `--decision`.
- This note is not a S09-P2 failure.

## Scope Boundary

- S09-P2 only.
- S09-P3 is not executed.
- Stage 9 review is not executed.
- GitHub upload is not executed.
- Raw/private business artifacts are not committed.

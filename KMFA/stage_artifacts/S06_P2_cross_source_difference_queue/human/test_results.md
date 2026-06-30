# S06-P2 测试结果

## Phase Tests

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_cross_source_difference_queue -q
----------------------------------------------------------------------
Ran 6 tests in 0.065s

OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/cross_source_difference_queue.py --fixture KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_synthetic_pdf_excel_conflict_fixture.json --queue-jsonl KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_synthetic_difference_queue.jsonl --gate-json KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_report_grade_gate.json
{"queue_items": 1, "report_grade_a_allowed": false, "status": "queued_for_manual_review"}
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s06_p2_difference_queue.py
PASS: KMFA S06-P2 difference queue check passed (queue_items=1, report_grade_a_allowed=False)
```

## Regression And Governance Sweep

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q
----------------------------------------------------------------------
Ran 65 tests in 1.629s

OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py
PASS: no KMFA Python float money usage found
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py
PASS: KMFA no omission check passed (requirements=20, P0=9, P1=8, status_records=305, tasks=162, v1.2_html=45+)
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py
PASS: KMFA immutability policy check passed (raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes)
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py
PASS: KMFA metadata protocol check passed (dirs=8, files=19, identifiers=5)
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py
PASS: KMFA report grade gate check passed (quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence)
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA
CodexProject governance validation
root: checked
projects checked: KMFA
errors: 0
warnings: 0
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA
CodexProject governance validation
root: checked
projects checked: KMFA
errors: 0
warnings: 0
```

## Structure And Safety Checks

```text
JSON/JSONL parse check
PASS: JSON/JSONL parse check passed (files=74)
```

```text
parameter_registry.csv column count check
PASS: parameter_registry.csv column check passed (columns=34, rows=42)
```

```text
changed-file raw artifact scan
PASS: changed-file raw artifact scan passed (changed_files=34, blocked_files=0)
```

```text
changed-file secret scan
PASS: changed-file secret scan passed (files=31, findings=0)
```

```text
git diff --check -- README.md governance/projects.yaml KMFA
exit 0; no whitespace errors reported
```

## Pre-Commit Staged Checks

```text
staged raw artifact scan with git diff --cached --name-only -z
PASS: staged raw artifact scan passed with -z paths (staged_files=34, blocked_files=0)
```

```text
staged secret scan with git diff --cached --name-only -z
PASS: staged secret scan passed with -z paths (files=34, findings=0)
```

## Evidence Scope

- `raw_business_data_used=false`
- `public_repo_raw_files_committed=false`
- `private_csv_committed=false`
- `report_grade_a_allowed_before_resolution=false`
- `stage6_review_completed=false`
- `github_upload_allowed=false`

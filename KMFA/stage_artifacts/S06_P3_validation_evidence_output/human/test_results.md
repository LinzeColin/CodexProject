# S06-P3 测试结果

## TDD RED

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_validation_evidence_output -q
ModuleNotFoundError: No module named 'KMFA.tools.validation_evidence_output'
FAILED (errors=1)
```

## Phase Tests

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_validation_evidence_output -q
----------------------------------------------------------------------
Ran 4 tests in 0.064s

OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/validation_evidence_output.py --zero-delta-result KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_zero_delta_result.json --source-mismatch-report KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_mismatch_report.csv --difference-queue KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_synthetic_difference_queue.jsonl --report-gate KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_report_grade_gate.json --output-dir KMFA/stage_artifacts/S06_P3_validation_evidence_output/machine --metadata-quality-dir KMFA/metadata/quality --evidence-time 2026-06-30T14:30:00+10:00
{"metadata_quality_records": 4, "mismatches": 1, "project_statuses": 2, "zero_delta_passed": false}
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s06_p3_validation_evidence.py
PASS: KMFA S06-P3 validation evidence check passed (metadata_quality_records=3+)
```

## Final Verification

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q
----------------------------------------------------------------------
Ran 69 tests in 1.652s

OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py
PASS: no KMFA Python float money usage found

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py
PASS: KMFA no omission check passed (requirements=20, P0=9, P1=8, status_records=310, tasks=162, v1.2_html=45+)

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py
PASS: KMFA immutability policy check passed (raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes)

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py
PASS: KMFA metadata protocol check passed (dirs=8, files=19, identifiers=5)

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py
PASS: KMFA report grade gate check passed (quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence)

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s06_p3_validation_evidence.py
PASS: KMFA S06-P3 validation evidence check passed (metadata_quality_records=3+)
```

```text
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
```

```text
JSON/JSONL parse check: PASS (files=76)
parameter registry CSV shape check: PASS (columns=34, rows=46)
git diff --check -- README.md governance/projects.yaml KMFA: PASS
changed-file raw artifact scan: PASS
changed-file secret scan: PASS
```

## Evidence Scope

- `raw_business_data_used=false`
- `public_repo_raw_files_committed=false`
- `private_csv_committed=false`
- `sensitive_field_plaintext_committed=false`
- `source_amount_literals_committed=false`
- `report_grade_a_allowed_before_resolution=false`
- `stage6_review_completed=false`
- `github_upload_allowed=false`

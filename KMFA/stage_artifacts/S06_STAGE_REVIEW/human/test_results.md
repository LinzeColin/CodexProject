# KMFA Stage 6 Review Test Results

- review_id: `KMFA-S06-STAGE-REVIEW-20260630`
- test_time: `2026-06-30T15:10:00+10:00`
- result: `PASS_UPLOAD_READY_LOCAL_ONLY`
- raw_business_data_used: `false`
- github_upload_status: `not_pushed`

## Commands

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_zero_delta_validator -q` | PASS: 6 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/zero_delta_validator.py --fixture KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_mismatch_fixture.json --result-json KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_zero_delta_result.json --mismatch-report KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_mismatch_report.csv` | PASS: expected exit 1 for 1-cent mismatch; `zero_delta_passed=false`, `mismatch_count=1` |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_cross_source_difference_queue -q` | PASS: 6 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/cross_source_difference_queue.py --fixture KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_synthetic_pdf_excel_conflict_fixture.json --queue-jsonl KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_synthetic_difference_queue.jsonl --gate-json KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_report_grade_gate.json` | PASS: queue_items=1, `report_grade_a_allowed=false` |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s06_p2_difference_queue.py` | PASS: queue_items=1, `report_grade_a_allowed=False` |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_validation_evidence_output -q` | PASS: 4 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/validation_evidence_output.py --zero-delta-result KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_zero_delta_result.json --source-mismatch-report KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_mismatch_report.csv --difference-queue KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_synthetic_difference_queue.jsonl --report-gate KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_report_grade_gate.json --output-dir KMFA/stage_artifacts/S06_P3_validation_evidence_output/machine --metadata-quality-dir KMFA/metadata/quality --evidence-time 2026-06-30T14:30:00+10:00` | PASS: metadata_quality_records=4, mismatches=1, project_statuses=2, `zero_delta_passed=false` |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s06_p3_validation_evidence.py` | PASS: metadata_quality_records=3+ |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q` | PASS: 69 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_s05_p3_authority_baseline_lock -q` | PASS: 4 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/a0_authority_baseline_lock.py --locked-at 2026-06-30T12:00:00+10:00 --locked-by-ref codex_delegate_s05p3_public_safe_lock_20260630 --check-only` | PASS: q5_locked_fields=40, excluded_fields=5, `formal_report_allowed=false` |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_a0_authority_baseline_lock.py` | PASS: q5_locked_fields=40, excluded_fields=5, authority_records=45, `formal_report_allowed=false` |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=312, tasks=162, v1.2_html=45+ |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py` | PASS: html=45, core=7 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors 0 / warnings 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors 0 / warnings 0 |
| JSON/JSONL parse check | PASS: files=77 |
| parameter registry CSV shape check | PASS: columns=34, rows=46 |
| `git diff --check -- README.md governance/projects.yaml KMFA` | PASS |
| changed-file raw artifact scan | PASS: no forbidden raw/private binary artifacts |
| changed-file secret scan | PASS |
| S06 stage review evidence consistency check | PASS: P1/P2/P3 artifacts and review manifest aligned |
| S06-P3 forbidden output text scan | PASS: no forbidden raw/field/plaintext terms in S06-P3 public output surface |

## Evidence

- `KMFA/stage_artifacts/S06_STAGE_REVIEW/human/stage6_review_report.md`
- `KMFA/stage_artifacts/S06_STAGE_REVIEW/human/test_results.md`
- `KMFA/stage_artifacts/S06_STAGE_REVIEW/machine/stage6_review_manifest.json`
- `KMFA/stage_artifacts/S06_P1_zero_delta_validator/human/test_results.md`
- `KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/human/test_results.md`
- `KMFA/stage_artifacts/S06_P3_validation_evidence_output/human/test_results.md`

## Remaining Upload Validation

The final GitHub upload step must rerun this command set after reconciling with latest `origin/main`, then record the final commit and push proof.

# KMFA v0.1.3 Stage 1 Review Test Results

- review_id: `KMFA-V013-S01-STAGE-REVIEW-20260702`
- test_time: `2026-07-02T15:28:53+10:00`
- result: `PASS_UPLOAD_READY_LOCAL_ONLY_NO_GO`
- raw_business_data_used: `false`
- github_upload_status: `not_pushed`

## Commands

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s01_stage_review.py` | PASS: phases=3, findings_open=0, actual_lineage_rows=0, pending_reconciliation=12, grade_D=2, requirements=20, github_upload=false, delivery_allowed=false |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s01_stage_review -q` | PASS: 1 test |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s01_p1_preflight.py` | PASS: actual_lineage_rows=0, pending_reconciliation=12, grade_D=2, delivery_allowed=false |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s01_p2_scope_freeze.py` | PASS: actual_lineage_rows=0, pending_reconciliation=12, grade_D=2, delivery_allowed=false, stage_review=false, github_upload=false |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s01_p3_no_omission_gate.py` | PASS: requirements=20, P0=9, P1=8, stage_status_records=549, task_records=162, stage_review=false, github_upload=false, delivery_allowed=false |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=549, tasks=162, v1.2_html=45+ |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s KMFA/tests -q` | PASS: 283 tests |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors 0 / warnings 0 |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors 0 / warnings 0 |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync` | PASS: errors 0 / warnings 0 |
| structured changed-file parse check | PASS: json=1, jsonl=1, jsonl_records=119, csv=2, csv_rows=364 |
| changed-file raw/private path scan | PASS: files=18, no forbidden raw/private paths |
| high-signal secret scan | PASS: files=18, no high-signal secrets |
| `git diff --check -- KMFA scripts` | PASS |

## Evidence

- `KMFA/stage_artifacts/V013_S01_STAGE_REVIEW/human/stage1_review_report.md`
- `KMFA/stage_artifacts/V013_S01_STAGE_REVIEW/human/test_results.md`
- `KMFA/stage_artifacts/V013_S01_STAGE_REVIEW/machine/stage1_review_manifest.json`
- `KMFA/tools/check_v013_s01_stage_review.py`

## Remaining Upload Validation

Stage 1 GitHub upload remains a separate gate. It must rebase or otherwise reconcile with latest `origin/main`, refresh review evidence bindings, rerun the command set, and record dry-run push, push and post-push parity.

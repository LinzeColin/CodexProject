# KMFA Stage 5 Review Test Results

- review_id: `KMFA-S05-STAGE-REVIEW-20260630`
- test_time: `2026-06-30T13:00:00+10:00`
- result: `PASS_UPLOAD_READY_LOCAL_ONLY`
- raw_business_data_used: `false`
- github_upload_status: `not_pushed`

## Commands

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_a0_file_register -q` | PASS: 3 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_a0_file_registration.py` | PASS: files=9, pdf=8, excel=1, member_sha256_recorded=0, member_sha256_pending=9, candidates=9 |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_a0_golden_fixture KMFA.tests.test_s05_p2_excel_owner_decision KMFA.tests.test_s05_p2_owner_decision_intake KMFA.tests.test_s05_p2_owner_decision_templates KMFA.tests.test_s05_p2_owner_decision_application KMFA.tests.test_s05_p2_completion_gate -q` | PASS: 20 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_a0_golden_fixture.py` | PASS: fixture_candidates=45, fields_per_candidate=5, private_value_hash_recorded=40, private_value_pending=5, source_anchor_recorded=40, source_anchor_pending=5 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s05_p2_excel_owner_decision.py` | PASS: allowed_decisions=3, pending_fields=5, status=awaiting_owner_or_authorized_decision |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s05_p2_owner_decision_intake.py --decision KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/owner_decision_records/excel_owner_resolution_decision.json` | PASS: decision_status=validated_public_safe, decision_code=downgrade_to_cross_source_support |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s05_p2_owner_decision_templates.py` | PASS: template_count=3, active_decision_records=0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s05_p2_completion_gate.py --decision KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/owner_decision_records/excel_owner_resolution_decision.json` | PASS: ready, mode=owner_downgrade_to_cross_source_support, pending_fields=5, decision_code=downgrade_to_cross_source_support |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_s05_p3_authority_baseline_lock -q` | PASS: 4 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_a0_authority_baseline_lock.py` | PASS: q5_locked_fields=40, excluded_fields=5, authority_records=45, formal_report_allowed=false |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_a0_golden_fixture KMFA.tests.test_s05_p2_excel_owner_decision KMFA.tests.test_s05_p2_owner_decision_intake KMFA.tests.test_s05_p2_owner_decision_templates KMFA.tests.test_s05_p2_owner_decision_application KMFA.tests.test_s05_p2_completion_gate KMFA.tests.test_s05_p3_authority_baseline_lock KMFA.tests.test_a0_file_register KMFA.tests.test_file_import_register KMFA.tests.test_source_check_matrix KMFA.tests.test_source_priority KMFA.tests.test_amount_tools KMFA.tests.test_field_standardization KMFA.tests.test_basic_tool_boundaries -q` | PASS: 53 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=293, tasks=162, v1.2_html=45+ |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py` | PASS: dirs=8, files=19, identifiers=5 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py` | PASS: raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py` | PASS: quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors 0 / warnings 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors 0 / warnings 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py` | PASS: no KMFA Python float money usage |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py` | PASS: html=45, core=7 |
| `git diff --check -- README.md governance/projects.yaml KMFA` | PASS |
| `find KMFA -path 'KMFA/taskpack/v1_2/*' -prune -o -path 'KMFA/stage_artifacts/S01_REBASE_V12_FULL_TASKPACK/*' -prune -o -type f \( -name '*.zip' -o -name '*.xls' -o -name '*.xlsx' -o -name '*.pdf' -o -name '*.sqlite' -o -name '*.db' -o -name '*.sqlite-shm' -o -name '*.sqlite-wal' \) -print` | PASS: no files found |
| `rg -n --hidden -i '(sk-[A-Za-z0-9_-]{20,}\|api[_-]?key\s*[:=]\|password\s*[:=]\|secret\s*[:=]\|银行流水\|纳税申报\|工资明细\|身份证\|银行卡号)' KMFA -g '!KMFA/taskpack/v1_2/**' -g '!KMFA/stage_artifacts/S01_REBASE_V12_FULL_TASKPACK/**'` | PASS_WITH_POLICY_TEXT_MATCHES_ONLY |

## JSON / JSONL Parse Checks

| File | Result |
|---|---|
| `KMFA/metadata/baseline/a0_authority_baseline_records.jsonl` | PASS: 45 records |
| `KMFA/metadata/stage_status.jsonl` | PASS: 293 records |
| `KMFA/docs/governance/events.jsonl` | PASS: 32 records |
| `KMFA/docs/governance/development_events.jsonl` | PASS: 32 records |
| `KMFA/metadata/approvals/control_events.jsonl` | PASS: 5 records |
| `KMFA/metadata/approvals/resolution_events.jsonl` | PASS: 5 records |
| `KMFA/metadata/baseline/a0_authority_baseline_manifest.json` | PASS: valid JSON |

## Evidence

- `KMFA/stage_artifacts/S05_STAGE_REVIEW/human/stage5_review_report.md`
- `KMFA/stage_artifacts/S05_STAGE_REVIEW/human/test_results.md`
- `KMFA/stage_artifacts/S05_STAGE_REVIEW/machine/stage5_review_manifest.json`

## Remaining Upload Validation

The final GitHub upload step must rerun this command set after reconciling with latest `origin/main`, then record the final commit and push proof.

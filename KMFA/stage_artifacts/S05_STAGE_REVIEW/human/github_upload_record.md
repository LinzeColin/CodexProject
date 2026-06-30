# KMFA Stage 5 GitHub Upload Record

upload_id: `KMFA-S05-GITHUB-UPLOAD-20260630`
upload_time: `2026-06-30T13:13:10+10:00`
stage: `S05 - A0 权威项目成本黄金基准`
target: `LinzeColin/CodexProject main`
result: `UPLOADED_TO_GITHUB_MAIN`

## Evidence

- reviewed_content_commit: `ca6788949c444188b4b93f7db42c94094d90209f`
- reviewed_s05p3_commit: `c3314e47ce11cfb8bf56e44d4a38a77904584495`
- upload_base_origin_main: `495bcd977a587b7fd8b1923bfd74f5138f12263e`
- review_report: `KMFA/stage_artifacts/S05_STAGE_REVIEW/human/stage5_review_report.md`
- review_test_results: `KMFA/stage_artifacts/S05_STAGE_REVIEW/human/test_results.md`
- upload_manifest: `KMFA/stage_artifacts/S05_STAGE_REVIEW/machine/stage5_upload_manifest.json`

## Validation Before Upload

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_a0_file_register -q`: PASS, 3 tests.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_a0_file_registration.py`: PASS, files=9, pdf=8, excel=1, member_sha256_recorded=0, member_sha256_pending=9, candidates=9.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_a0_golden_fixture KMFA.tests.test_s05_p2_excel_owner_decision KMFA.tests.test_s05_p2_owner_decision_intake KMFA.tests.test_s05_p2_owner_decision_templates KMFA.tests.test_s05_p2_owner_decision_application KMFA.tests.test_s05_p2_completion_gate -q`: PASS, 20 tests.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_a0_golden_fixture.py`: PASS, fixture_candidates=45, fields_per_candidate=5, private_value_hash_recorded=40, private_value_pending=5, source_anchor_recorded=40, source_anchor_pending=5.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s05_p2_excel_owner_decision.py`: PASS, allowed_decisions=3, pending_fields=5, status=awaiting_owner_or_authorized_decision.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s05_p2_owner_decision_intake.py --decision KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/owner_decision_records/excel_owner_resolution_decision.json`: PASS, decision_status=validated_public_safe, decision_code=downgrade_to_cross_source_support.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s05_p2_owner_decision_templates.py`: PASS, template_count=3, active_decision_records=0.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s05_p2_completion_gate.py --decision KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/owner_decision_records/excel_owner_resolution_decision.json`: PASS, mode=owner_downgrade_to_cross_source_support, pending_fields=5.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_s05_p3_authority_baseline_lock -q`: PASS, 4 tests.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_a0_authority_baseline_lock.py`: PASS, q5_locked_fields=40, excluded_fields=5, authority_records=45, formal_report_allowed=false.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_a0_golden_fixture KMFA.tests.test_s05_p2_excel_owner_decision KMFA.tests.test_s05_p2_owner_decision_intake KMFA.tests.test_s05_p2_owner_decision_templates KMFA.tests.test_s05_p2_owner_decision_application KMFA.tests.test_s05_p2_completion_gate KMFA.tests.test_s05_p3_authority_baseline_lock KMFA.tests.test_a0_file_register KMFA.tests.test_file_import_register KMFA.tests.test_source_check_matrix KMFA.tests.test_source_priority KMFA.tests.test_amount_tools KMFA.tests.test_field_standardization KMFA.tests.test_basic_tool_boundaries -q`: PASS, 53 tests.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py`: PASS, requirements=20, P0=9, P1=8, status_records=295, tasks=162, v1.2_html=45+.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py`: PASS, dirs=8, files=19, identifiers=5.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py`: PASS, raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py`: PASS, quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py`: PASS, html=45, core=7.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA`: PASS, errors 0 / warnings 0.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA`: PASS, errors 0 / warnings 0.
- `git diff --check -- README.md governance/projects.yaml KMFA`: PASS.
- sensitive file suffix scan: PASS, no `.zip`, `.xls`, `.xlsx`, `.pdf`, `.sqlite`, `.db`, `.sqlite-shm` or `.sqlite-wal` under `KMFA/` outside committed taskpack/baseline exclusions.
- high-signal secret/raw text scan: PASS_WITH_POLICY_TEXT_MATCHES_ONLY.
- JSONL parse check: PASS, authority_records=45, stage_status=295, governance_events=33, development_events=33, control_events=5, resolution_events=5.

## Boundary

- No raw business files were uploaded.
- Stage 5 upload did not implement S06 zero-delta, fact layer, lineage full check, management reports, UI, or external interfaces.
- The upload preserves remote `origin/main` history by rebasing the full Stage 5 stack on top of `495bcd977a587b7fd8b1923bfd74f5138f12263e` before push.

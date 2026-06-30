# KMFA Stage 6 GitHub Upload Record

upload_id: `KMFA-S06-GITHUB-UPLOAD-20260630`
upload_time: `2026-06-30T15:40:00+10:00`
stage: `S06 - 零差异校验与差异处理队列`
target: `LinzeColin/CodexProject main`
result: `UPLOADED_TO_GITHUB_MAIN`

## Evidence

- reviewed_content_commit: `5cd284e500fec5ff215741b0e8ee164912f50268`
- reviewed_s06p3_commit: `c66c8b44c17ae760a5a6da4b98ab5892d90d73d0`
- upload_base_origin_main: `fd14057e7427d7f275fdb62a33619936618d0d35`
- review_report: `KMFA/stage_artifacts/S06_STAGE_REVIEW/human/stage6_review_report.md`
- review_test_results: `KMFA/stage_artifacts/S06_STAGE_REVIEW/human/test_results.md`
- upload_manifest: `KMFA/stage_artifacts/S06_STAGE_REVIEW/machine/stage6_upload_manifest.json`

## Validation Before Upload

- `git fetch origin main`: PASS.
- `git rebase origin/main`: PASS, Stage 6 stack replayed on `fd14057e7427d7f275fdb62a33619936618d0d35`.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q`: PASS, 69 tests.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/zero_delta_validator.py --fixture KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_mismatch_fixture.json --result-json KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_zero_delta_result.json --mismatch-report KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_mismatch_report.csv`: PASS, expected exit 1 for 1-cent mismatch; `zero_delta_passed=false`, `mismatch_count=1`.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/cross_source_difference_queue.py --fixture KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_synthetic_pdf_excel_conflict_fixture.json --queue-jsonl KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_synthetic_difference_queue.jsonl --gate-json KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_report_grade_gate.json`: PASS, queue_items=1, `report_grade_a_allowed=false`.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s06_p2_difference_queue.py`: PASS, queue_items=1, `report_grade_a_allowed=False`.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/validation_evidence_output.py --zero-delta-result KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_zero_delta_result.json --source-mismatch-report KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_mismatch_report.csv --difference-queue KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_synthetic_difference_queue.jsonl --report-gate KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_report_grade_gate.json --output-dir KMFA/stage_artifacts/S06_P3_validation_evidence_output/machine --metadata-quality-dir KMFA/metadata/quality --evidence-time 2026-06-30T14:30:00+10:00`: PASS, metadata_quality_records=4, mismatches=1, project_statuses=2, `zero_delta_passed=false`.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s06_p3_validation_evidence.py`: PASS, public-safe metadata/quality evidence only.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/a0_authority_baseline_lock.py --locked-at 2026-06-30T12:00:00+10:00 --locked-by-ref codex_delegate_s05p3_public_safe_lock_20260630 --check-only`: PASS, q5_locked_fields=40, excluded_fields=5, `formal_report_allowed=false`.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_a0_authority_baseline_lock.py`: PASS, authority_records=45.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py`: PASS, requirements=20, P0=9, P1=8, tasks=162, v1.2_html=45+.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py`: PASS, html=45, core=7.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA`: PASS, errors 0 / warnings 0.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA`: PASS, errors 0 / warnings 0.
- JSON/JSONL parse check: PASS.
- parameter registry CSV shape check: PASS.
- upload evidence consistency check: PASS.
- raw/private artifact scan: PASS.
- high-signal secret scan: PASS.
- staged raw/private artifact scan: PASS.
- staged high-signal secret scan: PASS.
- `git diff --check -- README.md governance/projects.yaml KMFA`: PASS.
- `git push --dry-run origin HEAD:main`: PASS.
- `git push origin HEAD:main`: PASS.
- post-push parity check: PASS, `HEAD == origin/main`.

## Upload Gate Finding Fixes

- `KMFA-S06-UPLOAD-F01`: fixed rebase binding for Stage 6 review evidence by updating `reviewed_head` from the pre-rebase S06-P3 commit to `c66c8b44c17ae760a5a6da4b98ab5892d90d73d0`.
- `KMFA-S06-UPLOAD-F02`: fixed duplicate and stale Stage 6 upload policy state in `KMFA/metadata/project/project.yaml`; the file now records one authoritative Stage 6 uploaded state.

## Boundary

- No raw business data, zip, Excel, PDF, private CSV, credentials, bank statements, contracts, payroll files, tax filings or private extracted values were uploaded.
- Stage 6 upload does not implement S07 file adapters, fact layer, lineage full check, management reports, UI or external connectors.
- The next work item is `S07-P1｜财务文件适配`, and it must be handled as a separate phase.

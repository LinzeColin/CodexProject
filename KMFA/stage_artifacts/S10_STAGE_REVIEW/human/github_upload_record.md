# KMFA Stage 10 GitHub Upload Record

upload_id: `KMFA-S10-GITHUB-UPLOAD-20260630`
upload_time: `2026-06-30T23:59:59+10:00`
stage: `S10 - 报告可信等级与经营报告生成`
target: `LinzeColin/CodexProject main`
result: `UPLOADED_TO_GITHUB_MAIN`

## Evidence

- upload_base_origin_main: `6b6e599100e59cfdd0c404b28f58821b396b3267`
- reviewed_content_commit: `171d89d2ca74f78292e97502488bf6d31b11a247`
- reviewed_s10p1_commit: `de4fe18a00509c2f92e97b7cea22a13c61814b9d`
- reviewed_s10p2_commit: `6882fcf6f2a08da4b9eb434c20b943abd739d8c8`
- reviewed_s10p3_commit: `00bd0e28619db095948ab104b7764c61c04b0e8a`
- review_report: `KMFA/stage_artifacts/S10_STAGE_REVIEW/human/stage10_review_report.md`
- review_test_results: `KMFA/stage_artifacts/S10_STAGE_REVIEW/human/test_results.md`
- upload_manifest: `KMFA/stage_artifacts/S10_STAGE_REVIEW/machine/stage10_upload_manifest.json`

## Validation Before Upload

- `git rev-parse --show-toplevel`: PASS, `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/kmfa`.
- `git branch --show-current`: PASS, `codex/kmfa`.
- `git remote -v`: PASS, `git@github.com:LinzeColin/CodexProject.git`.
- `git fetch origin`: PASS.
- `git rebase origin/main`: PASS, Stage 10 stack replayed on `6b6e599100e59cfdd0c404b28f58821b396b3267`.
- `git status --short --branch`: PASS, clean branch ahead of `origin/main` after rebase.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s10_p1_report_templates.py`: PASS, templates=2, sections=11, project_cost_sections=4, business_overview_sections=7, formal_report_allowed=false, trusted_grade_assignment_allowed=false, s10_p2_scope=false, s10_p3_scope=false, ui_scope=false, lineage_full_check_scope=false, external_connector_scope=false.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s10_p2_report_grade_runtime.py`: PASS, grade_records=2, grade_distribution={'D': 2}, pending_reconciliation_count=12, complete_trusted_report_display_allowed=false, formal_report_allowed=false, business_decision_basis_allowed=false, s10_p3_scope=false, export_artifact_count=0.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s10_p3_report_export.py`: PASS, export_records=2, html_exports=2, csv_appendices=2, excel_compatible_downloads=2, pdf_private_runtime_enabled=true, committed_pdf_files=0, committed_excel_files=0, formal_report_allowed=false, business_decision_basis_allowed=false, stage10_review=false, github_upload=false.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s10_stage_review.py`: PASS, report_templates=2, sections=11, grade_records=2, export_records=2, html_exports=2, csv_appendices=2, pending_owner_or_authorized_review_records=12, upload_allowed_after_review=true, s11_allowed=false, github_upload_status=not_pushed.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q`: PASS, 116 tests.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py`: PASS, requirements=20, P0=9, P1=8, status_records=386, tasks=162, v1.2_html=45+.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py`: PASS, html=45, core=7.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py`: PASS, dirs=8, files=19, identifiers=5.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py`: PASS, raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py`: PASS, quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA`: PASS, errors 0 / warnings 0.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA`: PASS, errors 0 / warnings 0.
- YAML parse check: PASS, files=30.
- JSON/JSONL/CSV parse check: PASS, json=92, jsonl=49, jsonl_records=851, csv=26, csv_rows=718.
- raw/private artifact scan: PASS, no zip/xlsx/xls/xlsm/pdf/doc/docx/sqlite/db files under `KMFA`.
- high-signal secret scan: PASS, hits=0.
- `git diff --check -- README.md governance/projects.yaml KMFA`: PASS.
- `git push --dry-run origin HEAD:main`: PASS after upload evidence commit.
- `git push origin HEAD:main`: PASS after upload evidence commit.
- post-push parity check: PASS, `HEAD == origin/main == remote main`.

## Boundary

- No raw business data, zip, Excel workbook, PDF, private CSV, credentials, bank statements, contracts, payroll files, tax filings, sqlite/db files or private extracted values are included in this upload evidence.
- Stage 10 upload does not implement S11, UI, lineage full check, formal reports, external connectors, difference closure, derived metric rerun or business release.
- The next work item is `S11-P1｜首页与导航`, and it must be handled as a separate phase.

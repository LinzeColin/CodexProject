# KMFA Stage 13 GitHub Upload Record

upload_id: `KMFA-S13-GITHUB-UPLOAD-20260701`
upload_time: `2026-07-01T21:00:00+10:00`
stage: `S13 - 财务经营报表与回款应收扩展`
target: `LinzeColin/CodexProject main`
result: `UPLOADED_TO_GITHUB_MAIN`

## Evidence

- upload_base_origin_main: `dfdf16c98656c4272fa105027dcbf46ba15d37dd`
- reviewed_content_commit: `7b61cc92ce4535bdfa4b459bcd280c4352b6bf95`
- reviewed_s13p1_commit: `891abf61001bdc36c64582535713f6a3215aad0a`
- reviewed_s13p2_commit: `0a1242a2b9803656a0e4fd34095140e2df550c0c`
- reviewed_s13p3_commit: `55c96758d7c883d5aa7131189bb77fcf669f0f4b`
- review_report: `KMFA/stage_artifacts/S13_STAGE_REVIEW/human/stage13_review_report.md`
- review_test_results: `KMFA/stage_artifacts/S13_STAGE_REVIEW/human/test_results.md`
- review_manifest: `KMFA/stage_artifacts/S13_STAGE_REVIEW/machine/stage13_review_manifest.json`
- upload_manifest: `KMFA/stage_artifacts/S13_GITHUB_UPLOAD/machine/stage13_upload_manifest.json`

## Validation Before Upload

- `git rev-parse --show-toplevel`: PASS, `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/kmfa`.
- `git branch --show-current`: PASS, `codex/kmfa`.
- `git remote -v`: PASS, `git@github.com:LinzeColin/CodexProject.git`.
- `git fetch origin main`: PASS, latest `origin/main` was `dfdf16c98656c4272fa105027dcbf46ba15d37dd`.
- `git status --short --branch`: PASS, branch ahead of `origin/main` with no unrelated changes before upload evidence.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s13_p1_financial_operating_report.py`: PASS, source_lanes=4, drafts=2, html=2, field_mappings=39, pending_reconciliation=12, report_grade_visible=D, formal_report_allowed=false, business_decision_basis=false, s13_p2_scope=false, s13_p3_scope=false, lineage_full_check_scope=false, github_upload=false.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s13_p2_collection_receivable_aging.py`: PASS, source_lanes=5, issue_types=4, priority_items=4, responsibility_items=4, field_mappings=25, pending_reconciliation=12, report_grade_visible=D, formal_report_allowed=false, business_decision_basis=false, legal_collection_decision=false, payment_or_bank_operation=false, s13_p3_scope=false, stage13_review=false, github_upload=false.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s13_p3_cross_table_review.py`: PASS, review_dimensions=4, difference_queue=4, quality_report=1, pending_reconciliation=12, report_grade_visible=D, formal_report_allowed=false, business_decision_basis=false, difference_auto_resolution=false, stage13_review=false, github_upload=false.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s13_stage_review.py`: PASS, financial_lanes=4, drafts=2, collection_lanes=5, priority_items=4, review_dimensions=4, difference_queue=4, quality_reports=1, pending_reconciliation=12, upload_allowed_after_review=true, s14_allowed=false, github_upload_status=not_pushed.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s KMFA/tests -q`: PASS, 172 tests.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py`: PASS, requirements=20, P0=9, P1=8, status_records=445, tasks=162, v1.2_html=45+.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py`: PASS, html=45, core=7.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py`: PASS, dirs=8, files=19, identifiers=5.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py`: PASS, raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py`: PASS, quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence.
- `python3 scripts/lean_governance.py validate --project KMFA`: PASS, errors 0 / warnings 0.
- `python3 scripts/validate_project_governance.py --project KMFA`: PASS, errors 0 / warnings 0.
- YAML parse check: PASS.
- JSON/JSONL/CSV parse check: PASS, stage_status rows=445, events rows=73, development_events rows=73, parameter_registry rows=150 columns=34.
- tracked raw/private artifact scan: PASS, forbidden tracked artifacts outside `KMFA/taskpack/v1_2/` = 0.
- high-signal secret scan: PASS, hits=0.
- `git diff --check -- KMFA scripts`: PASS.
- `git push --dry-run origin HEAD:main`: PASS after upload evidence commit.
- `git push origin HEAD:main`: PASS after upload evidence commit.
- post-push parity check: PASS, `HEAD == origin/main == remote main`.

## Boundary

- No raw business data, zip, Excel workbook, PDF, private CSV, credentials, bank statements, contracts, payroll files, tax filings, sqlite/db files, true account numbers, true money amounts or field plaintext are included in this upload evidence.
- Stage 13 upload only publishes the reviewed public-safe financial operating report drafts, collection receivable aging draft, cross-table review evidence, Stage 13 review evidence and upload proof.
- Stage 13 upload does not implement S14, lineage full check, formal reports, external connectors, difference closure, invoicing, payment, bank operations, tax filing, legal collection actions or business release.
- Operating and collection outputs remain grade `D`; 12 pending reconciliation records still block formal report use and business decision basis.

## Next Work Item

The next work item is `S14-P1｜资金计划现金贷款` as a separate run work. It must start from a fresh git/root/status check, read the v1.2 task pack and roadmap, and must not bypass the D-grade report and pending reconciliation gates.

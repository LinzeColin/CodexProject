# KMFA Stage 14 GitHub Upload Record

upload_id: `KMFA-S14-GITHUB-UPLOAD-20260701`
upload_time: `2026-07-01T23:59:59+10:00`
stage: `S14 - 资金、开票、纳税与政策证据模块`
target: `LinzeColin/CodexProject main`
result: `UPLOADED_TO_GITHUB_MAIN`

## Evidence

- upload_base_origin_main: `76782d14bd324a3c44f4e7fc843b6e7cad8843a2`
- reviewed_content_commit: `15774b953e2a6fd57cf0a96723aa6c00abd8fc14`
- reviewed_s14p1_commit: `a655d37ed8ac68f4c4d409c6a85ec78b9a592986`
- reviewed_s14p2_commit: `18279aff3241322deff271a3845398c70eac8f80`
- reviewed_s14p3_commit: `783e5acf081d61d858e7c5c6d5c233434b57007e`
- review_commit: `15774b953e2a6fd57cf0a96723aa6c00abd8fc14`
- review_report: `KMFA/stage_artifacts/S14_STAGE_REVIEW/human/stage14_review_report.md`
- review_test_results: `KMFA/stage_artifacts/S14_STAGE_REVIEW/human/test_results.md`
- review_manifest: `KMFA/stage_artifacts/S14_STAGE_REVIEW/machine/stage14_review_manifest.json`
- upload_manifest: `KMFA/stage_artifacts/S14_GITHUB_UPLOAD/machine/stage14_upload_manifest.json`

## Validation Before Upload

- `pwd`: PASS, `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/kmfa`.
- `git rev-parse --show-toplevel`: PASS, `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/kmfa`.
- `git branch --show-current`: PASS, `codex/kmfa`.
- `git remote -v`: PASS, `git@github.com:LinzeColin/CodexProject.git`.
- `git fetch origin main`: PASS, latest `origin/main` was `76782d14bd324a3c44f4e7fc843b6e7cad8843a2`.
- `git rebase origin/main`: PASS, Stage 14 reviewed stack rebased cleanly.
- `git status --short --branch`: PASS, branch ahead of `origin/main` with no unrelated changes before upload evidence.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s14_p1_fund_cash_loan_plan.py`: PASS, source_lanes=4, cash_pressure=4, loan_due_alerts=3, account_summaries=3, field_mappings=25, pending_reconciliation=12, report_grade_visible=D, formal_report_allowed=false, business_decision_basis=false, payment_approval=false, bank_operation=false, loan_management=false, s14_p2_scope=false, s14_p3_scope=false, stage14_review=false, github_upload=false.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s14_p2_invoice_tax_plan.py`: PASS, source_lanes=3, issue_candidates=3, cash_summaries=3, field_mappings=30, pending_reconciliation=12, report_grade_visible=D, formal_report_allowed=false, business_decision_basis=false, tax_filing=false, invoice_issuance=false, invoice_operation=false, s14_p3_scope=false, stage14_review=false, github_upload=false.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s14_p3_policy_evidence_plan.py`: PASS, policy_programs=5, directories=5, gaps=5, risk_tips=5, field_mappings=19, pending_reconciliation=12, report_grade_visible=D, formal_report_allowed=false, policy_conclusion=false, policy_submission=false, stage14_review=false, github_upload=false.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s14_stage_review.py`: PASS, fund_lanes=4, cash_pressure=4, invoice_tax_lanes=3, invoice_tax_issues=3, policy_directories=5, policy_gaps=5, pending_reconciliation=12, upload_allowed_after_review=true, s15_allowed=false, github_upload_status=not_pushed.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s KMFA/tests -q`: PASS, 191 tests.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py`: PASS, requirements=20, P0=9, P1=8, status_records=464, tasks=162, v1.2_html=45+.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py`: PASS, html=45, core=7.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py`: PASS, dirs=8, files=19, identifiers=5.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py`: PASS, raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py`: PASS, quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence.
- `python3 scripts/lean_governance.py validate --project KMFA`: PASS, errors 0 / warnings 0.
- `python3 scripts/validate_project_governance.py --project KMFA`: PASS, errors 0 / warnings 0.
- YAML parse check: PASS.
- JSON/JSONL/CSV parse check: PASS, stage_status rows=464, events rows=78, development_events rows=78, parameter_registry rows=170 columns=34.
- tracked raw/private artifact scan: PASS, forbidden tracked artifacts outside `KMFA/taskpack/v1_2/` = 0.
- high-signal secret scan: PASS, hits=0.
- `git diff --check -- KMFA scripts`: PASS.
- `git push --dry-run origin HEAD:main`: PASS after upload evidence commit.
- `git push origin HEAD:main`: PASS after upload evidence commit.
- post-push parity check: PASS, `HEAD == origin/main == remote main`.

## Boundary

- No raw business data, zip, Excel workbook, PDF, private CSV, credentials, bank statements, contracts, payroll files, tax filings, sqlite/db files, true account numbers, true money amounts, invoice numbers, tax filing files, policy application files, policy score, policy qualification conclusion or field plaintext are included in this upload evidence.
- Stage 14 upload only publishes the reviewed public-safe fund/cash/loan planning signals, invoice/tax planning signals, policy evidence directory/gap/risk-tip evidence, Stage 14 review evidence and upload proof.
- Stage 14 upload does not implement S15, lineage full check, formal reports, external connectors, difference closure, payment, bank operations, loan management actions, invoice issuance, tax filing, policy qualification decisions, policy submissions, subsidies, legal collection actions or business release.
- All Stage 14 outputs remain grade `D`; 12 pending reconciliation records still block formal report use, business decision basis, policy qualification conclusions and operational execution.

## Next Work Item

The next work item is `S15-P1｜销售绩效事实与复核清单` as a separate run work. It must start from a fresh git/root/status check, read the v1.2 task pack and roadmap, and must not bypass the D-grade report, pending reconciliation, lineage and public-safe repository gates.

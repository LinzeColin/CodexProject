# KMFA Stage 15 GitHub Upload Record

upload_id: `KMFA-S15-GITHUB-UPLOAD-20260701`
upload_time: `2026-07-01T23:59:59+10:00`
stage: `S15 - 销售绩效事实与复核清单`
target: `LinzeColin/CodexProject main`
result: `UPLOADED_TO_GITHUB_MAIN`

## Evidence

- upload_base_origin_main: `7aff82efe2dd83fce940a97868868c13e65a6f1c`
- reviewed_content_commit: `e79f5d3e5f55ddc99ea392a99e9a2aa30fb5beae`
- reviewed_s15p1_commit: `22103a21bef44290c69e0635a36f3cf672dfb68f`
- reviewed_s15p2_commit: `0bc0f6c58b7264916c1a51b177d0134d1c61c38d`
- reviewed_s15p3_commit: `39004e31fbc9655106d69ff12a7a46ae26f8ae49`
- review_commit: `e79f5d3e5f55ddc99ea392a99e9a2aa30fb5beae`
- review_report: `KMFA/stage_artifacts/S15_STAGE_REVIEW/human/stage15_review_report.md`
- review_test_results: `KMFA/stage_artifacts/S15_STAGE_REVIEW/human/test_results.md`
- review_manifest: `KMFA/stage_artifacts/S15_STAGE_REVIEW/machine/stage15_review_manifest.json`
- upload_manifest: `KMFA/stage_artifacts/S15_GITHUB_UPLOAD/machine/stage15_upload_manifest.json`

## Validation Before Upload

- `pwd`: PASS, `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/kmfa`.
- `git rev-parse --show-toplevel`: PASS, `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/kmfa`.
- `git branch --show-current`: PASS, `codex/kmfa`.
- `git remote -v`: PASS, `git@github.com:LinzeColin/CodexProject.git`.
- `git fetch origin`: PASS, latest `origin/main` was `7aff82efe2dd83fce940a97868868c13e65a6f1c`.
- `git rebase origin/main`: PASS, Stage 15 reviewed stack rebased cleanly.
- `git status --short --branch`: PASS, branch ahead of `origin/main` with no unrelated changes before upload evidence.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_performance_fact_fields.py`: PASS, 5 tests.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s15_p1_performance_fact_fields.py`: PASS, fields=6, bindings=6, manual_reviews=4, salary_calculation=false, bonus_approval=false, payroll_export=false, github_upload=false.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_performance_review_list.py`: PASS, 5 tests.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s15_p2_performance_review_list.py`: PASS, fact_rows=4, review_items=16, salary_calculation=false, bonus_approval=false, payroll_export=false, final_compensation=false, github_upload=false.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_performance_salary_boundary.py`: PASS, 5 tests.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s15_p3_salary_boundary.py`: PASS, interface_contracts=1, readiness_rows=4, live_integration=false, salary_calculation=false, bonus_approval=false, payroll_export=false, final_approval_human=true, payment_release_human=true, github_upload=false.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_s15_stage_review.py`: PASS, 1 test.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s15_stage_review.py`: PASS, fields=6, bindings=6, fact_rows=4, review_items=16, interface_contracts=1, readiness_rows=4, salary_calculation=false, bonus_approval=false, payroll_export=false, final_compensation=false, github_upload=false.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s KMFA/tests -q`: PASS, 207 tests.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py`: PASS, requirements=20, P0=9, P1=8, status_records=483, tasks=162, v1.2_html=45+.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py`: PASS, html=45, core=7.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py`: PASS, dirs=8, files=19, identifiers=5.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py`: PASS, raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py`: PASS, quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence.
- `python3 scripts/lean_governance.py validate --project KMFA`: PASS, errors 0 / warnings 0.
- `python3 scripts/validate_project_governance.py --project KMFA`: PASS, errors 0 / warnings 0.
- YAML parse check: PASS.
- JSON/JSONL/CSV parse check: PASS, stage_status rows=483, events rows=83, development_events rows=83, parameter_registry rows=194 columns=34.
- tracked raw/private artifact scan: PASS, forbidden tracked artifacts outside `KMFA/taskpack/v1_2/` = 0.
- high-signal secret scan: PASS, hits=0.
- `git diff --check -- KMFA scripts`: PASS.
- `git push --dry-run origin HEAD:main`: PASS after upload evidence commit.
- `git push origin HEAD:main`: PASS after upload evidence commit.
- post-push parity check: PASS, `HEAD == origin/main == remote main`.

## Boundary

- No raw business data, zip, Excel workbook, PDF, private CSV, sqlite/db files, bank statements, contracts, payroll files, tax filings, source field plaintext, true account numbers, true money amounts, true staff details, salary materials, bonus approval material or interface secrets are included in this upload evidence.
- Stage 15 upload only publishes reviewed public-safe performance fact fields, performance fact/review records, salary-boundary interface contract/readiness draft, Stage 15 review evidence and upload proof.
- Stage 15 upload does not implement S16, lineage full check, formal reports, external connectors, salary calculation, wage calculation, bonus approval, payroll export, final compensation, payment release, automatic payroll execution or business release.
- All Stage 15 outputs remain grade `D` or public-safe evidence. The 12 pending reconciliation records still block formal report use, business decision basis and operational execution.

## Next Work Item

The next work item is `S16-P1｜外协采购归集` as a separate run work. It must start from a fresh git/root/status check, read the v1.2 task pack and roadmap, and must not bypass the D-grade report, pending reconciliation, lineage, public-safe repository, formal report, salary, bonus, payroll or payment-release gates.

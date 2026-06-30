# KMFA Stage 7 GitHub Upload Record

upload_id: `KMFA-S07-GITHUB-UPLOAD-20260630`
upload_time: `2026-06-30T19:30:00+10:00`
stage: `S07 - 文件型源适配与字段映射`
target: `LinzeColin/CodexProject main`
result: `UPLOADED_TO_GITHUB_MAIN`

## Evidence

- upload_base_origin_main: `a734729629efc07d49d95732b400144d39dc343c`
- reviewed_content_commit: `e7f0bf78935b8769cfa19d4dd55029e565b6a2d2`
- reviewed_s07p1_commit: `d1f3d0d37b6530306cfadfcc8ad4e1eefb8210aa`
- reviewed_s07p2_commit: `859ab9de59e449e134f61480e54cdd2ec6ea712c`
- reviewed_s07p3_commit: `98a21215db0a74da352f02fe171d0ebaf6510389`
- review_report: `KMFA/stage_artifacts/S07_STAGE_REVIEW/human/stage7_review_report.md`
- review_test_results: `KMFA/stage_artifacts/S07_STAGE_REVIEW/human/test_results.md`
- upload_manifest: `KMFA/stage_artifacts/S07_STAGE_REVIEW/machine/stage7_upload_manifest.json`

## Validation Before Upload

- `git rev-parse --show-toplevel`: PASS, `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/kmfa`.
- `git branch --show-current`: PASS, `codex/kmfa`.
- `git remote -v`: PASS, `git@github.com:LinzeColin/CodexProject.git`.
- `git rev-parse HEAD`: PASS, `e7f0bf78935b8769cfa19d4dd55029e565b6a2d2` before upload evidence commit.
- `git status --short --branch`: PASS, clean branch ahead of `origin/main`.
- `git fetch origin --prune`: PASS.
- `git rebase origin/main`: PASS, Stage 7 stack replayed on `a734729629efc07d49d95732b400144d39dc343c`.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s07_p1_finance_file_adapter.py`: PASS, categories=9, field_candidates=45, field_reports=9, source_header_hashes=45, WPS/redcircle/formal-report scopes false.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s07_p2_wps_file_adapter.py`: PASS, exports=4, field_mappings=20, conversion_guidance=4, rule_versions=1, source_header_hashes=20, finance/redcircle/formal-report scopes false.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s07_p3_redcircle_postponement.py`: PASS, templates=4, rollback_plans=4, D15 connector disallowed, read-only/hash/rollback/manual approval required, formal-report scope false.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q`: PASS, 77 tests.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA`: PASS, errors 0 / warnings 0.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA`: PASS, errors 0 / warnings 0.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py`: PASS, html=45, core=7.
- YAML parse check: PASS.
- JSON/JSONL/CSV parse check: PASS.
- Stage 7 evidence consistency check: PASS.
- raw/private artifact scan: PASS, no zip/xlsx/xls/pdf outside the committed taskpack baseline.
- high-signal secret scan: PASS, no hits.
- `git diff --check -- README.md governance/projects.yaml KMFA`: PASS.
- `git push --dry-run origin HEAD:main`: PASS before upload evidence commit, SSH remote writable.
- `git push --dry-run origin HEAD:main`: PASS after upload evidence commit.
- `git push origin HEAD:main`: PASS after upload evidence commit.
- post-push parity check: PASS, `HEAD == origin/main`.

## Boundary

- No raw business data, zip, Excel, PDF, private CSV, credentials, bank statements, contracts, payroll files, tax filings or private extracted values are included in this upload evidence.
- Stage 7 upload does not implement S08 project identity matching, fact layer, lineage full check, management reports, UI or external connectors.
- The next work item is `S08-P1｜项目组合键`, and it must be handled as a separate phase.

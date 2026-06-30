# KMFA Stage 8 GitHub Upload Record

upload_id: `KMFA-S08-GITHUB-UPLOAD-20260630`
upload_time: `2026-06-30T23:20:00+10:00`
stage: `S08 - 业务实体与项目身份匹配`
target: `LinzeColin/CodexProject main`
result: `UPLOADED_TO_GITHUB_MAIN`

## Evidence

- upload_base_origin_main: `ce2881204c49a56da463893db5314ff180c7812d`
- reviewed_content_commit: `4add0b6a00798008f6eb3439ff5a8da10279265f`
- reviewed_s08p1_commit: `c728f4a84eec99c716e36738966ea9f6de80be41`
- reviewed_s08p2_commit: `aab6bb8e13298ffa63e65eaf1290d65036326e57`
- reviewed_s08p3_commit: `15e4782e063a4c53b0549ecc674a9c321ec69913`
- review_report: `KMFA/stage_artifacts/S08_STAGE_REVIEW/human/stage8_review_report.md`
- review_test_results: `KMFA/stage_artifacts/S08_STAGE_REVIEW/human/test_results.md`
- upload_manifest: `KMFA/stage_artifacts/S08_STAGE_REVIEW/machine/stage8_upload_manifest.json`

## Validation Before Upload

- `git rev-parse --show-toplevel`: PASS, `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/kmfa`.
- `git branch --show-current`: PASS, `codex/kmfa`.
- `git remote -v`: PASS, `git@github.com:LinzeColin/CodexProject.git`.
- `git rev-parse HEAD`: PASS, `4add0b6a00798008f6eb3439ff5a8da10279265f` before upload evidence commit.
- `git status --short --branch`: PASS, clean branch ahead of `origin/main`.
- `git fetch origin`: PASS.
- `git rebase origin/main`: PASS, Stage 8 stack replayed on `ce2881204c49a56da463893db5314ff180c7812d`.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s08_p1_project_composite_key.py`: PASS, components=8, profiles=4, matches=3, manual_review_queue=2, formal-report/upload scopes false.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s08_p2_business_entity_model.py`: PASS, entities=8, relationships=14, lifecycle_statuses=32, S08-P3/fact-layer/formal-report/upload scopes false.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s08_p3_entity_matching_quality.py`: PASS, scenarios=4, quality_cases=4, manual_review_queue=3, stage-review/fact-layer/formal-report/upload scopes false.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q`: PASS, 88 tests.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA`: PASS, errors 0 / warnings 0.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA`: PASS, errors 0 / warnings 0.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py`: PASS, html=45, core=7.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py`: PASS, requirements=20, P0=9, P1=8, status_records=352, tasks=162.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py`: PASS.
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py`: PASS.
- YAML parse check: PASS, files=30.
- JSON/JSONL/CSV parse check: PASS, json=77, jsonl=39, jsonl_records=733, csv=24, csv_rows=676.
- Stage 8 evidence consistency check: PASS.
- raw/private artifact scan: PASS, no zip/xlsx/xls/pdf/docx files under `KMFA`.
- high-signal secret scan: PASS, no hits.
- `git diff --check -- README.md governance/projects.yaml KMFA`: PASS.
- `git push --dry-run origin HEAD:main`: PASS before upload evidence commit, SSH remote writable.
- `git push --dry-run origin HEAD:main`: PASS after upload evidence commit.
- `git push origin HEAD:main`: PASS after upload evidence commit.
- post-push parity check: PASS, `HEAD == origin/main`.

## Boundary

- No raw business data, zip, Excel, PDF, private CSV, credentials, bank statements, contracts, payroll files, tax filings or private extracted values are included in this upload evidence.
- Stage 8 upload does not implement S09 fact layer, lineage full check, management reports, UI or external connectors.
- The next work item is `S09-P1｜项目成本事实层`, and it must be handled as a separate phase.

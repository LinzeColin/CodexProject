# KMFA v0.1.3 Stage 1-10 GitHub Upload Gate

- upload_id: `KMFA-V013-STAGE1-10-GITHUB-UPLOAD-20260703`
- upload_time: `2026-07-03T19:32:29+10:00`
- project_id: `KMFA`
- source_scope: `v0.1.3 Stage 1-10 batch overall review`
- target: `LinzeColin/CodexProject main`
- branch: `codex/kmfa`
- status: `ready_to_push_github_main_public_safe`
- upload_base_origin_main: `387f2bdd1e4cb06d3fced781417f057f854c2901`
- reviewed_stage1_10_batch_commit: `494a166779fa8fdc1a282d1ebbdca293e3e78886`
- upload_evidence_commit: `recorded_by_commit_containing_this_file`

## Scope

This gate records the v0.1.3 Stage 1-10 batch reviewed KMFA stack after rebasing onto the latest `origin/main`. It is only a public-safe GitHub main upload gate for reviewed code, governance records, validators, tests and evidence.

This gate does not perform raw value matching, lineage full check, formal report release, live connector work, Redcircle automatic connector work, OpMe deep coupling or business execution.

## Validation Evidence

- `check_v013_stage1_10_batch_review.py`: PASS, stages=10, open_batch_findings=0, upload_ready_next_gate=true, github_upload=false
- S01-S10 v0.1.3 stage review validators: PASS
- focused upload gate unit test: PASS
- focused batch review unit test: PASS
- full KMFA unit tests: PASS, 326 tests
- no-float check: PASS
- no-omission check: PASS, requirements=20, P0=9, P1=8, tasks=162, v1.2_html=45+
- project governance validator: PASS, errors=0, warnings=0
- lean governance validator: PASS, errors=0, warnings=0
- governance sync validator: PASS, changed scope KMFA only, errors=0, warnings=0
- structured parse and YAML parse checks: PASS
- raw/private path scan, strict key-shaped secret scan and public-safe semantic scan: PASS
- `git diff --check -- KMFA`: PASS
- Git push dry-run, push and post-push parity: required after local evidence commit; final command outputs are terminal proof for this upload gate.

## Public Repository Boundary

- raw business data uploaded: `false`
- zip uploaded: `false`
- Excel/PDF uploaded: `false`
- private CSV uploaded: `false`
- sqlite/db uploaded: `false`
- bank statement / contract / payroll / tax filing uploaded: `false`
- field plaintext / raw filename / raw hash / sheet name / row value / true amount uploaded: `false`
- credentials or connector secrets uploaded: `false`
- formal report, live connector, OpMe deep coupling or production business action uploaded: `false`

## Evidence References

- `KMFA/stage_artifacts/V013_STAGE1_10_BATCH_REVIEW/machine/stage1_10_batch_review_manifest.json`
- `KMFA/stage_artifacts/V013_STAGE1_10_BATCH_REVIEW/human/stage1_10_batch_review_report.md`
- `KMFA/stage_artifacts/V013_STAGE1_10_BATCH_REVIEW/human/test_results.md`
- `KMFA/stage_artifacts/V013_STAGE1_10_GITHUB_UPLOAD/machine/stage1_10_github_upload_manifest.json`
- `KMFA/stage_artifacts/V013_STAGE1_10_GITHUB_UPLOAD/human/test_results.md`

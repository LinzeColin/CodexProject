# KMFA v0.1.3 Stage 1-10 GitHub Upload Gate Test Results

- upload_id: `KMFA-V013-STAGE1-10-GITHUB-UPLOAD-20260703`
- status: `ready_to_push_github_main_public_safe`
- github_main_push_performed_before_local_evidence_commit: `false`
- raw_inbox_read_by_this_upload_gate: `false`
- raw_inbox_mutation_performed: `false`
- formal_report_allowed: `false`
- business_execution_allowed: `false`

## Command Results

- PASS: upload gate validator, focused upload gate unit test and focused batch review unit test passed.
- PASS: S01-S10 v0.1.3 stage review validators all passed after rebase onto `origin/main`.
- PASS: full KMFA unittest discovery passed with 326 tests.
- PASS: no-float, no-omission, project governance, lean governance, governance sync, structured parse, YAML parse and diff check passed.
- PASS: raw/private path scan, strict key-shaped secret scan and public-safe evidence semantic scan passed.
- REQUIRED: push dry-run, push and post-push parity must be executed after this local evidence commit.

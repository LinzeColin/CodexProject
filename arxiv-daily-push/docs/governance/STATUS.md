# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.19`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +26`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +26`
- Current iteration: `ITER-20260621-038`
- Current phase: `E`
- Current gate: `ADP-PHASE11-PRODUCTION-TRIAL-START-PRECHECK-BLOCKED`
- Model count: `29`
- Formula count: `31`
- Parameter count: `153`
- Task count: `33`
- Unbound event count: `45`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `0`
- Semantic coverage: `machine_verified`
- Semantic rollout task: `GOV-SEMANTIC-ADP-001`

## Latest Run

- Event: `EVENT-20260622-ADP-045`
- Task: `ADP-PHASE11-PRODUCTION-TRIAL-START-022`
- Summary: Recorded a no-secret production trial start precheck after PR #32 merged to main, proving default_branch_ref and trial_start_workflow_ref while keeping launch blocked on confirmation, runner, SMTP, Release, and workflow variable refs.
- Model delta: No arXiv Daily Push runtime model behavior change.
- Parameter delta: No active parameter value change.
- Tests: curl GitHub PR #32 metadata, curl GitHub Actions runs for main merge commit df28c70f255d4db0cabf15d6555ce34a8b2fa560, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_trial_start_precheck PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push plan-production-launch --path . --pr-info <pr32 metadata> --generated-at 2026-06-22T04:55:00+10:00 --expected-head-sha 426709648fde32bbaf0d0a1f4f6006318891f5f2 --default-branch-ref git://LinzeColin/CodexProject/main@df28c70f255d4db0cabf15d6555ce34a8b2fa560 --trial-start-workflow-ref github-actions://LinzeColin/CodexProject/.github/workflows/arxiv-daily-push-trial-start.yml@main#df28c70f255d4db0cabf15d6555ce34a8b2fa560 --json, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_precheck_target_tests PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_production_launch.py arxiv-daily-push/tests/test_trial_start_workflow.py arxiv-daily-push/tests/test_cli.py -q, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_precheck_arxiv_tests PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_precheck_root_tests2 python3 -m unittest discover -s tests/governance -p 'test_*.py' -q, +4 more
- Evidence: governance/run_manifests/ADP-PHASE11-PRODUCTION-TRIAL-START-PRECHECK-20260622.json, arxiv-daily-push/docs/phase_records/PHASE_11_PRODUCTION_TRIAL_START_PRECHECK.md, arxiv-daily-push/docs/runbooks/PRODUCTION_TRIAL_RUNBOOK.md
- Result: `pass`
- Rollback: Remove the production trial start precheck phase record, run manifest, development event, runbook/status/delivery task updates, and regenerated governance dashboard/status files.

## Current Blockers

Semantic coverage is machine_verified with 152 machine-checked active parameters and all 31 active formulas; no active semantic registry rows remain HUMAN_REVIEW_REQUIRED under `GOV-SEMANTIC-ADP-001`. PR #32 is merged to `main` at merge commit `df28c70f255d4db0cabf15d6555ce34a8b2fa560` and main Project Governance CI run `27913796642` passed; `default_branch_ref` and `trial_start_workflow_ref` are now durable, but production launch remains blocked by missing explicit launch confirmation and missing durable readiness refs for `runner_ref`, `smtp_secret_ref`, `release_target_ref`, and `workflow_vars_ref`; production acceptance still requires a passing default-branch trial start workflow run, live source ingest pass on the runner, real SMTP and Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries.

## Semantic Coverage

- Status: `machine_verified`
- Target: Add machine extractors for arXiv Daily Push active parameter values and formula implementation fingerprints without changing runtime behavior.
- Evidence/rollout: acceptance_id: ACC-SEMANTIC-ADP-001; evidence_ref: governance/run_manifests/GOV-SEMANTIC-ADP-EXTRACT-005.json; owner: project owner; rationale: GOV-SEMANTIC-ADP-001 now machine-checks all 152 active parameters and all 31 active formulas; no active semantic registry rows remain HUMAN_REVIEW_REQUIRED.; status: machine_verified; target: Add machine extractors for arXiv Daily Push active parameter values and formula implementation fingerprints without changing runtime behavior.; +1 more

## Next Task

`ADP-PHASE11-PRODUCTION-TRIAL-START-022` - Provision durable production refs and run the default-branch trial start workflow before 30-day acceptance evidence can begin.

- Status: `blocked`
- Acceptance: ADP-ACC-PHASE11-PRODUCTION-TRIAL-START
- Selection rationale: status=blocked; phase=E; current_phase=E; unmet_dependencies=none; score=127

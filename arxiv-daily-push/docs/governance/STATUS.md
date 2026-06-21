# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.24`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +27`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +27`
- Current iteration: `ITER-20260621-043`
- Current phase: `E`
- Current gate: `ADP-PHASE11-PRODUCTION-TRIAL-START-BLOCKED`
- Model count: `30`
- Formula count: `32`
- Parameter count: `164`
- Task count: `38`
- Unbound event count: `50`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `0`
- Semantic coverage: `machine_verified`
- Semantic rollout task: `GOV-SEMANTIC-ADP-001`

## Latest Run

- Event: `EVENT-20260622-ADP-050`
- Task: `ADP-PHASE11-TRIAL-START-LAUNCH-PREFLIGHT-027`
- Summary: Updated the default-branch trial-start workflow so production refs discovery and launch readiness run after production preflight and before live source, SMTP, Release, or trial-start gate work.
- Model delta: No new runtime model; MOD-ADP-028 now requires production refs discovery and launch readiness before trial-start workflow source, SMTP, Release, or start-gate work.
- Parameter delta: Updated PARAM-ADP-145 artifact coverage and added PARAM-ADP-164 for trial-start launch preflight ordering.
- Tests: PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_trial_launch_focus PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_trial_start_workflow.py arxiv-daily-push/tests/test_production_launch.py arxiv-daily-push/tests/test_cli.py -q, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_trial_launch_cli PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push plan-trial-start-workflow --path . --generated-at 2026-06-22T22:00:00+10:00 --json, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_trial_launch_semantic python3 scripts/validate_semantic_extractors.py arxiv-daily-push, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_trial_launch_project python3 scripts/validate_project_governance.py --project arxiv-daily-push, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_trial_launch_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_trial_launch_arxiv PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q, +4 more
- Evidence: governance/run_manifests/ADP-PHASE11-TRIAL-START-LAUNCH-PREFLIGHT-20260622.json, arxiv-daily-push/docs/phase_records/PHASE_11_TRIAL_START_LAUNCH_PREFLIGHT.md, .github/workflows/arxiv-daily-push-trial-start.yml, arxiv-daily-push/src/arxiv_daily_push/trial_start_workflow.py, arxiv-daily-push/tests/test_trial_start_workflow.py, arxiv-daily-push/docs/runbooks/PRODUCTION_TRIAL_RUNBOOK.md
- Result: `pass`
- Rollback: Remove trial-start workflow production refs and launch precheck steps, revert workflow contract checks, remove PARAM-ADP-164 and related governance records, and restore version 0.11.23.

## Current Blockers

Semantic coverage is machine_verified with 163 machine-checked active parameters and all 32 active formulas; no active semantic registry rows remain HUMAN_REVIEW_REQUIRED under `GOV-SEMANTIC-ADP-001`. Production refs provisioning now has a no-secret owner-fillable template plus a GitHub metadata discovery command for provisioned runners, trial-start/scheduled production workflows declare machine-checked `contents: write` permission for controlled draft Release evidence, and trial-start now runs production refs discovery plus launch readiness before source, SMTP, Release, or start-gate work. Production launch remains blocked by missing owner-provisioned durable readiness refs for `runner_ref`, `smtp_secret_ref`, `release_target_ref`, and `workflow_vars_ref`, missing explicit launch confirmation, and missing default-branch trial-start run evidence. Production acceptance still requires a passing default-branch trial start workflow run, live source ingest pass on the runner, real SMTP and Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries.

## Semantic Coverage

- Status: `machine_verified`
- Target: Add machine extractors for arXiv Daily Push active parameter values and formula implementation fingerprints without changing runtime behavior.
- Evidence/rollout: acceptance_id: ACC-SEMANTIC-ADP-001; evidence_ref: governance/run_manifests/GOV-SEMANTIC-ADP-EXTRACT-005.json; owner: project owner; rationale: GOV-SEMANTIC-ADP-001 now machine-checks all 152 active parameters and all 31 active formulas; no active semantic registry rows remain HUMAN_REVIEW_REQUIRED.; status: machine_verified; target: Add machine extractors for arXiv Daily Push active parameter values and formula implementation fingerprints without changing runtime behavior.; +1 more

## Next Task

`ADP-PHASE11-PRODUCTION-TRIAL-START-022` - Provision durable production refs and run the default-branch trial start workflow before 30-day acceptance evidence can begin.

- Status: `blocked`
- Acceptance: ADP-ACC-PHASE11-PRODUCTION-TRIAL-START
- Selection rationale: status=blocked; phase=E; current_phase=E; unmet_dependencies=none; score=127

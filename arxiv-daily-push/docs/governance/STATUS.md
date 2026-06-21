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
- Current iteration: `ITER-20260621-032`
- Current phase: `E`
- Current gate: `ADP-PHASE11-POST-MERGE-LAUNCH-AUDIT-PASS`
- Model count: `29`
- Formula count: `31`
- Parameter count: `153`
- Task count: `32`
- Unbound event count: `39`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `0`
- Semantic coverage: `planned`
- Semantic rollout task: `GOV-SEMANTIC-ADP-001`

## Latest Run

- Event: `EVENT-20260622-ADP-039`
- Task: `ADP-PHASE11-POST-MERGE-LAUNCH-AUDIT-021`
- Summary: Recorded the post-merge launch audit after PR #14 merged to main; PR/default-branch gates now pass while external durable refs and launch confirmation still block production launch.
- Model delta: No runtime model behavior change.
- Parameter delta: No active parameter value change.
- Tests: PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_postmerge_launch_current PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push plan-production-launch --path . --pr-info /tmp/adp_pr14_merged_current.json --generated-at 2026-06-22T13:05:00+10:00 --expected-head-sha ff4490159d49121d4008caa49c47a83de4dfa4b3 --json, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_postmerge_unit_final PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_postmerge_root_final python3 -m unittest discover -s tests/governance -p 'test_*.py' -q, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_postmerge_project_final python3 scripts/validate_project_governance.py --project arxiv-daily-push, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_postmerge_dashboard_final python3 scripts/generate_governance_dashboard.py --write, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_postmerge_changed_final python3 scripts/validate_project_governance.py --changed-only --enforce-sync --semantic --base-ref origin/main, +3 more
- Evidence: arxiv-daily-push/docs/phase_records/PHASE_11_POST_MERGE_LAUNCH_AUDIT.md, governance/run_manifests/ADP-PHASE11-POST-MERGE-LAUNCH-AUDIT-20260622.json
- Result: `pass`
- Rollback: Revert the post-merge audit phase record, delivery task, ledger/status/runbook updates, run manifest, event record, and generated dashboard/status changes.

## Current Blockers

PR #14 is merged to `main`; production launch remains blocked by missing explicit launch confirmation and missing durable readiness refs for `default_branch_ref`, `runner_ref`, `smtp_secret_ref`, `release_target_ref`, `workflow_vars_ref`, and `trial_start_workflow_ref`; no GitHub Actions workflow runs or combined status checks exist for merge commit `9616264221cecc8077fc862692ec6025f1e4872b`; semantic coverage remains planned and not machine verified; production acceptance still requires a passing default-branch trial start workflow run, live source ingest pass on the runner, real SMTP and Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries.

## Semantic Coverage

- Status: `planned`
- Target: Add machine extractors for arXiv Daily Push active parameter values and formula implementation fingerprints without changing runtime behavior.
- Evidence/rollout: acceptance_id: ACC-SEMANTIC-ADP-001; evidence_ref: governance/run_manifests/GOV-SEMANTIC-ADP-PLANNED-001.json; owner: project owner; rationale: Main branch governance now requires every required project to carry a semantic coverage rollout contract. arXiv Daily Push does not yet claim machine-verified semantic extraction, so coverage remains planned and task-bound.; status: planned; target: Add machine extractors for arXiv Daily Push active parameter values and formula implementation fingerprints without changing runtime behavior.; +1 more

## Next Task

`GOV-SEMANTIC-ADP-001` - Plan machine semantic coverage for arXiv Daily Push active parameter values and formula implementation fingerprints under the latest CodexProject governance standard.

- Status: `planned`
- Acceptance: ACC-SEMANTIC-ADP-001
- Selection rationale: status=planned; phase=E; current_phase=E; unmet_dependencies=none; score=112

# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.23`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +27`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +27`
- Current iteration: `ITER-20260621-042`
- Current phase: `E`
- Current gate: `ADP-PHASE11-PRODUCTION-TRIAL-START-BLOCKED`
- Model count: `30`
- Formula count: `32`
- Parameter count: `163`
- Task count: `37`
- Unbound event count: `49`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `0`
- Semantic coverage: `machine_verified`
- Semantic rollout task: `GOV-SEMANTIC-ADP-001`

## Latest Run

- Event: `EVENT-20260622-ADP-049`
- Task: `ADP-PHASE11-PRODUCTION-REFS-GITHUB-DISCOVERY-026`
- Summary: Added a no-secret GitHub Actions metadata discovery command so a provisioned private runner can build production refs readiness reports from runner labels, secret names, Release target, and workflow variable names without logging secret values or gh output.
- Model delta: No new runtime model; MOD-ADP-030 now includes no-secret GitHub metadata discovery for production refs readiness input.
- Parameter delta: Added PARAM-ADP-163 for the default GitHub repository used by production refs metadata discovery.
- Tests: PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_github_refs_focus PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_production_refs.py arxiv-daily-push/tests/test_production_launch.py arxiv-daily-push/tests/test_cli.py -q, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_github_refs_cli PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push discover-production-refs --generated-at 2026-06-22T21:00:00+10:00 --json >/tmp/codex_adp_github_refs_discovery.json; rc=$?; python3 -m json.tool /tmp/codex_adp_github_refs_discovery.json >/tmp/codex_adp_github_refs_discovery.pretty.json, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_github_refs_semantic python3 scripts/validate_semantic_extractors.py arxiv-daily-push, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_github_refs_project python3 scripts/validate_project_governance.py --project arxiv-daily-push, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_github_refs_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_github_refs_arxiv PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q, +4 more
- Evidence: governance/run_manifests/ADP-PHASE11-PRODUCTION-REFS-GITHUB-DISCOVERY-20260622.json, arxiv-daily-push/docs/phase_records/PHASE_11_PRODUCTION_REFS_GITHUB_DISCOVERY.md, arxiv-daily-push/src/arxiv_daily_push/production_refs.py, arxiv-daily-push/tests/test_production_refs.py, arxiv-daily-push/docs/runbooks/PRODUCTION_TRIAL_RUNBOOK.md
- Result: `pass`
- Rollback: Remove GitHub metadata discovery functions, CLI command, tests, runbook/phase record/governance updates, and restore version 0.11.22.

## Current Blockers

Semantic coverage is machine_verified with 162 machine-checked active parameters and all 32 active formulas; no active semantic registry rows remain HUMAN_REVIEW_REQUIRED under `GOV-SEMANTIC-ADP-001`. Production refs provisioning now has a no-secret owner-fillable template plus a GitHub metadata discovery command for provisioned runners, and trial-start/scheduled production workflows declare machine-checked `contents: write` permission for controlled draft Release evidence while Release upload remains disabled by default. Production launch remains blocked by missing owner-provisioned durable readiness refs for `runner_ref`, `smtp_secret_ref`, `release_target_ref`, and `workflow_vars_ref`, missing explicit launch confirmation, and missing default-branch trial-start run evidence. Production acceptance still requires a passing default-branch trial start workflow run, live source ingest pass on the runner, real SMTP and Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries.

## Semantic Coverage

- Status: `machine_verified`
- Target: Add machine extractors for arXiv Daily Push active parameter values and formula implementation fingerprints without changing runtime behavior.
- Evidence/rollout: acceptance_id: ACC-SEMANTIC-ADP-001; evidence_ref: governance/run_manifests/GOV-SEMANTIC-ADP-EXTRACT-005.json; owner: project owner; rationale: GOV-SEMANTIC-ADP-001 now machine-checks all 152 active parameters and all 31 active formulas; no active semantic registry rows remain HUMAN_REVIEW_REQUIRED.; status: machine_verified; target: Add machine extractors for arXiv Daily Push active parameter values and formula implementation fingerprints without changing runtime behavior.; +1 more

## Next Task

`ADP-PHASE11-PRODUCTION-TRIAL-START-022` - Provision durable production refs and run the default-branch trial start workflow before 30-day acceptance evidence can begin.

- Status: `blocked`
- Acceptance: ADP-ACC-PHASE11-PRODUCTION-TRIAL-START
- Selection rationale: status=blocked; phase=E; current_phase=E; unmet_dependencies=none; score=127

# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.27`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +28`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +28`
- Current iteration: `ITER-20260621-046`
- Current phase: `E`
- Current gate: `ADP-PHASE11-TWO-DAY-SIMULATION-PASS`
- Model count: `31`
- Formula count: `33`
- Parameter count: `169`
- Task count: `41`
- Unbound event count: `53`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `0`
- Semantic coverage: `machine_verified`
- Semantic rollout task: `GOV-SEMANTIC-ADP-001`

## Latest Run

- Event: `EVENT-20260622-ADP-053`
- Task: `ADP-PHASE11-TWO-DAY-SIMULATION-030`
- Summary: Added and ran a no-real-side-effect two-day simulation acceptance gate for the updated Phase 11 goal.
- Model delta: Added MOD-ADP-031 adp-two-day-simulation-v1 for the updated two-day simulation acceptance path.
- Parameter delta: Added PARAM-ADP-167 through PARAM-ADP-169 for the simulation model id, required day count, and no-production-claim safety flags.
- Tests: PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_two_day_focus PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_simulation.py -q, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_two_day_cli PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push run-two-day-simulation --path . --generated-at 2026-06-22T06:30:00+10:00 --start-date 2026-06-22 --json, python3 -m json.tool /Users/linzezhang/Documents/Codex/2026-06-21/readme-first-md-01-execution-contract/outputs/arxiv_daily_push_two_day_simulation_20260622.json, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_two_day_arxiv1 PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_two_day_semantic2 python3 scripts/validate_semantic_extractors.py arxiv-daily-push, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_two_day_project3 python3 scripts/validate_project_governance.py --project arxiv-daily-push, +4 more
- Evidence: governance/run_manifests/ADP-PHASE11-TWO-DAY-SIMULATION-20260622.json, arxiv-daily-push/docs/phase_records/PHASE_11_TWO_DAY_SIMULATION.md, arxiv-daily-push/src/arxiv_daily_push/simulation.py, arxiv-daily-push/tests/test_simulation.py, arxiv-daily-push/docs/runbooks/PRODUCTION_TRIAL_RUNBOOK.md
- Result: `pass`
- Rollback: Remove the two-day simulation module, CLI command, tests, MOD-ADP-031, FORM-ADP-033, PARAM-ADP-167 through PARAM-ADP-169, phase record, manifest, governance updates, and restore version 0.11.26.

## Current Blockers

The updated local Phase 11 two-day simulation gate passes with two consecutive mocked scheduled daily runs, two trial ledger appends, no real SMTP, no real Release upload, no network fetch, no Codex auth read, and no production acceptance claim. Semantic coverage is machine_verified with 168 machine-checked active parameters and all 33 active formulas; no active semantic registry rows remain HUMAN_REVIEW_REQUIRED under `GOV-SEMANTIC-ADP-001`. Production launch remains blocked by missing owner-provisioned durable readiness refs for `runner_ref`, `smtp_secret_ref`, `release_target_ref`, and `workflow_vars_ref`, missing explicit launch confirmation, missing passing owner-run provisioning audit and artifact review evidence, and missing default-branch trial-start run evidence. Full production acceptance still requires owner-provisioned runner/secret/Release/workflow refs, a passing default-branch trial start workflow run, live source ingest pass on the runner, real SMTP and Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries if the project chooses the real production-trial path later.

## Semantic Coverage

- Status: `machine_verified`
- Target: Add machine extractors for arXiv Daily Push active parameter values and formula implementation fingerprints without changing runtime behavior.
- Evidence/rollout: acceptance_id: ACC-SEMANTIC-ADP-001; evidence_ref: governance/run_manifests/GOV-SEMANTIC-ADP-EXTRACT-005.json; owner: project owner; rationale: GOV-SEMANTIC-ADP-001 now machine-checks all 152 active parameters and all 31 active formulas; no active semantic registry rows remain HUMAN_REVIEW_REQUIRED.; status: machine_verified; target: Add machine extractors for arXiv Daily Push active parameter values and formula implementation fingerprints without changing runtime behavior.; +1 more

## Next Task

`ADP-PHASE11-PRODUCTION-TRIAL-START-022` - Provision durable production refs and run the default-branch trial start workflow before 30-day acceptance evidence can begin.

- Status: `blocked`
- Acceptance: ADP-ACC-PHASE11-PRODUCTION-TRIAL-START
- Selection rationale: status=blocked; phase=E; current_phase=E; unmet_dependencies=none; score=127

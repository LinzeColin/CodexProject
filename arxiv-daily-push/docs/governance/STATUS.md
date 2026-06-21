# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.22`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +27`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +27`
- Current iteration: `ITER-20260621-041`
- Current phase: `E`
- Current gate: `ADP-PHASE11-PRODUCTION-TRIAL-START-BLOCKED`
- Model count: `30`
- Formula count: `32`
- Parameter count: `162`
- Task count: `36`
- Unbound event count: `48`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `0`
- Semantic coverage: `machine_verified`
- Semantic rollout task: `GOV-SEMANTIC-ADP-001`

## Latest Run

- Event: `EVENT-20260622-ADP-048`
- Task: `ADP-PHASE11-PRODUCTION-REFS-TEMPLATE-025`
- Summary: Added a no-secret owner-fillable production refs input template and CLI command so runner, SMTP secret-name, Release target, and workflow variable refs can be prepared without hand-writing the JSON contract or exposing secret values.
- Model delta: No new runtime model; MOD-ADP-030 now includes no-secret template generation for production refs readiness input.
- Parameter delta: Added PARAM-ADP-162 for required production refs template sections.
- Tests: PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_refs_template_focus PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_production_refs.py arxiv-daily-push/tests/test_production_launch.py arxiv-daily-push/tests/test_cli.py -q, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_refs_template_cli PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push print-production-refs-template --runner-label arxiv-daily-push-prod --release-target adp-private | python3 -m json.tool >/tmp/codex_adp_refs_template.json, PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_refs_template_plan PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push plan-production-refs --readiness-input /tmp/codex_adp_refs_template.json --generated-at 2026-06-22T20:00:00+10:00 --json >/tmp/codex_adp_refs_template_report.json; test "$?" -eq 2, python3 -m json.tool arxiv-daily-push/config/examples/production_refs.input.example.json >/dev/null, PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_semantic_extractors.py arxiv-daily-push, PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project arxiv-daily-push, +3 more
- Evidence: governance/run_manifests/ADP-PHASE11-PRODUCTION-REFS-TEMPLATE-20260622.json, arxiv-daily-push/docs/phase_records/PHASE_11_PRODUCTION_REFS_TEMPLATE.md, arxiv-daily-push/config/examples/production_refs.input.example.json, arxiv-daily-push/src/arxiv_daily_push/production_refs.py, arxiv-daily-push/docs/runbooks/PRODUCTION_TRIAL_RUNBOOK.md
- Result: `pass`
- Rollback: Remove the template function, CLI command, example JSON, tests, runbook/phase record/governance updates, and restore version 0.11.21.

## Current Blockers

Semantic coverage is machine_verified with 161 machine-checked active parameters and all 32 active formulas; no active semantic registry rows remain HUMAN_REVIEW_REQUIRED under `GOV-SEMANTIC-ADP-001`. Production refs provisioning now has a no-secret owner-fillable template, and trial-start/scheduled production workflows declare machine-checked `contents: write` permission for controlled draft Release evidence while Release upload remains disabled by default. Production launch remains blocked by missing owner-provisioned durable readiness refs for `runner_ref`, `smtp_secret_ref`, `release_target_ref`, and `workflow_vars_ref`, missing explicit launch confirmation, and missing default-branch trial-start run evidence. Production acceptance still requires a passing default-branch trial start workflow run, live source ingest pass on the runner, real SMTP and Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries.

## Semantic Coverage

- Status: `machine_verified`
- Target: Add machine extractors for arXiv Daily Push active parameter values and formula implementation fingerprints without changing runtime behavior.
- Evidence/rollout: acceptance_id: ACC-SEMANTIC-ADP-001; evidence_ref: governance/run_manifests/GOV-SEMANTIC-ADP-EXTRACT-005.json; owner: project owner; rationale: GOV-SEMANTIC-ADP-001 now machine-checks all 152 active parameters and all 31 active formulas; no active semantic registry rows remain HUMAN_REVIEW_REQUIRED.; status: machine_verified; target: Add machine extractors for arXiv Daily Push active parameter values and formula implementation fingerprints without changing runtime behavior.; +1 more

## Next Task

`ADP-PHASE11-PRODUCTION-TRIAL-START-022` - Provision durable production refs and run the default-branch trial start workflow before 30-day acceptance evidence can begin.

- Status: `blocked`
- Acceptance: ADP-ACC-PHASE11-PRODUCTION-TRIAL-START
- Selection rationale: status=blocked; phase=E; current_phase=E; unmet_dependencies=none; score=127

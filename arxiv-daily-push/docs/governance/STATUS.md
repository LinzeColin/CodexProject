# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.9.0`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +6`
- Parameter profile versions: `adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, adp-evidence-parameters:adp-evidence-parameters-v1, +6`
- Current iteration: `ITER-20260621-009`
- Current phase: `D`
- Current gate: `ADP-PHASE9-LOCAL-PIPELINE-PASS`
- Model count: `9`
- Formula count: `11`
- Parameter count: `47`
- Task count: `10`
- Unbound event count: `16`

## Latest Run

- Event: `EVENT-20260621-ADP-016`
- Task: `ADP-PHASE9-LOCAL-PIPELINE-001`
- Summary: Implemented Phase 9 local daily dry-run orchestration through RunRecord completion and email preview without scheduler, Release upload, SMTP send, or media output.
- Model delta: `Activated MOD-ADP-009 deterministic local daily dry-run pipeline.`
- Parameter delta: `Activated PARAM-ADP-045 through PARAM-ADP-047 as pipeline parameters.`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase9_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase9_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase9_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase9_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase9_dashboard python3 scripts/generate_governance_dashboard.py --write', 'git diff --check']`
- Evidence: `['arxiv-daily-push/docs/phase_records/PHASE_09.md', 'arxiv-daily-push/src/arxiv_daily_push/pipeline.py', 'arxiv-daily-push/tests/test_pipeline.py', 'arxiv-daily-push/tests/fixtures/pipeline_input.json']`
- Result: `pass`
- Rollback: Revert Phase 9 pipeline code and governance updates.

## Current Blockers

Later phases still need runner/release/email dry-run handoff and 30-day acceptance evidence.

## Next Task

`ADP-PHASE10-RUNNER-RELEASE-EMAIL-001`

# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.10.0`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +7`
- Parameter profile versions: `adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, adp-evidence-parameters:adp-evidence-parameters-v1, +7`
- Current iteration: `ITER-20260621-010`
- Current phase: `D`
- Current gate: `ADP-PHASE10-RUNNER-RELEASE-EMAIL-PASS`
- Model count: `10`
- Formula count: `12`
- Parameter count: `50`
- Task count: `11`
- Unbound event count: `17`

## Latest Run

- Event: `EVENT-20260621-ADP-017`
- Task: `ADP-PHASE10-RUNNER-RELEASE-EMAIL-001`
- Summary: Implemented Phase 10 runner/release/email dry-run handoff while keeping scheduler, GitHub Actions runner, unattended execution, Release upload, and real SMTP send disabled.
- Model delta: `Activated MOD-ADP-010 deterministic runner/release/email dry-run handoff gate.`
- Parameter delta: `Activated PARAM-ADP-048 through PARAM-ADP-050 as handoff parameters.`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase10_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase10_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase10_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase10_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase10_dashboard python3 scripts/generate_governance_dashboard.py --write', 'git diff --check']`
- Evidence: `['arxiv-daily-push/docs/phase_records/PHASE_10.md', 'arxiv-daily-push/src/arxiv_daily_push/handoff.py', 'arxiv-daily-push/tests/test_handoff.py', 'arxiv-daily-push/tests/fixtures/pipeline_input.json']`
- Result: `pass`
- Rollback: Revert Phase 10 handoff code, tests, and governance updates.

## Current Blockers

Final acceptance still needs handoff packaging; live 30-day operational evidence is not claimed.

## Next Task

`ADP-PHASE11-ACCEPTANCE-HANDOFF-001`

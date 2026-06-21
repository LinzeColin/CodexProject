# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.5.0`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +2`
- Parameter profile versions: `adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, adp-evidence-parameters:adp-evidence-parameters-v1, +2`
- Current iteration: `ITER-20260621-005`
- Current phase: `C`
- Current gate: `ADP-PHASE5-EVIDENCE-GATE-PASS`
- Model count: `5`
- Formula count: `7`
- Parameter count: `34`
- Task count: `7`
- Unbound event count: `12`

## Latest Run

- Event: `EVENT-20260621-ADP-012`
- Task: `ADP-PHASE5-EVIDENCE-GATE-001`
- Summary: Validated Phase 5 Claim Ledger publication gate with project tests, root governance tests, schema parse, project governance, changed-only sync, dashboard generation, and diff hygiene.
- Model delta: `Activated MOD-ADP-003 deterministic Claim Ledger publication gate.`
- Parameter delta: `Activated PARAM-ADP-017 and PARAM-ADP-018 as evidence gate parameters.`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase5_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase5_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase5_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase5_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase5_dashboard python3 scripts/generate_governance_dashboard.py --write', 'git diff --check']`
- Evidence: `['arxiv-daily-push/docs/phase_records/PHASE_05.md', 'arxiv-daily-push/src/arxiv_daily_push/evidence_gate.py', 'arxiv-daily-push/tests/test_evidence_gate.py', 'arxiv-daily-push/tests/fixtures/claim_ledger_input.json']`
- Result: `pass`
- Rollback: Revert the Phase 5 commit and restore arxiv-daily-push to version 0.4.0.

## Current Blockers

Later phases still need lesson generation, real mail transport validation, and later media/runner resource readiness.

## Next Task

`ADP-PHASE6-LESSON-001`

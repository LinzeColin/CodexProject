# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.2.0`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-planned-v1, MOD-ADP-003:adp-claim-gate-planned-v1, +1`
- Parameter profile versions: `adp-contract-parameters:adp-contract-parameters-v1, adp-evidence-parameters:adp-evidence-parameters-planned-v1, adp-foundation-parameters:adp-foundation-parameters-v1, +1`
- Current iteration: `ITER-20260621-002`
- Current phase: `B`
- Current gate: `ADP-PHASE2-DATA-CONTRACTS-PASS`
- Model count: `4`
- Formula count: `6`
- Parameter count: `28`
- Task count: `5`
- Unbound event count: `6`

## Latest Run

- Event: `EVENT-20260621-ADP-006`
- Task: `ADP-PHASE2-DATA-CONTRACTS-001`
- Summary: Validated Phase 2 generic data contracts and RunRecord state machine with project tests, schema parse, root governance tests, project governance, changed-only sync, dashboard generation, and diff hygiene.
- Model delta: `no model behavior change beyond MOD-ADP-004 Phase 2 contract/state gate; validation evidence recorded`
- Parameter delta: `no parameter value change beyond PARAM-ADP-020 through PARAM-ADP-028; validation evidence recorded`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache python3 scripts/generate_governance_dashboard.py --write', 'git diff --check']`
- Evidence: `['governance/run_manifests/ADP-PHASE2-DATA-CONTRACTS-20260621.json', 'arxiv-daily-push/docs/phase_records/PHASE_02.md', 'arxiv-daily-push/tests/test_contracts.py', 'arxiv-daily-push/tests/test_state_machine.py', 'arxiv-daily-push/src/arxiv_daily_push/contracts.py', 'arxiv-daily-push/src/arxiv_daily_push/state_machine.py']`
- Result: `pass`
- Rollback: Revert Phase 2 commit and restore arxiv-daily-push to version 0.1.0.

## Current Blockers

Later phases still need arXiv network ingest/ranking/evidence implementation, real mail transport validation, and later media/runner resource readiness.

## Next Task

`ADP-PHASE4-RANKING-001`

# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.3.0`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-planned-v1, MOD-ADP-003:adp-claim-gate-planned-v1, +2`
- Parameter profile versions: `adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, adp-evidence-parameters:adp-evidence-parameters-planned-v1, +2`
- Current iteration: `ITER-20260621-003`
- Current phase: `B`
- Current gate: `ADP-PHASE3-ARXIV-ADAPTER-PASS`
- Model count: `5`
- Formula count: `7`
- Parameter count: `34`
- Task count: `6`
- Unbound event count: `8`

## Latest Run

- Event: `EVENT-20260621-ADP-008`
- Task: `ADP-PHASE3-ARXIV-ADAPTER-001`
- Summary: Recorded final local validation pass for Phase 3 arXiv Atom SourceAdapter, including project tests, root governance tests, changed-only sync, dashboard generation, and diff hygiene.
- Model delta: `added MOD-ADP-005 active arXiv Atom source adapter`
- Parameter delta: `added PARAM-ADP-029 through PARAM-ADP-034 for arXiv adapter parameters`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache python3 scripts/generate_governance_dashboard.py --write', 'git diff --check']`
- Evidence: `['governance/run_manifests/ADP-PHASE3-ARXIV-ADAPTER-20260621.json', 'arxiv-daily-push/docs/phase_records/PHASE_03.md', 'arxiv-daily-push/src/arxiv_daily_push/arxiv_adapter.py', 'arxiv-daily-push/tests/test_arxiv_adapter.py', 'arxiv-daily-push/tests/fixtures/arxiv_atom_sample.xml']`
- Result: `pass`
- Rollback: Revert Phase 3 adapter code and governance updates; restore version 0.2.0.

## Current Blockers

Later phases still need arXiv network ingest/ranking/evidence implementation, real mail transport validation, and later media/runner resource readiness.

## Next Task

`ADP-PHASE4-RANKING-001`

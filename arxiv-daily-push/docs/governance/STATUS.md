# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.7.0`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +4`
- Parameter profile versions: `adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, adp-evidence-parameters:adp-evidence-parameters-v1, +4`
- Current iteration: `ITER-20260621-007`
- Current phase: `D`
- Current gate: `ADP-PHASE7-TTS-DRY-RUN-PASS`
- Model count: `7`
- Formula count: `9`
- Parameter count: `40`
- Task count: `8`
- Unbound event count: `14`

## Latest Run

- Event: `EVENT-20260621-ADP-014`
- Task: `ADP-PHASE7-TTS-001`
- Summary: Implemented Phase 7 narration/TTS-ready dry-run JSON generation and resource gate while keeping audio synthesis, model downloads, and audio writes blocked.
- Model delta: `Activated MOD-ADP-007 deterministic narration and TTS dry-run gate.`
- Parameter delta: `Activated PARAM-ADP-037 through PARAM-ADP-040 as narration/TTS dry-run parameters.`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase7_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase7_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase7_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase7_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase7_dashboard python3 scripts/generate_governance_dashboard.py --write', 'git diff --check']`
- Evidence: `['arxiv-daily-push/docs/phase_records/PHASE_07.md', 'arxiv-daily-push/src/arxiv_daily_push/narration.py', 'arxiv-daily-push/tests/test_narration.py', 'arxiv-daily-push/tests/fixtures/narration_input.json']`
- Result: `pass`
- Rollback: Revert the Phase 7 commit and restore arxiv-daily-push to version 0.6.0.

## Current Blockers

Later phases still need video/media QA, daily runner automation, real mail transport validation, and release readiness.

## Next Task

`ADP-PHASE8-VIDEO-001`

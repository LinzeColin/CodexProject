# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.1.0`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-planned-v1, MOD-ADP-003:adp-claim-gate-planned-v1`
- Parameter profile versions: `adp-evidence-parameters:adp-evidence-parameters-planned-v1, adp-foundation-parameters:adp-foundation-parameters-v1, adp-ranking-parameters:adp-ranking-parameters-planned-v1`
- Current iteration: `ITER-20260621-001`
- Current phase: `A`
- Current gate: `ADP-PHASE1-FOUNDATION-PASS`
- Model count: `3`
- Formula count: `4`
- Parameter count: `19`
- Task count: `5`
- Unbound event count: `4`

## Latest Run

- Event: `EVENT-20260621-ADP-004`
- Task: `ADP-PHASE1-FOUNDATION-001`
- Summary: Recorded local validation pass for arXiv Daily Push Phase 1 foundation, including project tests, root governance tests, changed-only sync, doctor, and email dry-run evidence.
- Model delta: `no runtime model behavior change beyond initial Phase 1 foundation; local validation evidence recorded`
- Parameter delta: `no parameter value change beyond initial Phase 1 foundation; local validation evidence recorded`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'python3 -m json.tool arxiv-daily-push/schemas/source_item.schema.json', 'python3 -m json.tool arxiv-daily-push/schemas/run_record.schema.json', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache python3 scripts/validate_project_governance.py --changed-only', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache python3 scripts/generate_governance_dashboard.py --write', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push doctor --json', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push render-email --status PASS --run-id ADP-PHASE1-FOUNDATION-20260621 --summary 'Phase 1 foundation validated' --date 2026-06-21", 'git diff --check']`
- Evidence: `['governance/run_manifests/ADP-PHASE1-FOUNDATION-20260621.json', 'tests/governance/test_project_governance_validator.py', 'arxiv-daily-push/docs/phase_records/PHASE_01.md', 'arxiv-daily-push/docs/governance/STATUS.md']`
- Result: `pass`
- Rollback: Remove arxiv-daily-push/, remove ADP-PHASE1-FOUNDATION-20260621 manifest, and restore README.md plus governance/projects.yaml.

## Current Blockers

Later phases need Node/npm/gh/ffmpeg/docker, more disk, runner readiness, and real mail transport validation.

## Next Task

`ADP-PHASE2-DATA-CONTRACTS-001`

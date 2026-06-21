# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.1`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +8`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.1, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +8`
- Current iteration: `ITER-20260621-012`
- Current phase: `E`
- Current gate: `ADP-PHASE11-EVIDENCE-REF-HARDENING-PASS`
- Model count: `11`
- Formula count: `13`
- Parameter count: `56`
- Task count: `12`
- Unbound event count: `19`

## Latest Run

- Event: `EVENT-20260621-ADP-019`
- Task: `ADP-PHASE11-EVIDENCE-REF-HARDENING-002`
- Summary: Hardened Phase 11 production acceptance so true operational evidence flags require non-empty evidence references.
- Model delta: `Updated MOD-ADP-011 to adp-acceptance-v1.1 evidence-reference hardening.`
- Parameter delta: `Added PARAM-ADP-056 as evidence-reference requirement.`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_evidence_ref_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_evidence_ref_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_evidence_ref_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_evidence_ref_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_evidence_ref_dashboard python3 scripts/generate_governance_dashboard.py --write', 'git diff --check']`
- Evidence: `['arxiv-daily-push/docs/phase_records/PHASE_11_EVIDENCE_REF_HARDENING.md', 'arxiv-daily-push/src/arxiv_daily_push/acceptance.py', 'arxiv-daily-push/tests/test_acceptance.py']`
- Result: `pass`
- Rollback: Revert Phase 11 evidence-reference hardening and restore version 0.11.0.

## Current Blockers

Production acceptance still requires real 30-day trial, scheduler, Release, SMTP, and resource evidence; those are not claimed by this handoff.

## Next Task

`UNKNOWN`

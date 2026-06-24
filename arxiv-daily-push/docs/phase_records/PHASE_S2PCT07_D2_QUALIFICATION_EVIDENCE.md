# PHASE S2PCT07 D2 Qualification Evidence

Date: 2026-06-24

## Scope

S2PCT07 adds D2 source-domain qualification and cross-type calibration evidence
after completed S2PCT01-S2PCT06 top-journal, engineering public-signal, and
authoritative report shadow evidence.

This phase records qualification readiness only. It does not claim
`D2_SOURCE_DOMAIN_ACCEPTED`, `STAGE2_PRODUCTION_ACCEPTED`, or
`INTEGRATED_PRODUCTION_ACCEPTED`.

## Evidence

- `adp stage2-d2-source-domain-qualification`
- `MOD-ADP-060`
- `FORM-ADP-062`
- `PARAM-ADP-416` through `PARAM-ADP-423`
- `ACC-S2PCT07-D2`

The qualification report requires:

- passing S2PCT04 top-journal profile evidence
- passing S2PCT05 engineering public-signal evidence
- passing S2PCT06 authoritative report evidence
- 30 unique D2 replay dates with no future leakage or P0/P1 blockers
- at least 48 hours of no-production shadow evidence
- correction and retraction forced-event propagation
- selected, queued, and deferred queue explanations
- full required type coverage across D2 domains with zero calibration spread

## Production Boundary

The following remain false or disabled:

- D2 source-domain acceptance
- formal production inclusion
- Stage 2 production acceptance
- integrated production acceptance
- SMTP transport
- Release upload
- GitHub cloud production schedule
- production queue mutation
- schema migration
- PDF/full-text download
- paid API use
- paywall bypass
- marketing-material acceptance

## Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_s2pct07_focus1 PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_stage2_sources.py -q`
  - Result: 31 tests OK
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_s2pct07_semantic2 PYTHONPATH=scripts:arxiv-daily-push/src python3 scripts/validate_semantic_extractors.py arxiv-daily-push`
  - Result: `semantic_formulas_checked=62`, `semantic_parameters_checked=406`

## Next

Current V7.1 routing advances to `S2PDT01` / legacy `S2P3T01` China C0
national authoritative backbone. S2PD must still run metadata-only source
evidence and keep production acceptance gates closed until P0/P1 and S2PMT07
requirements are satisfied.

# PHASE S2P1T01 - Preprint Source Promotion

Task: `S2P1T01`
Acceptance: `ADP-ACC-S2P1T01-SOURCE-PROMOTION`
Date: 2026-06-24

## Result

Status: `in_progress`

S2P1T01 now has a metadata-only bioRxiv/medRxiv adapter, disabled owner-control
source entries, source-level promotion gates, and a separate shadow daily path.
This does not add bioRxiv or medRxiv to formal production selection yet.

## Implemented

- `preprint_adapter.py` maps public bioRxiv/medRxiv details API JSON into
  generic `SourceItem` records with `source_type=preprint`.
- `stage2_sources.py` adds the S2P1T01 promotion gate and shadow daily runner.
- Source registry and schemas now recognize disabled Stage 2 preprint sources
  while Stage 1 active source remains only `SRC-ARXIV`.
- `global_scan.py` and `lesson.py` can build ROI candidates, claims, lessons,
  and email previews from preprint abstract metadata without arXiv-only
  assumptions.
- CLI commands were added for `fetch-preprint-latest`,
  `stage2-preprint-gate`, and `stage2-preprint-shadow-daily`.

## Live Canary

- bioRxiv fixed historical interval canary passed via curl fallback:
  `biorxiv:10.1101-2023.12.30.573731`.
- medRxiv fixed historical interval canary passed via curl fallback:
  `medrxiv:10.1101-2023.10.21.23297352`.
- One local shadow daily run passed under `/tmp/adp_s2p1_live_20260624`,
  selected the medRxiv source, and wrote a separate shadow queue, ledger, report,
  plain email preview, and HTML email preview.

## Safety

- `formal_production_inclusion=false`
- `github_cloud_schedule_enabled=false`
- `production_schedule_enabled=false`
- `real_smtp_sent=false`
- `release_upload_enabled=false`
- `video_required=false`
- `secret_values_logged=false`

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_s2p1_focus4 PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_preprint_adapter.py arxiv-daily-push/tests/test_stage2_sources.py arxiv-daily-push/tests/test_global_scan.py arxiv-daily-push/tests/test_lesson.py arxiv-daily-push/tests/test_source_registry.py arxiv-daily-push/tests/test_owner_controls.py arxiv-daily-push/tests/test_contracts.py -q
```

Result: `39 tests OK`

Additional verification:

- `python3 -m unittest discover -s arxiv-daily-push/tests -q`: `216 tests OK`
- schema JSON parse: pass
- live bioRxiv and medRxiv fixed-interval canaries: pass
- one S2P1 shadow daily canary: pass

## Remaining Gate

S2P1T01 is not complete yet. The source promotion gate still requires:

- terminal replay over at least 30 unique historical dates,
- no future leakage,
- no duplicate selected canonical papers,
- no P0/P1 blockers,
- 48 hours of shadow-mode evidence,
- no production effect on the accepted Stage 1 arXiv local runner.

## Next

Current task remains `S2P1T01`: run/attach the 30-date terminal replay and
48-hour shadow evidence before marking source promotion complete.

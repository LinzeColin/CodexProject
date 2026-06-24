# PHASE S2P1T01 - Preprint Source Promotion

Task: `S2P1T01`
V7 alias: `S2PBT01`
Acceptance: `ADP-ACC-S2P1T01-SOURCE-PROMOTION`
Date: 2026-06-24

## Result

Status: `in_progress`

S2P1T01 now has a metadata-only bioRxiv/medRxiv adapter, disabled owner-control
source entries, source-level promotion gates, and a separate shadow daily path.
This does not add bioRxiv or medRxiv to formal production selection yet.

Under the V7 route lock, legacy `S2P1T01` is treated as alias `S2PBT01`.
This record does not rewrite historical V6 events. Stage 2 Stop Gate remains
`INTEGRATED_PRODUCTION_ACCEPTED -> DAILY_OPERATION`.

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
  `stage2-preprint-gate`, `stage2-preprint-shadow-daily`, and
  `stage2-preprint-replay-shadow`.
- `stage2_sources.py` now includes a deterministic replay/shadow evidence
  builder for 30 historical as-of dates. It reuses the no-send shadow daily
  path, persists local queue/ledger/report/email-preview artifacts, builds a
  48-hour shadow aggregate, and writes the S2P1 promotion report without
  claiming Stage 2 production acceptance.

## Live Canary

- bioRxiv fixed historical interval canary passed via curl fallback:
  `biorxiv:10.1101-2023.12.30.573731`.
- medRxiv fixed historical interval canary passed via curl fallback:
  `medrxiv:10.1101-2023.10.21.23297352`.
- One local shadow daily run passed under `/tmp/adp_s2p1_live_20260624`,
  selected the medRxiv source, and wrote a separate shadow queue, ledger, report,
  plain email preview, and HTML email preview.

## Replay / Shadow Evidence Builder

- Added `build_s2p1_preprint_replay_shadow_evidence(...)`.
- Added CLI command `stage2-preprint-replay-shadow`.
- Fixture-backed replay test passed for 30 unique historical dates.
- The aggregate report requires:
  - 30/30 successful daily shadow reports,
  - 30 unique dates,
  - real `biorxiv:` or `medrxiv:` source IDs,
  - no future leakage,
  - no duplicate selected source or canonical DOI,
  - no queue/ledger/email persistence break,
  - no P0/P1 blocker,
  - at least 48 hours of shadow coverage,
  - no production side effects.
- The aggregate output explicitly keeps `stage2_production_accepted=false`.

## Real Replay Evidence

One local no-send real replay passed with compact evidence persisted in
`governance/run_manifests/ADP-S2PBT01-REAL-REPLAY-SHADOW-EVIDENCE-20260624.json`.

- date range: `2024-01-01` through `2024-01-30`
- result: `pass`
- success_count: `30/30`
- unique_date_count: `30`
- real_preprint_source_id_count: `30`
- duplicate_selected_count: `0`
- duplicate_canonical_count: `0`
- future_leakage_count: `0`
- queue_continuity_break_count: `0`
- p0_p1_blocker_count: `0`
- shadow_hours: `720.0`
- full local artifact directory: `/tmp/adp_s2p1_replay_real_20260624/state`
- full artifact size: `46M`
- repo-persisted evidence: compact manifest only

## Safety

- `formal_production_inclusion=false`
- `github_cloud_schedule_enabled=false`
- `production_schedule_enabled=false`
- `real_smtp_sent=false`
- `release_upload_enabled=false`
- `video_required=false`
- `secret_values_logged=false`
- `stage2_production_accepted=false`
- `integrated_production_accepted=false`
- `formal_new_source_production_inclusion=false`

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_s2p1_focus4 PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_preprint_adapter.py arxiv-daily-push/tests/test_stage2_sources.py arxiv-daily-push/tests/test_global_scan.py arxiv-daily-push/tests/test_lesson.py arxiv-daily-push/tests/test_source_registry.py arxiv-daily-push/tests/test_owner_controls.py arxiv-daily-push/tests/test_contracts.py -q
```

Result: `41 tests OK`

Replay/shadow builder focused verification:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_s2p1_replay_focus2 PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_stage2_sources.py -q
```

Result: `6 tests OK`

Additional verification:

- `python3 -m unittest discover -s arxiv-daily-push/tests -q`: `218 tests OK`
- schema JSON parse: pass
- live bioRxiv and medRxiv fixed-interval canaries: pass
- one S2P1 shadow daily canary: pass
- real no-send replay/shadow run: `pass`, `30/30`, `shadow_hours=720.0`

## Remaining Gate

S2P1T01 / S2PBT01 is not complete yet. The source evidence gate has passed one
local no-send real replay, but formal source inclusion and Stage 2 production
acceptance remain blocked until the V7 root contract, AGENTS, three baseline
files, and CI contract hash gate are merged and no contract mismatch exists.

Remaining constraints:

- no production effect on the accepted Stage 1 arXiv local runner.
- no SMTP, Release, GitHub schedule, video, PDF, full-text, or formal email
  inclusion.
- no `INTEGRATED_PRODUCTION_ACCEPTED` or `STAGE2_PRODUCTION_ACCEPTED` claim.

## Next

Current task remains `S2PBT01/S2P1T01`: wait for or reconcile the V7 route-lock
contract hash gate, then decide whether the passed no-send real replay evidence
is sufficient for source-level progression without formal production inclusion.

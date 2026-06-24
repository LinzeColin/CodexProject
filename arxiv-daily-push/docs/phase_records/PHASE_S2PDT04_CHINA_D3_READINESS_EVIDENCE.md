# PHASE S2PDT04 China D3 Readiness Evidence

Date: 2026-06-24

## Scope

S2PDT04 / legacy S2P3T04 builds metadata-only China official D3 readiness review evidence after the completed S2PDT01 C0 source foundation, S2PDT02 C1 department source map, and S2PDT03 legal metadata relation shadow.

Covered readiness surfaces:

- 30 distinct replay as-of dates
- 2 distinct no-production shadow dates
- authority evidence references across replay, shadow, and board routes
- B2 policy, B3 frontier, B4 industry, B5 macro, and B6 risk source-to-reading-board routes
- metadata-only and no-production side-effect gates

## Acceptance

Acceptance target: ACC-S2PDT04-D3-CORE.

The report passes only when upstream S2PDT01, S2PDT02, and S2PDT03 reports pass; all replay records pass with `future_leakage_count=0` and `p0_p1_blocker_count=0`; shadow records pass without production impact or SMTP; all required board routes include source ids, route explanations, `authority_gate=pass`, `metadata_only=true`, and evidence references; and all D3 core acceptance and production flags remain false.

## Boundaries

This phase grants D3 readiness review evidence only. It does not grant D3 source-domain production acceptance, Stage2 production acceptance, integrated production acceptance, or daily operation.

Forbidden and kept false:

- D3 core source-domain acceptance
- formal production inclusion
- Stage2 or integrated production acceptance
- SMTP transport
- Release upload
- GitHub cloud schedule
- production queue mutation
- public schema or queue schema migration
- bulk scraping
- PDF download
- full-text extraction
- paid API use
- paywall bypass
- V7.1 CURRENT switch
- V7.2 mail or public Schema pre-run

## V7.2 Revalidation

S2PDT04 proceeds only after the Stage2 completed-work V7.2 revalidation receipt was recorded. The current product contract remains `ADP-PRODUCT-CONTRACT-V7.2`, V7.1 remains read-only history, and inherited V7.1 P0/P1 blockers continue to block real restore, SMTP production, scheduler installation, Release/final production claims, and `INTEGRATED_PRODUCTION_ACCEPTED`.

## Evidence

- Code: `arxiv-daily-push/src/arxiv_daily_push/stage2_sources.py`
- CLI: `arxiv-daily-push/src/arxiv_daily_push/cli.py`
- Tests: `arxiv-daily-push/tests/test_stage2_sources.py`
- Model: `MOD-ADP-064`
- Formula: `FORM-ADP-066`
- Parameters: `PARAM-ADP-450` through `PARAM-ADP-458`
- Revalidation receipt: `arxiv-daily-push/docs/phase_records/PHASE_V7_2_REVALIDATION_S2PD_COMPLETED_WORK_RECEIPT.md`
- Manifest: `governance/run_manifests/ADP-S2PDT04-CHINA-D3-READINESS-EVIDENCE-20260624.json`

## Verification

Initial focused validation:

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_s2pdt04_focus2_v72 PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_stage2_sources.py -q`
- Result: 47 tests OK

Final governance validation is recorded in the run manifest after closeout.

Final local validation:

- V7.2 contract validator: PASS, errors 0, warnings 0
- V7.2 contract unittest: 4 tests OK
- Focused Stage2 source tests: 47 tests OK
- Full `arxiv-daily-push/tests`: 274 tests OK
- Semantic extractor: 66 formulas / 441 parameters OK
- ADP project governance: errors 0, warnings 0
- Lean render check: drift 0, reference issues 0
- JSON/JSONL/CSV parse: OK
- YAML parse: 8 files OK
- `git diff --check`: PASS

# Industry Research System

This directory is the PFI_OS landing zone for the AI-Research-System / Industry Research and Trading Strategy Advice system.

## Current Phase

`source_migrated`

The public-safe source, tests, docs, configs, prompts, templates, scripts, and sample data were migrated into `source/`. Runtime artifacts and private account data were intentionally excluded.

## Directory Map

- `source/src/`: research, reporting, monitoring, data trust, reconciliation, ResearchBus, PFIOS, policy bridge, moomoo/OpenD adapter, and report-quality logic.
- `source/tests/`: regression tests that use local sample fixtures and mocks.
- `source/docs/`: data trust, reconciliation, manual review, entity registry, evidence decision, report layer, and workflow docs.
- `source/config/`: public-safe stub LLM config and risk/strategy examples.
- `source/00_prompts/` and `source/01_templates/`: report prompts and Markdown templates.
- `source/data/sample/`: public-safe or sanitized fixtures for tests and demo runs. These are not real account records.
- `evidence/`: reserved for future migration evidence summaries.

## Privacy Boundary

Allowed in GitHub:

- Source code, tests, docs, prompt/template files, public-safe configs, and sample fixtures.
- Synthetic or zero-value sample holdings and watchlists used by tests.
- Handoff summaries that do not include transaction-level private data.

Forbidden in GitHub:

- `data/private/`, Alipay exports, screenshots/videos, real holdings, account summaries, pending orders, moomoo local databases, cookies, API keys, broker tokens, generated PDFs, source logs, report artifacts, and local runtime logs.

## Smoke Validation

Run from repository root:

```bash
python3 -m compileall -q \
  systems/industry_research/source/src \
  systems/industry_research/source/doctor.py
```

```bash
PYTHONPATH=systems/industry_research/source \
python3 -m pytest \
  systems/industry_research/source/tests/test_advice_engine.py \
  systems/industry_research/source/tests/test_backtesting.py \
  systems/industry_research/source/tests/test_reconciliation.py \
  systems/industry_research/source/tests/test_workflow_layer.py \
  -q
```

## Productization Next Steps

1. Create an PFI_OS adapter that publishes report readiness, evidence-grade summaries, research themes, and validation tasks to ResearchBus without exposing raw account artifacts.
2. Keep report generation fail-closed when model gates, quote snapshots, Alipay confirmation, policy bridge, or report evidence are stale or blocked.
3. Move macOS operation into the unified PFI_OS UI Shell after the policy system is migrated.
4. Keep all real execution as research-only. No broker order placement or real trade submission.

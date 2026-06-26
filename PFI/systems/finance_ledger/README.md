# Finance Ledger System

This directory is the PFI_OS landing zone for the local Consumption Analysis / Finance Ledger system.

## Current Phase

`source_migrated`

The production source, tests, docs, configs, launcher source, and public-safe assets were migrated into `source/`. Runtime data and generated outputs were intentionally excluded.

## Directory Map

- `source/`: migrated source project from the legacy local root.
- `source/src/econ_bleed_analyzer/`: parser, classifier, ledger, reporting, audit, reconciliation, data trust, and review logic.
- `source/scripts/`: local CLI, weekly update, validation, read-only API, package, doctor, and launcher scripts.
- `source/tests/`: regression tests that can run without private user data.
- `source/docs/`: workflow, data contract, Weixin ingestion, and reference-model docs.
- `samples/`: tiny sanitized Alipay/WeChat sample bills for parser smoke tests and onboarding.
- `evidence/`: reserved for future migration evidence summaries. Do not store raw bills here.

## Privacy Boundary

Allowed in GitHub:

- Source code, tests, configs, docs, launcher source, and public-safe icons.
- Small synthetic or anonymized samples under `samples/`.
- Handoff notes that do not include transaction-level private data.

Forbidden in GitHub:

- Raw Alipay/WeChat bills, transaction-detail HTML, personal names, account numbers, order ids from real bills.
- SQLite runtime databases such as `finance_ledger.sqlite` or `consumption.sqlite`.
- Generated `outputs/`, browser screenshots, audit logs containing transaction rows, local `work/`, cookies, tokens, and API keys.

## Smoke Validation

Run from repository root:

```bash
PYTHONPATH=systems/finance_ledger/source/src \
python3 -m pytest \
  systems/finance_ledger/source/tests/test_bill_import.py \
  systems/finance_ledger/source/tests/test_classifier.py \
  systems/finance_ledger/source/tests/test_reconciliation.py \
  -q
```

Compile check:

```bash
python3 -m compileall -q \
  systems/finance_ledger/source/src \
  systems/finance_ledger/source/scripts
```

## Productization Next Steps

1. Add an PFI_OS adapter that publishes only summarized cashflow, category, risk-tag, and review-queue metrics to ResearchBus.
2. Keep write operations approval-gated; do not let other systems mutate ledger production tables directly.
3. Rebuild the macOS launcher after the unified UI Shell is ready, instead of preserving the old standalone app as the final entrypoint.
4. Move only deterministic tests into root CI; keep browser/PDF/final package gates as macOS acceptance gates.

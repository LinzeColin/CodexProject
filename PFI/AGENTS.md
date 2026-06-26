# PFI Agent Contract

## Current Root

PFI V0.2 work uses `CodexProject/PFI` as the only active product root.
The QBVS runtime lives at `PFI/modules/qbvs_lab/qbvs` and maps to
`投资管理 > 策略实验室 / 大数据模拟器`.

## Stage 1 Scope

Stage 1 builds the shared PFI V0.2 skeleton:

- 8 first-level IA contract.
- DataSource, Account, AssetInstrument, ImportBatch, RawRecord,
  NormalizedTransaction, LedgerEvent, and Snapshot model contracts.
- Transfer, fund, bullion, and credit-card repayment classification fixtures.

## Boundaries

- Do not move or rename `PFI/modules/qbvs_lab/qbvs` without a dedicated
  migration gate and backup.
- Do not add Alpha as a PFI product page or first-level navigation entry.
- Do not add rejected Alpha variants, system/development product navigation, or
  real-money execution surfaces.
- Do not request, store, or test trading passwords.
- Do not submit broker orders, payments, or automatic real-money actions.
- Owner-provided personal finance data and non-trading credentials are allowed
  only for local read/import/reconciliation flows in later stages.

## Validation

Preferred Stage 1 checks:

```bash
cd PFI
PYTHONPATH=src python3 -B -m unittest tests.test_stage1_ia_contract -q
PYTHONPATH=src python3 -B -m unittest tests.test_stage1_core_models -q
PYTHONPATH=src python3 -B -m unittest tests.test_stage1_classification_rules -q
cd modules/qbvs_lab && PYTHONPATH=. python3 -B -m unittest tests.test_s3pct02_lifecycle -q
```

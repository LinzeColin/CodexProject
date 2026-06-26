# PFI Handoff

Last updated: 2026-06-27 Australia/Sydney

## Current Goal

Complete PFI V0.2 Stage 2 in `CodexProject/PFI`.

## Current Status

- Correct project root is `PFI/`.
- Legacy compatibility entry is `PFI/大数据模拟器`.
- Active legacy runtime path is `PFI/大数据模拟器/qbvs`.
- Stage 1 contracts remain in `src/pfi_v02/stage1_ia.py`, `src/pfi_v02/core_models.py`, and `src/pfi_v02/classification_rules.py`.
- Stage 2 registry is implemented in `src/pfi_v02/stage2_registry.py`.
- Stage 2 import pipeline is implemented in `src/pfi_v02/stage2_import.py`.
- Stage 2 non-CSV and reconciliation contracts are implemented in `src/pfi_v02/stage2_contracts.py`.
- Stage 2 record is `docs/pfi_v02/STAGE2_DATA_SYNC_MVP.md`.

## Decisions

- Do not flatten, move, or broadly refactor `PFI/大数据模拟器/qbvs`.
- Put new shared PFI V0.2 contracts at the `PFI/` root.
- Keep strategy backtesting and 大数据模拟器 under `投资管理 > 策略实验室 / 大数据模拟器`.
- Keep PFI research-only: no trading password, no automatic real-money orders.
- Non-CSV sources are first-class: 支付宝基金、中国大陆券商、ABC Bullion do not rely on CSV as the primary contract.
- Low-confidence OCR/screenshot/recording input is candidate-only and must enter review before acceptance.

## Validation Commands

```bash
PYTHONPATH=src python3 -B -m unittest tests.test_stage1_ia_contract tests.test_stage1_core_models tests.test_stage1_classification_rules tests.test_stage2_data_source_registry tests.test_stage2_cba_csv_import tests.test_stage2_alipay_import tests.test_stage2_non_csv_contracts -q
cd 大数据模拟器 && PYTHONPATH=. python3 -B -m unittest tests.test_s3pct02_lifecycle -q
git diff --check
```

Latest Stage 2 target result: `Ran 22 tests / OK`.
Latest closeout result: Stage 1+2 contracts `Ran 45 tests / OK`; legacy QBVS smoke `Ran 1 test / OK`; scoped exclusion grep and `git diff --check` produced no output; no local cache files were found under `PFI`.

## Next

1. Re-run full Stage 1+2 contract tests plus legacy QBVS smoke before closeout.
2. Stage 3 can build owner-readable homepage/account/ledger MVP on these contracts.

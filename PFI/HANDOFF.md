# PFI Handoff

Last updated: 2026-06-27 Australia/Sydney

## Current Goal

Complete PFI V0.2 Stage 1 in `CodexProject/PFI`.

## Current Status

- Correct project root is `PFI/`.
- Legacy compatibility entry is `PFI/大数据模拟器`.
- Active legacy runtime path is `PFI/大数据模拟器/qbvs`.
- Stage 1 Phase 1A IA contract is implemented in `src/pfi_v02/stage1_ia.py`.
- Stage 1 Phase 1B core model contract is implemented in `src/pfi_v02/core_models.py`.
- Phase 1A validation command is `PYTHONPATH=src python3 -B -m unittest tests.test_stage1_ia_contract -q`.
- Phase 1B validation command is `PYTHONPATH=src python3 -B -m unittest tests.test_stage1_core_models -q`.

## Decisions

- Do not flatten or move `PFI/大数据模拟器/qbvs` during Stage 1.
- Put new shared PFI V0.2 contracts at the `PFI/` root.
- Keep strategy backtesting and 大数据模拟器 under `投资管理 > 策略实验室 / 大数据模拟器`.
- Keep PFI research-only: no trading password, no automatic real-money orders.

## Next

1. Phase 1C: add transfer/fund/bullion/credit repayment classification fixtures.
2. Re-run Stage 1 tests plus legacy QBVS smoke.

# PFI Agent Contract

## Current Root

PFI V0.2 work uses `CodexProject/PFI` as the only active product root.
QBVS is an independent top-level system at `CodexProject/QBVS`; PFI may keep
external references to `QBVS/qbvs`, but PFI investment management must not own
or cover QBVS.

## Stage 1 Scope

Stage 1 builds the shared PFI V0.2 skeleton:

- 8 first-level IA contract.
- DataSource, Account, AssetInstrument, ImportBatch, RawRecord,
  NormalizedTransaction, LedgerEvent, and Snapshot model contracts.
- Transfer, fund, bullion, and credit-card repayment classification fixtures.

## Boundaries

- Do not re-embed `QBVS/qbvs` under `PFI/`.
- Keep PFI's own strategy backtesting, market-feel training, and simulator
  surfaces available under PFI.
- Do not add Alpha as a PFI product page or first-level navigation entry.
- Do not add rejected Alpha variants, system/development product navigation, or
  real-money execution surfaces.
- Do not request, store, or test trading passwords.
- Do not submit broker orders, payments, or automatic real-money actions.
- Owner-provided personal finance data and non-trading credentials are allowed
  only for local read/import/reconciliation flows in later stages.

## S4 精简执行胶囊

普通 PFI 任务先读本文件，以及用户或任务包点名的任务/证据文件。不得默认读取完整
`开发记录.md` 或 `模型参数文件.md`；只有任务涉及 roadmap 事实、模型规则、
公式、评分、阈值、财务计算、安全门禁或发布验收时，才升级读取这些完整文件。

验证命令：

```bash
cd PFI
PYTHONPATH=src python -B -m unittest tests.test_stage1_ia_contract tests.test_stage1_core_models tests.test_stage1_classification_rules -q
```

预览/就绪检查：

```bash
cd PFI
PYTHONPATH=src python -B -m pfi_os.examples.dev_ready_check
```

治理验证和 owner 预览：

```bash
python -B scripts/lean_governance.py validate --project PFI --semantic
python -B scripts/lean_governance.py check-render --project PFI
```

完整开发历史仍保留在 `开发记录.md`；本胶囊只是普通任务的一页启动路线。

## Validation

Preferred Stage 1 checks:

```bash
cd PFI
PYTHONPATH=src python3 -B -m unittest tests.test_stage1_ia_contract -q
PYTHONPATH=src python3 -B -m unittest tests.test_stage1_core_models -q
PYTHONPATH=src python3 -B -m unittest tests.test_stage1_classification_rules -q
cd ../QBVS && PYTHONPATH=. python3 -B -m unittest tests.test_s3pct02_lifecycle -q
```

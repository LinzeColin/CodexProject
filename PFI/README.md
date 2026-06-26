# PFI

PFI V0.2 is the Personal Financial Intelligence project under
`LinzeColin/CodexProject/PFI`.

The old public entry `PFI/大数据模拟器` is retained as a compatibility entry and
runtime boundary for QBVS. New product contracts, shared facts, tests, and
handoff records live at the `PFI/` root.

## Stage 1

Stage 1 builds the common skeleton for accounts, assets, data sources, ledger,
investment, consumption, recommendations, and reports.

Target first-level entries:

1. 首页总览
2. 账户与资产
3. 账本流水
4. 投资管理
5. 消费管理
6. 数据源与同步
7. 建议与复盘
8. 报告与洞察

Stage 1 source files:

| Purpose | Path |
| --- | --- |
| IA contract | `src/pfi_v02/stage1_ia.py` |
| Stage 1 record | `docs/pfi_v02/STAGE1_CORE_SKELETON.md` |
| Owner feature list | `功能清单` |
| Development record | `开发记录` |
| Model and parameter file | `模型参数文件` |
| Legacy compatibility runtime | `大数据模拟器/qbvs` |

## Boundaries

- No automatic real-money trading.
- No trading password.
- No broker-order or payment submission.
- No Alpha product page inside PFI.
- `PFI/大数据模拟器/qbvs` remains accessible and unmoved.

## Validation

```bash
PYTHONPATH=src python3 -B -m unittest tests.test_stage1_ia_contract -q
cd 大数据模拟器 && PYTHONPATH=. python3 -B -m unittest tests.test_s3pct02_lifecycle -q
```

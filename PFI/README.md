# PFI

PFI V0.2 is the Personal Financial Intelligence project under
`LinzeColin/CodexProject/PFI`.

`PFI/` is the only active product root. The former QBVS container path has
been migrated to `PFI/modules/qbvs_lab` so the root is no longer confused with
one strategy-lab module.

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
| Legacy compatibility runtime | `modules/qbvs_lab/qbvs` |

## Stage 2

Stage 2 builds the data-source and low-operation sync MVP contract. It adds:

- full registry for 支付宝日常、支付宝基金、Moomoo AU、中国券商、ABC Bullion、CBA、微信、其他平台
- CBA CSV parser and watch folder detection
- Alipay daily CSV/ZIP parser and low-confidence review queue
- non-CSV contracts for 支付宝基金、中国券商、ABC Bullion
- Moomoo AU read-only OpenD/API contract that reuses existing QBVS references
- WeChat ZIP/CSV/XLS/XLSX import contract
- reconciliation contracts for fund and bullion triangles

Stage 2 source files:

| Purpose | Path |
| --- | --- |
| Data source registry | `src/pfi_v02/stage2_registry.py` |
| CBA and Alipay import pipeline | `src/pfi_v02/stage2_import.py` |
| Non-CSV and reconciliation contracts | `src/pfi_v02/stage2_contracts.py` |
| Stage 2 record | `docs/pfi_v02/STAGE2_DATA_SYNC_MVP.md` |
| Stage 2 tests | `tests/test_stage2_*.py` |

## Boundaries

- No automatic real-money trading.
- No trading password.
- No broker-order or payment submission.
- No Alpha product page inside PFI.
- `PFI/modules/qbvs_lab/qbvs` is the canonical migrated QBVS runtime path.

## Validation

```bash
PYTHONPATH=src python3 -B -m unittest tests.test_stage1_ia_contract -q
PYTHONPATH=src python3 -B -m unittest tests.test_stage2_data_source_registry tests.test_stage2_cba_csv_import tests.test_stage2_alipay_import tests.test_stage2_non_csv_contracts -q
cd modules/qbvs_lab && PYTHONPATH=. python3 -B -m unittest tests.test_s3pct02_lifecycle -q
```

# PFI V0.2 Stage 1 Core Skeleton

更新时间：2026-06-27 Australia/Sydney

## Goal

建立 PFI V0.2 的核心骨架，让账户、资产、数据源、账本、投资、消费、建议、报告共用同一套事实层。

## Path Decision

Current project root is `CodexProject/PFI`.

`QBVS` is a separate top-level system at `CodexProject/QBVS`. PFI must not own
or cover QBVS. PFI investment management keeps its own strategy backtesting,
market-feel training, parameter scan, and big-data simulator.

## Phase Status

| Phase | Status | Evidence |
| --- | --- | --- |
| Phase 1A: 8 first-level IA contract | Verified | `src/pfi_v02/stage1_ia.py`, `tests/test_stage1_ia_contract.py`, `7 tests OK` |
| Phase 1B: Core object models | Verified | `src/pfi_v02/core_models.py`, `tests/test_stage1_core_models.py`, `9 tests OK` |
| Phase 1C: Classification rules | Verified | `src/pfi_v02/classification_rules.py`, `tests/test_stage1_classification_rules.py`, Stage 1 total `23 tests OK` |

## Phase 1A Contract Summary

PFI V0.2 first-level entries:

1. 首页总览
2. 账户与资产
3. 账本流水
4. 投资管理
5. 消费管理
6. 数据源与上传
7. 建议与复盘
8. 报告与洞察

Acceptance coverage:

| Entry | Required Stage 1 markers |
| --- | --- |
| 首页总览 | 净资产、账户地图、投资快照、消费快照、数据健康、今日建议 |
| 账户与资产 | DataSource / Account / AssetInstrument 分离、账户对账、跨币种 |
| 账本流水 | 消费、投资、转账、退款、费用、估值、汇率、证据链 |
| 投资管理 | Moomoo、支付宝基金、中国券商、ABC Bullion、PFI 策略实验室、盘感训练、大数据模拟器；QBVS 独立于 PFI |
| 消费管理 | 支付宝、微信、CBA、银行卡、信用卡、订阅、转账不计消费 |
| 数据源与上传 | 数据源列表、上传中心、导入中心、同步状态、对账、待复核、外部只读接口 |
| 建议与复盘 | 建议有证据、动作、状态、复盘、失效条件 |
| 报告与洞察 | 月度、投资、消费、数据质量、Context Export、证据链 |

## Boundaries

- No automatic real-money trading.
- No trading password.
- No broker-order or payment submission.
- No Alpha product page or first-level entry inside PFI.
- No system/development product first-level entry.
- `QBVS/qbvs` remains accessible as a top-level independent system, not as a PFI-owned module.

## Phase 1B Contract Summary

Core model contracts:

| Model | Boundary |
| --- | --- |
| CredentialRef | Non-trading credential pointer with read/import scopes only. |
| DataSource | Where data is read from; read-only by default. |
| Account | Where money or liability is held. |
| AssetInstrument | What asset is held. |
| ImportBatch | Dedupe and parser-version boundary for each ingest. |
| RawRecord | Source evidence pointer. |
| NormalizedTransaction | Normalized financial fact. |
| LedgerEvent | Fact used by investment, consumption, recommendation, and reports. |
| AccountSnapshot | Point-in-time account balance. |
| HoldingSnapshot | Point-in-time position state. |
| ValuationSnapshot | Point-in-time price or valuation state. |

Required coverage:

- Data sources: Alipay daily, Alipay fund, Moomoo AU, China broker, ABC Bullion, CBA, WeChat.
- Event types: CASH, TRANSFER, BUY_ASSET, SELL_ASSET, FUND, FEE, TAX, FX, REFUND, VALUATION.
- Account types: payment, bank, brokerage, fund platform, bullion platform, credit card, cash, liability.
- Asset types: cash, equity, ETF, fund, bullion, credit, FX.

## Phase 1C Contract Summary

Classification fixtures:

| Rule | Expected result |
| --- | --- |
| CBA to Moomoo / bank to broker / Alipay to bank transfer | `TRANSFER`, not ordinary consumption |
| Alipay fund subscription/redemption | `FUND`, investment event, not life spending |
| ABC Bullion gold/silver buy/sell | `BUY_ASSET` or `SELL_ASSET`, bullion investment event |
| Credit card repayment | `TRANSFER`, credit liability movement, dedupe key, not duplicate consumption |

## Validation

Phase 1A:

```bash
cd PFI
PYTHONPATH=src python3 -B -m unittest tests.test_stage1_ia_contract -q
```

Observed: `Ran 7 tests` / `OK`.

QBVS independent-system smoke:

```bash
cd QBVS
PYTHONPATH=. python3 -B -m unittest tests.test_s3pct02_lifecycle -q
```

Observed: `Ran 1 test` / `OK`.

Phase 1B:

```bash
cd PFI
PYTHONPATH=src python3 -B -m unittest tests.test_stage1_core_models -q
```

Observed: `Ran 9 tests` / `OK`.

Phase 1C:

```bash
cd PFI
PYTHONPATH=src python3 -B -m unittest tests.test_stage1_classification_rules -q
```

Observed closeout:

| Command | Result |
| --- | --- |
| `PYTHONPATH=src python3 -B -m unittest tests.test_stage1_ia_contract tests.test_stage1_core_models tests.test_stage1_classification_rules -q` | `Ran 23 tests` / `OK` |
| `cd QBVS && PYTHONPATH=. python3 -B -m unittest tests.test_s3pct02_lifecycle -q` | `Ran 1 test` / `OK` |
| Excluded-literal grep scoped to Stage 1 touched files | Pass, no output |
| `git diff --check` | Pass, no output |

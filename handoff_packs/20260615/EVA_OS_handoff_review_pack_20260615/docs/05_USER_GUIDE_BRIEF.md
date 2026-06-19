# EVA_OS 使用者说明简版

## What EVA_OS Is

EVA_OS 是个人研究与决策支持中台。它帮助整理市场数据、策略回测、报告、证据、现金流、政策、消费和 Token ROI，不是自动交易软件。

## What You Can Use Today

| Use Case | How |
| --- | --- |
| 打开系统 | 双击 `EVA_OS.app` |
| 查看总控状态 | 进入总控驾驶舱或运行 `scripts/commandCenter.sh` |
| 运行策略回测 | 使用 QuantLab 的单标的回测 / 策略入口 |
| 做参数扫描 | 使用参数扫描功能或相关脚本 |
| 查看报告 | 进入报告中心或查看 `data/**/**latest*` |
| 查看 Token ROI | 查看 `data/value/EVATokenROILedger_latest.*` |
| 查看政策/消费/现金流快照 | 查看对应 docs 和 `data/policy`, `data/consumption`, `data/cashflow` |
| 查看系统文档 | 先读 `README.md`, `docs/QuickStart.md`, `docs/Index.md` |

## App Entry Points

```text
/Users/linzezhang/Desktop/EVA_OS.app
/Users/linzezhang/Downloads/EVA_OS.app
/Applications/EVA_OS.app
```

## Safety Boundary

EVA_OS will not:

- place real trades;
- connect to broker execution by default;
- automatically bet;
- automatically pay;
- store brokerage passwords;
- replace human judgment.

Treat outputs as research evidence and review material, not as final financial advice.

## Recommended Daily Flow

1. Open `EVA_OS.app`.
2. Check Command Center status.
3. Review missing evidence and action queue.
4. Run backtests or reports only on the needed target.
5. Save important outputs into the report/evidence flow.
6. Do not act on results until evidence quality and limitations are reviewed.

## What Still Needs Work

The system still needs more productization in:

- faster hotspot analysis;
- cleaner consolidated workbench;
- better 52ETF reference ingestion;
- vectorized research mode;
- realtime read-only research flow;
- stronger real evidence inputs for Token ROI, CashFlow, Policy, and Consumption.

# 11 Risk And Boundary Rules

## Non-Execution Boundary

The system must never execute real buy/sell orders. It can only generate:

- recommendation labels;
- operation checklists;
- email/local notifications;
- manual review queues;
- audit records.

## Hard Risk Gates

| Rule | Threshold | Result |
|---|---:|---|
| Max drawdown | >= 40.00% | Block / Clear / Reduce label |
| Recovery time | >= 365 days | Manual Review or Block |
| 7-day drawdown worsening | > 5.00% | Risk Alert |
| Single position over-expansion | > 2 consecutive runs | Reduce / Risk Alert |
| Fee/redemption status missing | Any missing | No-New-Order |
| Official sources | < 2 | Cannot be Action-Ready |

## Benchmark Rules

The system must aim to outperform:

- Shanghai Composite.
- S&P 500.

Use windows:

- 1 month.
- 3 months.
- latest 10 trading days.

If an asset underperforms relevant benchmarks across all windows:

- Do not Increase.
- Use Avoid New or Reduce.

If a short-term asset outperforms but lacks evidence:

- Mark `short_term_momentum_only`.
- Do not Action-Ready.

## Conservative Asset Exclusion

Exclude:

- bond funds;
- money-market funds;
- Yu'e Bao and cash-management products;
- conservative structured products;
- low-growth defensive products;
- products with unexplainable volatility.

## Required Language Boundary

Allowed:

- "目标是跑赢基准。"
- "当前证据支持增配候选。"
- "若人工确认，可在窗口内执行。"

Forbidden:

- "保证跑赢。"
- "稳赚。"
- "必须买入/卖出。"
- "自动下单。"


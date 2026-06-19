# 00 Project Brief: Serenity Daily Analysis

## Goal

Build a local-first automation system named `Serenity Daily Analysis` that ranks aggressive but controlled off-platform fund candidates, audits current holdings, and sends disciplined rebalance notifications.

中文目标：用 Serenity 研究框架做 A 股/美股高成长方向研究，场外基金优先生成 Top5 候选池，并输出候选池刷新、策略更新、纪律审计、追加调仓建议和通知。

## Pursuing Goal

Deliver an MVP that can be run locally on macOS and later scheduled. The MVP must:

1. Store every run in SQLite.
2. Accept Alipay position import by CSV/template first.
3. Use moomoo/OpenD as the preferred market-data source when available.
4. Support fallback aggregated sources only as downgraded evidence.
5. Score and rank off-platform fund candidates.
6. Compare current holdings against target weights.
7. Generate action labels and rebalance alerts.
8. Generate Mac OS Mail-ready notification content and local notification hooks.
9. Never place real trades.

## Primary User

Single local user with high risk tolerance, strict discipline needs, and a requirement to reduce decision and timing loss. The user wants aggressive exposure but with data quality, drawdown, recovery-time, and execution-rule controls.

## Strategy Principle

Target return comes first, but not at the cost of unexplainable volatility or broken execution rules.

Benchmark objective:

- The system must use outperforming Shanghai Composite and S&P 500 as strategy target, filtering standard, discipline gate, and review metric.
- It must not promise or guarantee future outperformance.

## Delivery Boundary

Allowed:

- Research, ranking, scoring, discipline labels, notifications, audit trails, run history, and human-confirmed operation lists.

Forbidden:

- Automatic buy/sell execution.
- Guaranteed profit language.
- Scraping that bypasses authentication, CAPTCHA, or platform rules.
- Storing secrets, cookies, or passwords in plaintext.

## Source Inputs

Priority:

1. moomoo / OpenD / moomoo API.
2. Alipay imported holdings and fund trading-page evidence.
3. Fund company official pages, fund contracts, prospectuses, and announcements.
4. Official platform snapshots.
5. Public financial aggregators as fallback only.

## Core Outputs

- Top5 fund-first candidate pool.
- Candidate scorecard and ranking.
- Target weight table.
- Current holdings deviation audit.
- Rebalance candidate list.
- Manual review queue.
- Missing data and conflict logs.
- Markdown run report.
- Mail-ready notification bodies.
- SQLite database.


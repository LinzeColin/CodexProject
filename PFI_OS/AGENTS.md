# AGENTS.md

## PFI-First Transition Contract

This repository is in a controlled transition from legacy `PFI_OS` / `PFIOS`
to `PFI OS`. Until the directory and namespace migration is performed in a
later issue, agents must treat `PFI_OS/` as the legacy working directory and
the documents under `docs/product`, `docs/data`, `docs/ux`,
`docs/architecture`, and `docs/archive/legacy-migration.md` as the governing
PFI-001 product contracts.

PFI OS is the target product. PFI_OS is legacy input, not the target
architecture. Do not add new user-facing legacy workbench, cashflow, consumption,
or retired value-ledger product surfaces during this transition.

PFI V0.2 Stage 0 is governed by
`docs/pfi_v02/STAGE0_COMPATIBILITY_AUDIT.md`. The V0.2 target product IA has
eight first-level entries: 首页总览, 账户与资产, 账本流水, 投资管理, 消费管理,
数据源与同步, 建议与复盘, 报告与洞察. The current six Web Shell entries remain
compatibility aliases until Stage 1 migration. `PFI/大数据模拟器` maps to
`投资管理 > 策略实验室 / 大数据模拟器`; do not move or rename active runtime
paths while closing Stage 0.

PFI-002 has removed the retired value-ledger active surface. Do not restore its
modules, scripts, tests, navigation entries, command-center sources, or formal
docs. Historical context belongs only in `docs/archive/legacy-migration.md`.

## Project

This project is the local-first PFI_OS entry, displayed as PFI_OS. PFIOS is the embedded quantitative research, analysis, and backtesting subsystem and remains the main operating entry for now.

## Core Scope

- Markets: A-shares, Hong Kong stocks, US stocks.
- Timeframes: 1min to yearly, using a unified bar model.
- Purpose: research, analysis, backtesting, strategy comparison, and report generation.
- No live trading. Do not implement real brokerage order submission unless explicitly requested later.

## Engineering Principles

- Do not store API keys or tokens in source code.
- Use `.env` and `.env.example` for credentials.
- Every strategy must be reproducible and backtestable.
- Every backtest result must save data range, provider, adjustment mode, strategy version, parameters, cost model, and run timestamp.
- Add tests for indicators, signal generation, portfolio accounting, metrics, and edge cases.
- Prefer clear, inspectable logic over black-box shortcuts.
- PFI OS must keep strategy backtesting as a core workflow and preserve market-feel training as a Strategy Lab training mode.
- PFI V0.2 Stage 0 must keep every current owner-facing entry accessible while recording its target location under the 8-entry IA.
- Public/shared data, private user data, derived private data, secrets, and ephemeral runtime artifacts must follow `docs/data/PFI_DATA_BOUNDARIES.md`.

## Validation Discipline

- Default verifier: `scripts/devReadyCheck.sh --summary-json`.
- Do not run `scripts/finalAcceptanceCheck.sh`, `scripts/ciSmoke.sh`, full pytest, or git hooks during routine agent work.
- Heavy SmokeTest gates require explicit release intent and `PFI_OS_ALLOW_HEAVY_SMOKE=1`.
- GitHub smoke is PR/manual only; do not wire it to every `main` push.
- Use targeted tests, syntax checks, `git diff --check`, app-lite/lifecycle/runtime acceptance, and local health checks before escalating to heavy gates.

## Backtest Requirements

Every backtest should calculate total return, annualized return, volatility, Sharpe, Sortino, Calmar, maximum drawdown, win rate, trade count, turnover, average gain/loss, equity curve, drawdown curve, and transaction cost summary.

## Safety

- Never connect to live trading by default.
- Never place real orders.
- If paper trading is added later, require paper-only keys, dry-run mode, and explicit human confirmation.
- Never create autonomous real-money trading, payment, betting, or broker-order execution flows.

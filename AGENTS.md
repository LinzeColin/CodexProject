# AGENTS.md

## Project

This project is the local-first EVA_OS entry, displayed as EVA_OS. QuantLab is the embedded quantitative research, analysis, and backtesting subsystem and remains the main operating entry for now.

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

## Validation Discipline

- Default verifier: `scripts/devReadyCheck.sh --summary-json`.
- Do not run `scripts/finalAcceptanceCheck.sh`, `scripts/ciSmoke.sh`, full pytest, or git hooks during routine agent work.
- Heavy SmokeTest gates require explicit release intent and `EVA_OS_ALLOW_HEAVY_SMOKE=1`.
- GitHub smoke is PR/manual only; do not wire it to every `main` push.
- Use targeted tests, syntax checks, `git diff --check`, app-lite/lifecycle/runtime acceptance, and local health checks before escalating to heavy gates.

## Backtest Requirements

Every backtest should calculate total return, annualized return, volatility, Sharpe, Sortino, Calmar, maximum drawdown, win rate, trade count, turnover, average gain/loss, equity curve, drawdown curve, and transaction cost summary.

## Safety

- Never connect to live trading by default.
- Never place real orders.
- If paper trading is added later, require paper-only keys, dry-run mode, and explicit human confirmation.

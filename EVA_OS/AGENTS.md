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

## Structure Entry

- S4PBT02 archived historical root handoff docs, `handoff_packs/`, `cleanup/`, and the generated feature PDF under `governance/archive/other8_wave1_pending/EVA_OS/`.
- Do not recreate root `HANDOFF.md`, `AGENT_CONTINUITY.md`, `15_OPEN_QUESTIONS.md`, `PLANS.md`, `CODEX_PROMPTS.md`, `CODEX_TASK_PACK.md`, or `UPLOAD_MANIFEST.md` as tracked files.
- Active handoff and architecture navigation lives in `README.md`, `docs/Index.md`, `docs/EVA_OS.md`, `docs/governance/project.yaml`, `docs/governance/roadmap.yaml`, `docs/governance/events.jsonl`, and `docs/EVA_structure_report.md`.
- Historical references remain readable in the governance archive; they are not runtime or import entry points.

## Backtest Requirements

Every backtest should calculate total return, annualized return, volatility, Sharpe, Sortino, Calmar, maximum drawdown, win rate, trade count, turnover, average gain/loss, equity curve, drawdown curve, and transaction cost summary.

## Safety

- Never connect to live trading by default.
- Never place real orders.
- If paper trading is added later, require paper-only keys, dry-run mode, and explicit human confirmation.

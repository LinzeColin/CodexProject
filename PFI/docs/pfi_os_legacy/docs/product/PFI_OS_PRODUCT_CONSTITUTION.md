# PFI OS Product Constitution

Version: PFI-001

## Product Identity

PFI OS is a Personal Financial Intelligence Operating System for one local
user. It is local-first, research-first, evidence-driven, and built for
decision support before human action.

The target product name is `PFI OS`. The target directory is `PFI_OS`, the
target Python namespace is `pfi_os`, and the target command family is `pfi`.
During PFI-001 the working directory remains `PFI_OS`; that name is legacy
input and must not be treated as the target architecture.

## Operating Principles

- PFI-first controlled re-foundation: rebuild the product contract before
  deleting, renaming, or creating a new UI.
- One product, one user-facing entry. Internal services may exist, but the user
  should not have to operate PFIOS, ResearchBus, policy, cashflow, or other
  sub-products separately.
- Six primary workspaces only: 首页, 市场, 研究, 持仓, 策略实验室, 数据与系统.
- Every fact, estimate, recommendation, backtest, training result, and risk
  note must show source, as-of time, freshness, evidence class, and model or
  strategy version when applicable.
- PFI OS must still run core flows when the LLM provider is disabled.
- LLM providers are optional analysis accelerators, not authoritative writers
  of facts, holdings, trades, model versions, or orders.
- Strategy backtesting is a core workflow.
- Market-feel training is retained as a Strategy Lab training mode.
- No autonomous live trading, real-money order placement, broker submission,
  payment, betting, or unattended execution path is allowed.
- Human review is required for all decision queues and any order-intent style
  output.

## MVP Stop Conditions

PFI OS can be marked MVP-complete only when:

- Active product identity, scripts, packages, app names, and formal docs use
  PFI OS naming.
- Legacy names appear only in `docs/archive/legacy-migration.md` or Git
  history.
- Retired value-ledger surfaces are absent from navigation, active code paths,
  scripts, tests, formal docs, and new runtime summaries.
- The user sees one PFI OS entry, not independent user-facing platforms.
- The four core loops work end to end: market to research, policy document to
  impact analysis, portfolio to risk optimization, and strategy to validation.
- Strategy backtests are reproducible for the same data, costs, parameters, and
  strategy version.
- Market-feel training hides future data before answer reveal and records
  review outcomes without presenting a trading signal.
- Public/shared, private user, private derived, secret, and ephemeral data
  boundary tests pass.
- Git contains no real holdings, trades, account identifiers, private
  documents, SQLite runtime databases, secrets, or local logs.
- No live automatic order route exists.

## Non-Goals

- No live automatic trading.
- No autonomous broker, bank, payment, or betting execution.
- No multi-product launcher set for ordinary use.
- No global coverage of all assets, markets, and document types in v0.1.
- No mandatory local LLM before product architecture and data boundaries are
  correct.
- No preservation of low-value PFI features for nostalgia.
- No long-lived Streamlit and web dual-track product strategy.

## Review Queues

PFI OS uses explicit review queues:

- `manual_review_queue`
- `missing_data_log`
- `decision_record`
- `audit_log`
- `source_log`

Conclusion labels are: Actionable, Watch, Observe, Reject.

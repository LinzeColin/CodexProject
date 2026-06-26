# PFI Target Architecture

Version: PFI-001

PFI OS is one product, one repository area, and one user-facing launcher. The
internal implementation may use several processes, but the user should start
and understand one product.

## Target Shape

```text
CodexProject/
└── PFI_OS/
    ├── AGENTS.md
    ├── PLANS.md
    ├── README.md
    ├── pyproject.toml
    ├── .env.example
    ├── config/
    │   ├── sources/
    │   ├── policies/
    │   ├── models/
    │   └── schemas/
    ├── src/
    │   └── pfi_os/
    │       ├── domain/
    │       ├── application/
    │       ├── data/
    │       ├── analytics/
    │       ├── markets/
    │       ├── research/
    │       ├── portfolio/
    │       ├── strategy/
    │       ├── evidence/
    │       ├── agents/
    │       ├── api/
    │       ├── workers/
    │       └── infrastructure/
    ├── web/
    │   ├── app/
    │   ├── components/
    │   ├── features/
    │   ├── lib/
    │   ├── styles/
    │   └── tests/
    ├── scripts/
    │   └── pfi
    ├── tests/
    │   ├── unit/
    │   ├── contract/
    │   ├── integration/
    │   ├── e2e/
    │   └── visual/
    └── docs/
        ├── product/
        ├── architecture/
        ├── data/
        ├── ux/
        ├── operations/
        └── archive/
```

## Technology Decisions

- New UI: React/Next.js + TypeScript.
- Python computation kernels: migrate verified kernels into `src/pfi_os`.
- Local API: FastAPI.
- Background jobs: Python worker with local lightweight scheduling for MVP.
- Data: Operational SQLite, DuckDB + Parquet, immutable raw files, local FTS.
- Deployment: native macOS first; Docker is not required for MVP.
- Launcher: `scripts/pfi start` and later `PFI_OS.app`.
- LLM provider: `DisabledProvider` first, then optional OllamaProvider.
- Legacy Streamlit: migration baseline only; do not extend as final product UI.

## Core Runtime Principles

- UI reads application/domain contracts, not provider raw JSON or ResearchBus
  bridge files.
- Worker jobs are idempotent and track job id, status, phase, progress, retry
  count, errors, and artifacts.
- Fast Path does not use LLM:
  Source -> Fetch -> Deduplicate -> Raw Save -> Light Parse -> Entity Match ->
  Lightweight Metrics -> Event/Card -> UI Push.
- Deep Path can use optional LLM after the initial event is visible.
- Local LLM failure must not stop core data, backtest, portfolio, risk, or
  evidence workflows.
- There is no live automatic order route.

## Migration Notes

active entrances. PFI-003 performs directory, namespace, app, env var, script,
and artifact identity migration. PFI-004 creates the new Web Shell.

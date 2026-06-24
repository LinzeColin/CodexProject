# Alpha - Personal Quant Agent Workspace

Alpha is a local-first personal quant agent workspace for research, backtesting,
automatic paper trading, order-intent review, broker-ready ticket generation, and
dashboard visibility.

## Local run

```bash
python -m pip install -e .
python -m pytest tests -q
python -m backend.app.services.paper_trading_loop --once
uvicorn backend.app.main:app --reload
```

Start/stop the local workspace helper:

```bash
scripts/start_alpha_dashboard.sh
scripts/stop_alpha_dashboard.sh
```

When the dashboard starts, the app lifecycle starts the automatic paper agent
runtime. It runs one paper cycle immediately, then refreshes every 300 seconds.

App-format launchers are installed at:

```text
/Users/linzezhang/Downloads/Alpha.app
/Users/linzezhang/Applications/Alpha.app
/Applications/Alpha.app
```

## Historical outputs and handoff

Tracked patch bundles, repository-local launchers, and the reconstructed
handoff that previously lived under `Alpha/outputs/` and `Alpha/HANDOFF.md`
are archived under `governance/archive/other8_wave1_pending/Alpha/`.
The one-version compatibility map is `docs/structure_migration_map.md`.
Future runtime output should stay untracked under `Alpha/outputs/`,
`Alpha/runtime/`, or external local app paths.

Open:

```text
http://localhost:8000/health
http://localhost:8000/dashboard
http://localhost:8000/dashboard/state
```

Useful API endpoints:

```text
POST /paper/run-once
GET  /paper/portfolio
POST /strategy/tournament/run
GET  /agent/loop/status
GET  /orders/approval-queue
```

## Safety

- Live trading is disabled by default.
- Live broker adapter fails closed.
- Policy load failure means reject.
- External API must never trigger live trading.
- Alpha can generate broker-ready order tickets for owner review, but must not
  autonomously submit real-money broker orders.

## Governance

Canonical governance files live in `docs/governance/`:

- `MODEL_SPEC.md`
- `model_registry.yaml`
- `formula_registry.yaml`
- `parameter_registry.csv`
- `DEVELOPMENT_LEDGER.md`
- `development_events.jsonl`
- `DELIVERY_PLAN.md`
- `delivery_tasks.yaml`
- `VERSION_MATRIX.yaml`
- `TRACEABILITY_MATRIX.csv`

中文人类入口：`功能清单`、`开发记录`、`模型参数文件`。这三份文件必须直接保留
owner 可读的功能摘要、Roadmap/任务、模型/参数、证据状态、限制和下一步门禁；
它们不是跳转页，也不是第二套可编辑机器事实源。机器真相仍以
`docs/governance/` 下的 Lean v2 文件为准。

# Alpha Development Rules

## Core Goal

Build Alpha as a local-first personal quant agent workspace. The system may automate research, backtesting, paper trading, risk checks, approval queues, broker-ready order tickets, audit logging, and dashboard status.

Committed code must not implement or enable unattended real-money order submission. Real-money execution must remain outside the autonomous agent path and require owner-side broker confirmation.

## GitHub Continuity Rule

The authoritative project repository is:

```text
https://github.com/LinzeColin/CodexProject
project path: Alpha/
```

There is no active standalone `LinzeColin/Alpha` delivery repository for this
program. Do not push, mirror, or hand off Alpha delivery there. All source code,
project rules, docs, Task Packs, handoff notes, decision logs, test evidence,
and delivery manifests must be committed and pushed through
`LinzeColin/CodexProject`, project path `Alpha/`, after every meaningful run.

The current canonical local root is:

```text
/Users/linzezhang/Documents/Codex/2026-06-19/current-phase-phase-0-goal-scope/work/CodexProject/Alpha
```

Do not resume work from older shadow folders such as
`/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-alpha`
unless the owner explicitly designates them as an evidence source for read-only
comparison.

Local-only state is not authoritative except:

- uncommitted secrets and `.env` files
- broker credentials and account identifiers
- machine-specific cache files
- runtime queues, logs, and local databases

## Safety Boundaries

- `live_trading.enabled` must remain `false` in committed default config.
- `runtime/LIVE_AUTHORIZATION.json` must not be created by development,
  research, dashboard, paper/shadow, or Phase 6 closeout work.
- No committed code may directly call a real broker `place_order` endpoint.
- No agent may receive raw broker trading credentials.
- Real broker integration work is limited to read-only probes, broker paper APIs, or owner-confirmed order tickets.
- All live order candidates must be represented as `OrderIntent` and `BrokerReadyOrderTicket`.
- All live candidates must pass policy, risk, audit, kill-switch, idempotency, and freshness gates before entering the approval queue.
- If any policy or audit dependency fails, the system must reject or pause, not continue.

## Required Handoff Discipline

The historical root `HANDOFF.md` has been archived by S4PBT01 at
`governance/archive/other8_wave1_pending/Alpha/HANDOFF.md`. Do not recreate a
root handoff file for routine work. Keep current owner-facing state in
`开发记录`, canonical facts in `docs/governance/project.yaml`,
`docs/governance/roadmap.yaml`, and `docs/governance/events.jsonl`, and durable
product or safety decisions in `docs/decision_log.md`.

Every implementation run should report:

- changed files
- commands run
- test results
- remaining risks
- recommended next step

## Default Verification

Use the smallest useful checks first:

```bash
python -m pytest tests -q
python -m backend.app.services.paper_trading_loop --once
```

## S4 精简执行胶囊

- 普通 T0/T1 任务先读本文件和任务点名文件，不做无关项目扫描。
- 不得读取完整 `模型参数文件.md`，除非变更涉及策略规则、评分、风险、阈值、券商路由、
  paper/live execution 或模型证据。
- 治理验证：`python -B scripts/lean_governance.py validate --project Alpha --semantic`。
- owner 预览：`python -B scripts/lean_governance.py check-render --project Alpha`。

Run the API locally when touching routes or dashboard behavior:

```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Then inspect:

```text
http://127.0.0.1:8000/dashboard
http://127.0.0.1:8000/health
```

## Out Of Scope Unless Explicitly Re-approved

- autonomous real-money broker order submission
- leverage, margin, CFDs, options, short selling
- crypto withdrawals or cross-exchange transfers
- third-party financial advice or public buy/sell signals
- managing external capital

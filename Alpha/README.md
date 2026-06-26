# Alpha 中文 Owner 快速入口

<!-- CODEX_CHINESE_READABILITY_START -->

中文优先，默认全局中文。用户可读优先。
最小验证：先确认当前状态、证据、风险、下一步和回滚，再进入路径、命令和历史记录。
本轮 Owner-flow 治理任务：本页只改善 Owner 阅读路径和中文入口。
不改产品 canonical current_task，不改运行代码，不触发外部自动化。

中文优先，默认全局中文。用户可读优先。本段是 Owner 首屏摘要，用来回答“这是什么、现在到哪、我下一步看哪里、风险是什么”。技术名词、路径、API 名称可以保留英文，但解释必须先给中文结论。

## 一句话结论
量化策略与回测项目，当前重点是把策略、配置、测试证据和风险边界放到同一个可核查入口，避免 Owner 在代码目录和历史归档之间来回搜索。

这份中文入口不是目录索引，也不是给机器看的字段清单；它先服务 Owner 决策。读者应该先看到当前是否可用、证据是否足够、哪里有风险、下一步该做什么，以及如果判断错误如何回滚。只有在这些中文结论清楚之后，才需要进入下方的详细路径、测试命令和历史记录。

## 摘要
- project_id: `Alpha`
- 项目路径：`Alpha`
- current_stage: `S5`
- current_phase: `S5PA`
- current_task: `S5PAT01`
- next_gate: `S5PA-GATE-IN-PROGRESS`
- evidence_status: `以仓库内 docs/governance、测试结果、run manifest 和当前文件为准；没有证据的内容只按待确认处理。`
- 中文人类入口：`README.md`、`功能清单`、`开发记录`、`模型参数文件`。

## 当前状态
这个项目已经纳入 Lean v2 治理入口，首屏必须先说明业务含义、当前阶段、可用证据和限制。Owner 不需要先读源码，也不需要先理解 schema，应该能在本页判断是否继续验证、暂停、回滚或进入下一步。

## Owner 操作入口
1. 先读本文件首屏，确认项目目的、当前任务和下一步。
2. 需要看功能范围时读 `功能清单`，只把有证据的能力当作当前事实。
3. 需要看推进历史时读 `开发记录`，按 Stage -> Phase -> Task 和 stop_gate 判断是否能继续。
4. 需要看模型、公式、参数时读 `模型参数文件`，重点看 active 项和未确认项。
5. 需要机器证据时打开 `docs/governance/` 下的 registry、roadmap、events、STATUS 和 OWNER_STATUS。

## 证据与验证
- active_model_count: `9`
- active_formula_count: `9`
- active_parameter_count: `55`
- 总模型数：`9`；总公式数：`9`；总参数数：`55`。
- 当前证据以仓库文件为准；测试命令、CI 结果或 run manifest 缺失时，只能标记为待验证，不能写成已完成。

## 风险与边界
- 不把历史归档、示例、旧报告、生成物或草稿当成当前生产事实。
- 不因为存在文件路径就默认功能已可用；必须有治理证据、测试结果或 Owner 接受记录。
- 不在没有 Owner 明确确认时改变业务含义、模型参数、公式政策、隐私边界或外部自动化行为。

## 下一步
先补齐中文可读入口，再运行 changed-only 治理检查；若检查失败，优先修复证据、状态和中文说明，不用英文索引页绕过验收。普通开发只走 changed-only compact gate，完整治理计算放到计划任务或手动 all scope。

## 回滚
本次中文可读重做只改文档入口、测试和治理验收规则；如需回滚，恢复本文件和对应人类入口文件即可，不需要迁移数据、不需要改业务代码、不需要触发外部服务。

<!-- CODEX_CHINESE_READABILITY_END -->

# Alpha 中文 Owner 可读入口

# Alpha 中文 Owner 快速入口

- 产品 canonical 当前状态：`S5` / `S5PA` / `S5PAT01`，下一 Gate 为 `S5PA-GATE-IN-PROGRESS`；事实源以 `docs/governance/roadmap.yaml`、`功能清单`、`开发记录` 为准。
- 本轮 Owner-flow 治理任务：`S6PAT02` / `ACC-S6PAT02`，只补 Owner 路径，不改产品 canonical current_task。
- 验收口径：用户可读优先；中文优先，默认全局中文。
- 当前状态：主动源码仍在 `Alpha/backend/`，测试在 `Alpha/tests/`，配置在 `Alpha/configs/`。
- 历史输出边界：旧 `Alpha/outputs/**` 和旧 `Alpha/HANDOFF.md` 已归档到 `governance/archive/other8_wave1_pending/Alpha/`，不要把它们重新当作主动源码。
- S6PA 事实：`S6PA-GATE` 已在 repo-level Owner/Agent 路径范围内通过；`S6PB-GATE` 和最终 `S6-GATE` 仍在进行中。
- 操作路径：入口 `Alpha/backend/` -> 安装依赖 -> 运行最小测试 -> 若失败先看环境 blocker 和 `Alpha/docs/structure_migration_map.md`。
- 最小验证路径：先进入 `Alpha/`，再运行 `python -m pytest tests/test_backtest_fixture.py -q`。
- 当前环境 blocker：本机 bundled Python 缺少 `pytest`；运行策略/治理代码前还可能需要 `python -m pip install -e .[dev]` 安装 `pyyaml` 和 pytest 依赖。
- 成功反馈：测试通过后应看到 backtest fixture deterministic / 1 passed。
- 失败去向：若出现 `No module named pytest` 或 `No module named yaml`，先处理开发依赖；若出现业务断言失败，再查看 `Alpha/docs/structure_migration_map.md` 和对应测试文件。
- 回滚：revert S6PAT02 Alpha README 提交即可；本轮不改运行代码、不移动文件、不触发交易或外部自动化。

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

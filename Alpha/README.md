# Alpha 中文 Owner 快速入口

<!-- CODEX_CHINESE_READABILITY_START -->

中文优先，默认全局中文。用户可读优先。
最小验证：先确认当前状态、证据、风险、下一步和回滚，再进入路径、命令和历史记录。
本轮 Owner-flow 治理任务：本页只改善 Owner 阅读路径和中文入口。
不改产品 canonical current_task，不改运行代码，不触发外部自动化。

## 一句话结论

量化策略与回测项目，当前重点是把策略、配置、测试证据和风险边界放到同一个可核查入口，避免 Owner 在代码目录和历史归档之间来回搜索。
本页只提供 Owner 第一屏判断；详细字段、路径和历史放在下方原文与 `docs/governance/`。

## 中文瘦身原则

- 本入口瘦身不是删除事实，而是把反复计算、英文键名解释和历史索引移到下方；第一屏只留下 负责人当下要判断的状态、证据、风险、动作和回滚。
- 后续执行者 继续开发时，不应重新扫描全量治理目录；只取当前任务、下一门禁、必要证据和失败去向，避免上下文被重复材料消耗。
- 需要复盘时再读取机器字段、路线图、事件、登记表和运行清单；这些材料仍是事实源，但不进入每一次小开发动作的默认输入。
- 若为了变短而让 负责人看不懂、让证据来源消失或让 待定 被写成完成，本次瘦身即视为失败，必须回滚入口或补证据。
- 英文项目名、路径和命令只作定位；当英文数量变多时，必须用中文说明其业务含义、验收边界和开发影响。

## 当前状态
本项目已纳入 Lean v2 中文入口；当前事实以仓库文件、治理记录、测试命令和 run manifest 为准，缺证据时保持 待定。

## Owner 操作入口

先读本页，再按需进入 `功能清单`、`开发记录`、`模型参数文件` 和 `docs/governance/`；日常开发只带走当前任务、下一门禁、风险、回滚和必要证据。

## 证据与验证

证据以仓库事实和验证命令为准；中文说明只解释事实，不替代事实。

## 风险与边界

不把旧报告、示例、路径列表或英文键名当作当前完成事实；瘦身只移出重复治理计算，不删除治理真相。

## 下一步

先补缺失证据，再运行 变更范围快速门禁；完整治理计算留给计划任务或手动 all scope。

## 回滚

若入口误导 Owner，回滚本标记区文本；不迁移数据、不改业务代码、不触发外部服务。

## 摘要

- 项目 ID： `Alpha`
- 项目路径：`Alpha`
- 当前阶段： `S5`
- 当前分段： `S5PA`
- 当前任务： `S5PAT01`
- 下一门禁： `S5PA-GATE-IN-PROGRESS`
- 证据状态： `以仓库内 docs/governance、测试结果、run manifest 和当前文件为准；没有证据的内容只按待确认处理。`
- 中文人类入口：`README.md`、`功能清单`、`开发记录`、`模型参数文件`。
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

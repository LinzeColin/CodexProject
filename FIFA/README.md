# FIFA 中文 Owner 快速入口

<!-- CODEX_CHINESE_READABILITY_START -->

中文优先，默认全局中文。用户可读优先。
最小验证：先确认当前状态、证据、风险、下一步和回滚，再进入路径、命令和历史记录。
本轮 Owner-flow 治理任务：本页只改善 Owner 阅读路径和中文入口。
不改产品 canonical current_task，不改运行代码，不触发外部自动化。

中文优先，默认全局中文。用户可读优先。本段是 Owner 首屏摘要，用来回答“这是什么、现在到哪、我下一步看哪里、风险是什么”。技术名词、路径、API 名称可以保留英文，但解释必须先给中文结论。

## 一句话结论
足球数据与分析项目，当前重点是把数据、模型、测试、风险和验收状态讲清楚，避免只看到工程目录却看不出项目能做什么。

这份中文入口不是目录索引，也不是给机器看的字段清单；它先服务 Owner 决策。读者应该先看到当前是否可用、证据是否足够、哪里有风险、下一步该做什么，以及如果判断错误如何回滚。只有在这些中文结论清楚之后，才需要进入下方的详细路径、测试命令和历史记录。

## 摘要
- project_id: `FIFA`
- 项目路径：`FIFA`
- current_stage: `S5`
- current_phase: `S5PB`
- current_task: `S5PBT02`
- next_gate: `S5PB-GATE-IN-PROGRESS`
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
- active_model_count: `10`
- active_formula_count: `10`
- active_parameter_count: `109`
- 总模型数：`11`；总公式数：`11`；总参数数：`118`。
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

# FIFA 中文 Owner 可读入口

# FIFA 中文 Owner 快速入口

- S6PAT02 中文 Owner 快速入口：用户可读优先；中文优先，默认全局中文。
- 本轮 Owner-flow 治理任务：`S6PAT02` / `ACC-S6PAT02`，只补 Owner 路径，不改产品 canonical current_task；下一 Gate：`S6PA-GATE` 仍在进行中。
- 本轮边界：只补 Owner 可读路径，不改运行代码，不移动文件，不触发投注、TAB 点击、OpenD、邮件、launchd、app 打包或外部自动化。

| Owner 判断项 | 当前路径 | 状态 |
|---|---|---|
| active pipeline | `tab-research-pipeline/` | 主动研究流水线和默认测试入口，本轮不改 |
| legacy | `legacy/fifa-analysis-system/` | 只读历史实现，不参与默认运行 |
| artifacts | `artifacts/latest/`、`artifacts/backups/` | 生成结果和备份，不作为源码事实 |
| ops | `ops/` | 本地运行参考，不是 runtime source |

- 当前运行口径：research-only；当前 executable new stake 仍为 `AUD 0`。
- 最小验证路径：进入 `FIFA/tab-research-pipeline/`，运行 `set PYTHONPATH=..\..\..\test_stubs;.&& python -B -m unittest tests.test_pipeline.PipelineTests.test_parse_market_pairs tests.test_pipeline.PipelineTests.test_parse_market_pairs_rejects_invalid_decimal_odds_tokens tests.test_pipeline.PipelineTests.test_matches_gate_blocks_invalid_raw_decimal_odds tests.test_pipeline.PipelineTests.test_write_outputs tests.test_pipeline.PipelineTests.test_write_outputs_fails_closed_without_success_deliverables_when_gate_blocks tests.test_pipeline.PipelineTests.test_write_outputs_legacy_blocked_export_requires_explicit_flag -q`；本轮实测结果为 `Ran 6 tests` / `OK`。
- 最小治理验证：在仓库根目录运行 `python -B scripts/lean_governance.py check-render --project FIFA`，用于确认中文入口仍由 Lean v2 事实渲染且无漂移。
- 失败去向：若出现 `No module named fcntl`，先确认 `PYTHONPATH` 指向 `work/test_stubs`；若 parser、validation 或 export 断言失败，再查 `FIFA/docs/FIFA_structure_report.md`、`governance/stage_gates/s5pb/fifa_smoke_tests.log` 和 `tab-research-pipeline/tests/test_pipeline.py`。
- 回滚：revert S6PAT02 FIFA README 提交即可；本轮不改运行代码、不移动文件、不启用投注，不触发交易或外部自动化。

# FIFA TAB Research System

This repository is the continuity home for the local TAB FIFA betting-research system.

## Purpose

Build and maintain a research-only FIFA World Cup betting market analysis system:

- read and normalize authorized/public-safe market snapshots;
- generate Chinese professional betting-research reports;
- track research cadence, missing reports, and model/market diagnostics;
- monitor private My Bets positions only after local user authorization;
- support daily report automation readiness;
- never place bets, click odds, mutate Bet Slip, or bypass TAB access controls.

## Current Status

- Local app entry: `http://127.0.0.1:8767/`
- Local app bundle: `/Users/linzezhang/Downloads/TAB FIFA盘口研究系统.app`
- Primary code: `tab-research-pipeline/`
- Latest public artifacts: `artifacts/latest/`
- Legacy system: `legacy/fifa-analysis-system/` is read-only and not a default run path.
- Local ops material: `ops/` is operational reference only, not application source.
- Handoff: `docs/HANDOFF.md` and `docs/HANDOFF_DETAILED.md`
- Governance entry: `docs/governance/MODEL_SPEC.md`
- Current formal automation status: blocked.
- Research-only daily report status: available as candidate.
- Current executable new stake: `AUD 0`.

## S5PBT01 Structure Boundary

- Active pipeline and tests live under `tab-research-pipeline/`.
- Legacy implementation is isolated under `legacy/fifa-analysis-system/`; default commands do not import or execute it.
- Generated reports, backups, and public-safe latest artifacts live under `artifacts/`; Wave 2 archive candidates remain checksum-bound by the governance manifest before any future movement.
- Local launch and cleanup notes live under `ops/`; they are not product runtime source.
- Structure evidence: `docs/FIFA_structure_report.md` and `../governance/stage_gates/s5pb/fifa_structure_contract.yaml`.

## Governance Baseline

FIFA now maintains canonical governance files under `docs/governance/`:

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

## Hard Boundary

TAB public raw / Live discovery access is currently treated as `ai_controlled_access_rejected`.

The system must fail closed and must not use:

- headed fallback for public raw;
- CAPTCHA bypass;
- fingerprint spoofing;
- stealth browser;
- automatic odds clicks;
- Bet Slip mutation;
- unattended betting.

Allowed recovery paths:

- official or authorized odds/data feed;
- user-exported public raw snapshot imported into the pipeline;
- existing fresh partial raw for research-only diagnostics;
- private My Bets read-only import after user-authorized local login.

## Quick Start

```bash
cd tab-research-pipeline
python3 -m unittest tests.test_pipeline
python3 run_daily_report.py
python3 scripts/tab_fifa_app_server.py --port 8767
```

For current status and next steps, read:

- `docs/DEVELOPMENT_STATUS.md`
- `docs/FILE_RETENTION_POLICY.md`
- `docs/HANDOFF.md`

# whkmSalary 中文 Owner 快速入口

<!-- CODEX_CHINESE_READABILITY_START -->

中文优先，默认全局中文。用户可读优先。
最小验证：先确认当前状态、证据、风险、下一步和回滚，再进入路径、命令和历史记录。
本轮 Owner-flow 治理任务：本页只改善 Owner 阅读路径和中文入口。
不改产品 canonical current_task，不改运行代码，不触发外部自动化。

中文优先，默认全局中文。用户可读优先。本段是 Owner 首屏摘要，用来回答“这是什么、现在到哪、我下一步看哪里、风险是什么”。技术名词、路径、API 名称可以保留英文，但解释必须先给中文结论。

## 一句话结论
薪资计算项目，当前重点是把公式、参数、取整规则、测试证据和未确认业务政策分开表达。

这份中文入口不是目录索引，也不是给机器看的字段清单；它先服务 Owner 决策。读者应该先看到当前是否可用、证据是否足够、哪里有风险、下一步该做什么，以及如果判断错误如何回滚。只有在这些中文结论清楚之后，才需要进入下方的详细路径、测试命令和历史记录。

## 摘要
- project_id: `whkmSalary`
- 项目路径：`whkmSalary`
- current_stage: `S5`
- current_phase: `S5PA`
- current_task: `S5PAT04`
- next_gate: `S5PA-GATE-PENDING-MAIN-MERGE`
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
- active_model_count: `2`
- active_formula_count: `10`
- active_parameter_count: `80`
- 总模型数：`2`；总公式数：`10`；总参数数：`80`。
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

# whkmSalary 中文 Owner 可读入口

# whkmSalesSalary

- S6PAT02 中文 Owner 快速入口：用户可读优先；中文优先，默认全局中文。
- 本轮 Owner-flow 治理任务：`S6PAT02` / `ACC-S6PAT02`，只补 Owner 路径，不改产品 canonical current_task；下一 Gate：`S6PA-GATE` 仍在进行中。
- 最小验证路径：进入 `whkmSalary/`，运行 `python -m unittest discover -s tests -q`；本轮实测结果为 `Ran 10 tests` / `OK`。
- source/config/startup 边界：运行代码在 `src/whkm_salary/`；结构配置在 `config/structure_contract.yaml`，只记录结构归属，不承载工资政策参数；启动命令仍是 `streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0`。
- 失败去向：测试失败先看 `tests/test_salary_logic_boundaries.py`、`tests/test_salary_logic_weights.py`、`tests/test_salary_logic_rounding.py`；若启动命令或结构边界不一致，再查 `whkmSalary/docs/whkm_structure_report.md`。
- 回滚：revert S6PAT02 whkmSalary README 提交即可；本轮不改运行代码、不改工资公式、不移动文件、不触发外部自动化。

https://whkmsalessalary-production.up.railway.app/_stcore/health

## 结构入口

| 边界 | 当前路径 | 说明 |
|---|---|---|
| 运行代码 | `src/whkm_salary/` | 绩效工资计算和 Streamlit UI 的真实实现。 |
| 兼容入口 | `salary_logic.py`, `streamlit_app.py`, `Procfile` | 保留旧导入和 Railway 启动命令；文件只转发到 `src/whkm_salary/`。 |
| 测试 | `tests/` | 计算边界、权重、舍入与结构兼容测试。 |
| 结构配置 | `config/structure_contract.yaml` | 只记录结构与入口归属，不承载工资政策参数。 |
| 中文入口 | `功能清单`, `开发记录`, `模型参数文件` | Owner 优先阅读入口，由 `docs/governance/` 渲染。 |
| 结构证据 | `docs/whkm_structure_report.md` | S4PCT02 src/tests/config/中文入口边界报告。 |

启动命令保持不变：`streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0`。

## Governance

Machine sources of truth live under `docs/governance/`.

中文人类入口：`功能清单`、`开发记录`、`模型参数文件`。这三份文件必须直接保留
owner 可读的功能摘要、Roadmap/任务、模型/参数、证据状态、限制和下一步门禁；
它们不是跳转页，也不是第二套可编辑机器事实源。机器真相仍以
`docs/governance/` 下的 Lean v2 文件为准。

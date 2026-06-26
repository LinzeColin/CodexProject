# whkmSalary 中文 Owner 快速入口

<!-- CODEX_CHINESE_READABILITY_START -->

中文优先，默认全局中文。用户可读优先。
最小验证：先确认当前状态、证据、风险、下一步和回滚，再进入路径、命令和历史记录。
本轮 Owner-flow 治理任务：本页只改善 Owner 阅读路径和中文入口。
不改产品 canonical current_task，不改运行代码，不触发外部自动化。

## 一句话结论

薪资计算项目，当前重点是把公式、参数、取整规则、测试证据和未确认业务政策分开表达。
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

- 项目 ID： `whkmSalary`
- 项目路径：`whkmSalary`
- 当前阶段： `S5`
- 当前分段： `S5PA`
- 当前任务： `S5PAT04`
- 下一门禁： `S5PA-GATE-PENDING-MAIN-MERGE`
- 证据状态： `以仓库内 docs/governance、测试结果、run manifest 和当前文件为准；没有证据的内容只按待确认处理。`
- 中文人类入口：`README.md`、`功能清单`、`开发记录`、`模型参数文件`。
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

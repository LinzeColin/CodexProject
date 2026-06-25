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

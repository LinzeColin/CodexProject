# S6PBT02 回归闭环

- 验收状态：`PASSED_REGRESSION_CLOSURE`
- 中文优先，默认全局中文；用户可读优先。
- 本文件只记录 S6PBT01 延后项的关闭结果，不作为产品事实源。
- `S6PB-GATE`：`PASSED`，因为 S6PBT01 的剩余 Medium/Low 已在本轮关闭或转为代码/测试约束。
- `S6-GATE`：`IN_PROGRESS`，仍需 S6PC metrics/review closure evidence；不得提前声明最终通过。

## 本轮关闭项

| Finding | 关闭方式 |
|---|---|
| `S6PBT01-A1-LOW-OUTPUT-DIR-GUARD` | `wave1_gate.py` 和 `wave2_gate.py` 对 `--output-dir` 做 resolved-path 仓库内约束。 |
| `S6PBT01-A1-LOW-DIFF-RECOMPUTE` | S6PAT02/S6PA/S6PBT01 关键 manifest 升级为 `CI_ATTESTED`，测试用 `git show --name-only <result_commit>` 复算 changed files。 |
| `S6PBT01-A3-MED-STRING-ONLY-VALIDATION` | 8 个 S6PAT02 README 第一屏统一说明“本轮 Owner-flow 治理任务”，明确不改产品 canonical current_task。 |
| `S6PBT01-A3-MED-DASHBOARD-DECISION-POLICY` | Review8 Owner decision policy 移入 `governance/decision_policies/review8_owner_decision_policy.json`，生成器只读取和投影。 |

## 边界

- 治理真相保留：CI run、result commit、changed files、Owner-flow 与产品 canonical 状态分开记录。
- 治理计算不回流到每次开发动作：PR/main 仍走 changed-only fast gate；full dashboard/all validation 仍保留在 scheduled/manual all scope。
- 本轮不改产品运行代码、不移动文件、不触发外部自动化、不重建历史输出。

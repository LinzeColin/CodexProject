# whkmSalary S4PCT02 中文结构验收报告

- 任务：`S4PCT02`
- 验收：`ACC-S4PCT02`
- 结论：中文 owner 可读验收通过；本报告先给人类可读结论，再保留原技术记录。

## 用户可读结论

whkmSalary 的 S4PCT02 建立 `src` / `tests` / `config` / 中文入口的最小结构。工资公式、省份权重、Streamlit 字段默认值、Railway 启动命令和 payroll readiness 状态都没有改变。根目录兼容 wrapper 继续保留，旧 import 和 Procfile 不会失效。

## 中文验收标准

- Owner 能直接看出运行代码、UI、兼容入口、测试、配置和中文入口分别在哪里。
- `config/` 只记录结构合同，不承载未经 owner 证明的业务参数迁移。
- 报告必须明确停止条件和回滚路径。

## 停止条件与结果

- 为了目录美观重写工资计算：`false`
- 启动命令改变但 README 未同步：`false`
- 业务参数无 owner 证明迁入 config：`false`
- 测试绕开根兼容 import：`false`

## 回滚

优先用 git revert 回退 S4PCT02 任务提交。若必须手工恢复，把 `src/whkm_salary/salary_logic.py` 和 `src/whkm_salary/streamlit_app.py` 还原到根目录，移除结构合同和本报告，并恢复治理证据链接。

## 下一步

后续 S5/S6 验收只能确认结构和中文可读性，不得借结构任务改变工资政策或公式。

---

## 原技术记录

# whkmSalary Structure Report

Task: S4PCT02  
Acceptance: ACC-S4PCT02  
Baseline: 9bfe50b2195e8cfc04eb493e028c0f72e1ae0a90

## Scope

S4PCT02 establishes a minimal `src` / `tests` / `config` / Chinese owner-entry structure for whkmSalary. It does not change salary formulas, province weights, Streamlit field defaults, Railway startup commands, or payroll readiness status.

## Active Structure

| Area | Path | Responsibility |
|---|---|---|
| Runtime code | `whkmSalary/src/whkm_salary/salary_logic.py` | Quarterly performance salary calculation implementation. |
| Runtime UI | `whkmSalary/src/whkm_salary/streamlit_app.py` | Streamlit form and display implementation. |
| Compatibility imports | `whkmSalary/salary_logic.py` | Preserves existing `from salary_logic import ...` callers and tests. |
| Compatibility startup | `whkmSalary/streamlit_app.py` | Preserves `Procfile` command and forwards to package UI. |
| Tests | `whkmSalary/tests/` | Boundary, weight, rounding, and structure compatibility coverage. |
| Structure config | `whkmSalary/config/structure_contract.yaml` | Records code/test/config/Chinese-entry ownership only. |
| Machine truth | `whkmSalary/docs/governance/` | Lean v2 source of facts, limitations, and evidence links. |
| Chinese owner entries | `whkmSalary/功能清单`, `whkmSalary/开发记录`, `whkmSalary/模型参数文件` | Human-readable current state, task, and model/parameter surfaces. |

## OLD_TO_NEW_MAP

| Old path | New path | Compatibility |
|---|---|---|
| `whkmSalary/salary_logic.py` | `whkmSalary/src/whkm_salary/salary_logic.py` | Root wrapper remains and re-exports the package module. |
| `whkmSalary/streamlit_app.py` | `whkmSalary/src/whkm_salary/streamlit_app.py` | Root wrapper remains and runs the package module. |

## Stop Conditions

| Stop condition | Result | Evidence |
|---|---:|---|
| whkmSalary large calculation rewrite for appearance | no | Only file location/import boundary changed; formula bodies stay in moved module. |
| Startup command changed without README sync | no | `Procfile` remains unchanged and README records the preserved command. |
| Business parameters moved into config without owner proof | no | `config/` records structure only; payroll parameters remain governed as before. |
| Tests bypass root compatibility imports | no | Existing tests still import `salary_logic`; added structure checks cover package paths. |

## Rollback

Rollback is a single git revert of the S4PCT02 commit. If manual recovery is needed, move `src/whkm_salary/salary_logic.py` back to `salary_logic.py`, move `src/whkm_salary/streamlit_app.py` back to `streamlit_app.py`, remove `src/whkm_salary/`, `config/structure_contract.yaml`, this report, and revert governance evidence links.

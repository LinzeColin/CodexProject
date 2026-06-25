# whkmSalary S4PCT02 中文结构验收报告

- 任务：`S4PCT02`
- 验收：`ACC-S4PCT02`
- 结论：用户可读优先，中文 owner 可读验收通过；本报告先给人类可读结论，再保留原技术记录。
- 验收状态：`通过`

## 用户可读结论

whkmSalary 的 S4PCT02 建立 `src` / `tests` / `config` / 中文入口的最小结构。工资公式、省份权重、Streamlit 字段默认值、Railway 启动命令和 payroll readiness 状态都没有改变。根目录兼容 wrapper 继续保留，旧 import 和 Procfile 不会失效。

## 中文验收标准

- Owner 能直接看出运行代码、UI、兼容入口、测试、配置和中文入口分别在哪里。
- `config/` 只记录结构合同，不承载未经 owner 证明的业务参数迁移。
- 报告必须明确停止条件和回滚路径。

## 停止条件与结果

- 为了目录美观重写工资计算：`未触发`
- 启动命令改变但 README 未同步：`未触发`
- 业务参数无 owner 证明迁入 config：`未触发`
- 测试绕开根兼容 import：`未触发`

## 回滚

优先用 git revert 回退 S4PCT02 任务提交。若必须手工恢复，把 `src/whkm_salary/salary_logic.py` 和 `src/whkm_salary/streamlit_app.py` 还原到根目录，移除结构合同和本报告，并恢复治理证据链接。

## 下一步

后续 S5/S6 验收只能确认结构和中文可读性，不得借结构任务改变工资政策或公式。

---

## 原技术记录

# whkmSalary 结构报告

任务：S4PCT02
验收：ACC-S4PCT02
基线：9bfe50b2195e8cfc04eb493e028c0f72e1ae0a90

## 范围

S4PCT02 为 whkmSalary 建立最小 `src` / `tests` / `config` / 中文 owner 入口结构。工资公式、省份权重、Streamlit 字段默认值、Railway 启动命令和 payroll readiness 状态均未改变。

## 主动结构

| 区域 | 路径 | 职责 |
|---|---|---|
| 运行代码 | `whkmSalary/src/whkm_salary/salary_logic.py` | 季度绩效工资计算实现。 |
| 运行 UI | `whkmSalary/src/whkm_salary/streamlit_app.py` | Streamlit 表单和展示实现。 |
| 兼容 import | `whkmSalary/salary_logic.py` | 保留现有 `from salary_logic import ...` 调用方和测试。 |
| 兼容启动 | `whkmSalary/streamlit_app.py` | 保留 `Procfile` 命令，并转发到 package UI。 |
| 测试 | `whkmSalary/tests/` | 边界、权重、舍入和结构兼容性覆盖。 |
| 结构配置 | `whkmSalary/config/structure_contract.yaml` | 只记录代码、测试、配置和中文入口归属。 |
| 机器事实 | `whkmSalary/docs/governance/` | Lean v2 事实、限制和证据链接来源。 |
| 中文 owner 入口 | `whkmSalary/功能清单`, `whkmSalary/开发记录`, `whkmSalary/模型参数文件` | 人类可读的当前状态、任务和模型/参数表面。 |

## 旧到新路径映射（OLD_TO_NEW_MAP）

| 旧路径 | 新路径 | 兼容性 |
|---|---|---|
| `whkmSalary/salary_logic.py` | `whkmSalary/src/whkm_salary/salary_logic.py` | 根 wrapper 保留，并重新导出 package module。 |
| `whkmSalary/streamlit_app.py` | `whkmSalary/src/whkm_salary/streamlit_app.py` | 根 wrapper 保留，并运行 package module。 |

## 停止条件结果

| 停止条件 | 结果 | 证据 |
|---|---:|---|
| 为了目录美观大范围重写 whkmSalary 计算 | 未触发 | 只改变文件位置和 import 边界；公式主体保留在移动后的 module 中。 |
| 启动命令改变但 README 未同步 | 未触发 | `Procfile` 未改变，README 记录保留的命令。 |
| 业务参数无 owner 证明迁入 config | 未触发 | `config/` 只记录结构；payroll 参数仍按原治理管理。 |
| 测试绕开根兼容 import | 未触发 | 既有测试仍 import `salary_logic`；新增结构检查覆盖 package 路径。 |

## 回滚方式

回滚优先使用一次 git revert 回退 S4PCT02 提交。若必须手工恢复，把 `src/whkm_salary/salary_logic.py` 还原为 `salary_logic.py`，把 `src/whkm_salary/streamlit_app.py` 还原为 `streamlit_app.py`，移除 `src/whkm_salary/`、`config/structure_contract.yaml`、本报告，并恢复治理证据链接。

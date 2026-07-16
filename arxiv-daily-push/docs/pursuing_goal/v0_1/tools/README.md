# ADP V0.1 · 任务执行与独立验证工具（S0-P03-T008）

> 目标：**一个任务一个结果、可回滚、可机器验收、由独立上下文复核**。防止大包开发和虚假完成。

## 组件

| 文件 | 作用 |
|---|---|
| `../TASK_INDEX.csv` | 90 任务机器索引（task_id / stage / phase / priority / size / dependencies / release_mode / …），源自最终包 `06_TASK_INDEX.csv`。 |
| `check_dag.py` | **依赖 DAG 检查**：90 个 task_id 唯一、依赖引用存在、无环（拓扑）。 |
| `validate_evidence.py` | **证据 schema 校验**：必需文件齐全、含完成标记、未自签 PASS、cost_value 可解析。缺证据→INCOMPLETE。 |
| `task_runner.py` | **一任务一结果**：查 TASK_INDEX、校验依赖已 READY、校验本任务证据。输出单一状态。 |
| `EVIDENCE_TEMPLATE.md` | 每任务证据包模板 + TASK_REPORT 骨架 + 提交前自检。 |

## 用法

```bash
cd docs/pursuing_goal/v0_1
python3 tools/check_dag.py                     # 期望 RESULT: PASS（90 唯一 / 无环）
python3 tools/validate_evidence.py <TASK_ID>   # READY_FOR_INDEPENDENT_VERIFICATION 或 INCOMPLETE
python3 tools/task_runner.py <TASK_ID>         # BLOCKED_BY_DEPS / INCOMPLETE / READY_FOR_INDEPENDENT_VERIFICATION
```

## 硬规则（反黑洞）

- **绝不 PASS**：所有工具最强只到 `READY_FOR_INDEPENDENT_VERIFICATION`；PASS/FAIL 由独立上下文判定，实现者不自签。
- **缺证据 = INCOMPLETE**：任一必需证据缺失即 INCOMPLETE，不得声明完成。
- **依赖门**：task_runner 校验每个依赖已至少 READY，未就绪→BLOCKED_BY_DEPS。
- **一任务一结果**：runner 只处理单个 task_id。
- **只读**：三个工具都不修改任何仓库/生产文件。

## 与治理门的关系

这些工具是**任务级**自检（证据/依赖/DAG）；仓库级发布仍走 `scripts/lean_governance.py ci --changed-only`（治理同步门）与 GitHub CI。两者叠加：任务 READY + 治理门 SHIP + CI 双绿 + 独立复核 PASS 才算真正完成。

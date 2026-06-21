# OWNER_STATUS

生成方式：由 `scripts/generate_governance_dashboard.py` 从机器事实源生成；不要手工编辑。

## 1. 当前结论

EVA_OS 当前处于 B 阶段 / GOV-SEMANTIC-EVA-001-in-progress gate；CI 模式为 required，机器事实源显示模型 16 个、公式 16 个、参数 189 个。

## 2. 更新时间与 Commit

- 生成标记：`DETERMINISTIC_GENERATION`
- 仓库提交：`CURRENT_CHECKOUT`
- 最近事件时间：`2026-06-21T00:00:00+10:00`
- 最近事件提交证据：`PENDING`

## 3. 本轮最重要变化

Add machine selectors for 52 EVA_OS active parameters and implementation fingerprints for 16 active formulas without runtime behavior changes.

## 4. 模型、公式、参数旧值到新值

- 版本变化：current_gate: GOV-P13-required-passed -> GOV-SEMANTIC-EVA-001-in-progress; current_iteration: ITER-20260620-EVA-002 -> ITER-20260621-EVA-003; current_phase: A -> B; product_version: 0.1.0 unchanged
- 模型/公式变化：human_review_required: none at formula level in this rollout; machine_refs: implementation_refs on FORM-001 through FORM-016; semantic_formulas_checked: 16
- 参数变化：active_values_changed: 0; human_review_required_count: 137; human_review_task_id: GOV-SEMANTIC-EVA-001; semantic_parameters_checked: 52

## 5. 为什么改变及证据等级

- 原因：Add machine selectors for 52 EVA_OS active parameters and implementation fingerprints for 16 active formulas without runtime behavior changes.
- 证据等级：`EXTRACTED`
- 证据引用：EVA_OS/docs/governance/parameter_registry.csv, EVA_OS/docs/governance/formula_registry.yaml, governance/run_manifests/GOV-SEMANTIC-EVA-EXTRACT-001.json

## 6. 对输出、风险和业务决策的影响

formula_fingerprints_added: 16; runtime_behavior: unchanged; semantic_coverage: in_progress

## 7. 当前置信度和证据新鲜度

- 置信度：`Medium`
- 证据新鲜度：`3 unbound event(s)`
- 语义覆盖：`in_progress`
- 语义覆盖任务：`GOV-SEMANTIC-EVA-001`
- UNKNOWN/HUMAN_REVIEW_REQUIRED 数量：`404`
- 未绑定事件数量：`3`

## 8. 需要项目所有者决定的事项

Resolve source rationale for cross-source validation tolerance.

## 9. 当前前三风险

1. Semantic extractor coverage is in_progress; rollout task GOV-SEMANTIC-EVA-001 remains open.
2. Blocker: calibration/source rationale gaps tracked by `TASK-EVA-B-001` through `TASK-EVA-B-008`
3. UNKNOWN/HUMAN_REVIEW_REQUIRED facts: 404

## 10. 下一项可执行任务及 Acceptance

- 下一任务：`TASK-EVA-B-003`
- 状态：`blocked`
- Acceptance：ACC-EVA-B-003
- 选择理由：status=blocked; phase=B; current_phase=B; unmet_dependencies=none; score=145

## 11. 阻塞负责人和解除条件

- 负责人：Project owner
- 解除条件：Meet acceptance ACC-EVA-B-003

## 12. UNKNOWN 与过期证据数量

- UNKNOWN/HUMAN_REVIEW_REQUIRED：`404`
- 过期或未绑定证据：`3`

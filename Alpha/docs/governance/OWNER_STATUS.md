# OWNER_STATUS

生成方式：由 `scripts/generate_governance_dashboard.py` 从机器事实源生成；不要手工编辑。

## 1. 当前结论

Alpha 当前处于 B 阶段 / GOV-SEMANTIC-ALPHA-in-progress gate；CI 模式为 required，机器事实源显示模型 9 个、公式 9 个、参数 55 个。

## 2. 更新时间与 Commit

- 生成标记：`DETERMINISTIC_GENERATION`
- 仓库提交：`CURRENT_CHECKOUT`
- 最近事件时间：`2026-06-21T13:58:00Z`
- 最近事件提交证据：`PENDING`

## 3. 本轮最重要变化

Validated Alpha semantic extractor rollout locally and recorded blocked focused tests caused by missing local PyYAML dependency.

## 4. 模型、公式、参数旧值到新值

- 版本变化：current_gate: GOV-G4-ALPHA-REQUIRED -> GOV-SEMANTIC-ALPHA-in-progress; current_iteration: ITER-20260620-ALPHA-001 -> ITER-20260621-ALPHA-001; current_phase: E -> B; product_version: 0.1.0 unchanged
- 模型/公式变化：formula_fingerprints_added: 9; human_review_formula_ids: none; semantic_formulas_checked: 9
- 参数变化：active_values_changed: 0; human_review_parameter_count: 13; human_review_task_id: GOV-SEMANTIC-ALPHA-001; semantic_parameters_checked: 42

## 5. 为什么改变及证据等级

- 原因：Validated Alpha semantic extractor rollout locally and recorded blocked focused tests caused by missing local PyYAML dependency.
- 证据等级：`EXTRACTED`
- 证据引用：Alpha/docs/governance/parameter_registry.csv, Alpha/docs/governance/formula_registry.yaml, governance/run_manifests/GOV-SEMANTIC-ALPHA-EXTRACT-001.json, tests/governance/test_project_governance_validator.py

## 6. 对输出、风险和业务决策的影响

runtime_behavior: unchanged; semantic_coverage: planned -> in_progress

## 7. 当前置信度和证据新鲜度

- 置信度：`Medium`
- 证据新鲜度：`2 unbound event(s)`
- 语义覆盖：`in_progress`
- 语义覆盖任务：`GOV-SEMANTIC-ALPHA-001`
- UNKNOWN/HUMAN_REVIEW_REQUIRED 数量：`68`
- 未绑定事件数量：`2`

## 8. 需要项目所有者决定的事项

Resolve production validation and execution-policy UNKNOWN items before release readiness.

## 9. 当前前三风险

1. Semantic extractor coverage is in_progress; rollout task GOV-SEMANTIC-ALPHA-001 remains open.
2. Blocker: live execution policy and production validation remain blocked under `TASK-ALPHA-B-001`.
3. UNKNOWN/HUMAN_REVIEW_REQUIRED facts: 68

## 10. 下一项可执行任务及 Acceptance

- 下一任务：`TASK-ALPHA-B-001`
- 状态：`blocked`
- Acceptance：ACC-ALPHA-B-001
- 选择理由：status=blocked; phase=B; current_phase=B; unmet_dependencies=none; score=152

## 11. 阻塞负责人和解除条件

- 负责人：Project owner
- 解除条件：Meet acceptance ACC-ALPHA-B-001

## 12. UNKNOWN 与过期证据数量

- UNKNOWN/HUMAN_REVIEW_REQUIRED：`68`
- 过期或未绑定证据：`2`

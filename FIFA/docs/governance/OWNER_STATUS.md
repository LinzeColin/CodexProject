# OWNER_STATUS

生成方式：由 `scripts/generate_governance_dashboard.py` 从机器事实源生成；不要手工编辑。

## 1. 当前结论

FIFA 当前处于 B 阶段 / GOV-SEMANTIC-FIFA-in-progress gate；CI 模式为 required，机器事实源显示模型 11 个、公式 11 个、参数 117 个。

## 2. 更新时间与 Commit

- 生成标记：`DETERMINISTIC_GENERATION`
- 仓库提交：`CURRENT_CHECKOUT`
- 最近事件时间：`2026-06-21T14:22:12Z`
- 最近事件提交证据：`PENDING`

## 3. 本轮最重要变化

Add machine source selectors for 91 active FIFA parameters and AST implementation fingerprints for 10 active formulas; keep 17 active parameters HUMAN_REVIEW_REQUIRED under GOV-SEMANTIC-FIFA-001.

## 4. 模型、公式、参数旧值到新值

- 版本变化：current_gate: GOV-P13-required-passed -> GOV-SEMANTIC-FIFA-in-progress; current_iteration: ITER-20260620-001 -> ITER-20260621-FIFA-001; current_phase: A -> B; product_version: 0.1.0 unchanged
- 模型/公式变化：formula_fingerprints_added: 10; human_review_formula_ids: none; semantic_formulas_checked: 10
- 参数变化：active_values_changed: governance registry values corrected where previous summaries were count labels rather than exact extracted values; runtime behavior unchanged; human_review_parameter_count: 17; human_review_task_id: GOV-SEMANTIC-FIFA-001; semantic_parameters_checked: 91

## 5. 为什么改变及证据等级

- 原因：Add machine source selectors for 91 active FIFA parameters and AST implementation fingerprints for 10 active formulas; keep 17 active parameters HUMAN_REVIEW_REQUIRED under GOV-SEMANTIC-FIFA-001.
- 证据等级：`EXTRACTED`
- 证据引用：FIFA/docs/governance/parameter_registry.csv, FIFA/docs/governance/formula_registry.yaml, governance/run_manifests/GOV-SEMANTIC-FIFA-EXTRACT-001.json

## 6. 对输出、风险和业务决策的影响

runtime_behavior: unchanged; semantic_coverage: planned -> in_progress

## 7. 当前置信度和证据新鲜度

- 置信度：`Medium`
- 证据新鲜度：`3 unbound event(s)`
- 语义覆盖：`in_progress`
- 语义覆盖任务：`GOV-SEMANTIC-FIFA-001`
- UNKNOWN/HUMAN_REVIEW_REQUIRED 数量：`108`
- 未绑定事件数量：`3`

## 8. 需要项目所有者决定的事项

Add extractors for parser constants, validation rules, and active governance formulas.

## 9. 当前前三风险

1. Semantic extractor coverage is in_progress; rollout task GOV-SEMANTIC-FIFA-001 remains open.
2. Blocker: TASK-FIFA-B-001, TASK-FIFA-B-002, TASK-FIFA-C-001, TASK-FIFA-C-002, TASK-FIFA-D-001, TASK-FIFA-D-002, TASK-FIFA-E-001, TASK-FIFA-E-002
3. UNKNOWN/HUMAN_REVIEW_REQUIRED facts: 108

## 10. 下一项可执行任务及 Acceptance

- 下一任务：`GOV-SEMANTIC-FIFA-001`
- 状态：`in_progress`
- Acceptance：ACC-SEMANTIC-FIFA-001
- 选择理由：status=in_progress; phase=B; current_phase=B; unmet_dependencies=none; score=114

## 11. 阻塞负责人和解除条件

- 负责人：Codex/governance runner
- 解除条件：Meet acceptance ACC-SEMANTIC-FIFA-001

## 12. UNKNOWN 与过期证据数量

- UNKNOWN/HUMAN_REVIEW_REQUIRED：`108`
- 过期或未绑定证据：`3`

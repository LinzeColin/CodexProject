# OWNER_STATUS

生成方式：由 `scripts/generate_governance_dashboard.py` 从机器事实源生成；不要手工编辑。

## 1. 当前结论

OpenAIDatabase 当前处于 B 阶段 / GOV-SEMANTIC-OAIDB-in-progress gate；CI 模式为 required，机器事实源显示模型 11 个、公式 11 个、参数 92 个。

## 2. 更新时间与 Commit

- 生成标记：`DETERMINISTIC_GENERATION`
- 仓库提交：`CURRENT_CHECKOUT`
- 最近事件时间：`2026-06-21T13:15:45Z`
- 最近事件提交证据：`PENDING`

## 3. 本轮最重要变化

Bind generated dashboard, STATUS, and OWNER_STATUS outputs to the OpenAIDatabase semantic extractor rollout diff.

## 4. 模型、公式、参数旧值到新值

- 版本变化：current_gate: TASK-OAI-C-002-PERSONALIZATION-ARCHITECTURE -> GOV-SEMANTIC-OAIDB-in-progress; current_iteration: ITER-20260621-OAI-003 -> ITER-20260621-OAI-004; current_phase: C -> B; product_version: 0.2.0 unchanged
- 模型/公式变化：human_review_formula_ids: FORM-010; semantic_formulas_checked: 10
- 参数变化：active_values_changed: documentation correction only for PARAM-086; runtime value unchanged; human_review_task_id: GOV-SEMANTIC-OAIDB-001; semantic_parameters_checked: 28

## 5. 为什么改变及证据等级

- 原因：Bind generated dashboard, STATUS, and OWNER_STATUS outputs to the OpenAIDatabase semantic extractor rollout diff.
- 证据等级：`EXTRACTED`
- 证据引用：GOVERNANCE_DASHBOARD.md, OpenAIDatabase/docs/governance/STATUS.md, OpenAIDatabase/docs/governance/OWNER_STATUS.md

## 6. 对输出、风险和业务决策的影响

formula_fingerprints_added: 10; human_review_formula_ids: FORM-010; runtime_behavior: unchanged; semantic_coverage: planned -> in_progress

## 7. 当前置信度和证据新鲜度

- 置信度：`Medium`
- 证据新鲜度：`6 unbound event(s)`
- 语义覆盖：`in_progress`
- 语义覆盖任务：`GOV-SEMANTIC-OAIDB-001`
- UNKNOWN/HUMAN_REVIEW_REQUIRED 数量：`345`
- 未绑定事件数量：`6`

## 8. 需要项目所有者决定的事项

Resolve UNKNOWN calibration evidence for heuristic weights and thresholds.

## 9. 当前前三风险

1. Semantic extractor coverage is in_progress; rollout task GOV-SEMANTIC-OAIDB-001 remains open.
2. Blocker: remaining complex branch rules, TypeScript writeback semantics, and heuristic calibration evidence are HUMAN_REVIEW_REQUIRED or UNKNOWN under `GOV-SEMANTIC-OAIDB-001` and `TASK-OAI-B-001`
3. UNKNOWN/HUMAN_REVIEW_REQUIRED facts: 345

## 10. 下一项可执行任务及 Acceptance

- 下一任务：`TASK-OAI-B-001`
- 状态：`blocked`
- Acceptance：ACC-OAI-B-001
- 选择理由：status=blocked; phase=B; current_phase=B; unmet_dependencies=none; score=136

## 11. 阻塞负责人和解除条件

- 负责人：Project owner
- 解除条件：Meet acceptance ACC-OAI-B-001

## 12. UNKNOWN 与过期证据数量

- UNKNOWN/HUMAN_REVIEW_REQUIRED：`345`
- 过期或未绑定证据：`6`

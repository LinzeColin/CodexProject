# OWNER_STATUS

生成方式：由 `scripts/generate_governance_dashboard.py` 从机器事实源生成；不要手工编辑。

## 1. 当前结论

whkmSalary 当前处于 B 阶段 / GOV-SEMANTIC-WHKM-in-progress gate；CI 模式为 required，机器事实源显示模型 2 个、公式 10 个、参数 80 个。

## 2. 更新时间与 Commit

- 生成标记：`DETERMINISTIC_GENERATION`
- 仓库提交：`CURRENT_CHECKOUT`
- 最近事件时间：`2026-06-21T22:45:05+10:00`
- 最近事件提交证据：`PENDING`

## 3. 本轮最重要变化

Added machine semantic selectors for whkmSalary salary constants and formula fingerprints without changing salary runtime behavior.

## 4. 模型、公式、参数旧值到新值

- 版本变化：current_gate: GOV-G4-WHKM-REQUIRED -> GOV-SEMANTIC-WHKM-in-progress; current_iteration: ITER-20260620-WHKM-001 -> ITER-20260621-WHKM-001; current_phase: E -> B; product_version: 0.0.0 unchanged
- 模型/公式变化：formula_fingerprints_added: 9; human_review_formula_ids: FORM-010; semantic_formulas_checked: 9
- 参数变化：active_values_changed: 0; human_review_parameter_ids: PARAM-004, PARAM-005; semantic_parameters_checked: 78

## 5. 为什么改变及证据等级

- 原因：Added machine semantic selectors for whkmSalary salary constants and formula fingerprints without changing salary runtime behavior.
- 证据等级：`EXTRACTED`
- 证据引用：governance/run_manifests/GOV-SEMANTIC-WHKM-EXTRACT-001.json, whkmSalary/docs/governance/parameter_registry.csv, whkmSalary/docs/governance/formula_registry.yaml

## 6. 对输出、风险和业务决策的影响

runtime_behavior: unchanged; semantic_coverage: planned -> in_progress

## 7. 当前置信度和证据新鲜度

- 置信度：`Medium`
- 证据新鲜度：`3 unbound event(s)`
- 语义覆盖：`in_progress`
- 语义覆盖任务：`GOV-SEMANTIC-WHKM-001`
- UNKNOWN/HUMAN_REVIEW_REQUIRED 数量：`173`
- 未绑定事件数量：`3`

## 8. 需要项目所有者决定的事项

Resolve salary policy source, jurisdiction, effective date, tax basis, boundary behavior, and rounding policy evidence.

## 9. 当前前三风险

1. Semantic extractor coverage is in_progress; rollout task GOV-SEMANTIC-WHKM-001 remains open.
2. Blocker: `TASK-WHKM-B-001` for policy/source/effective date/rounding/boundary evidence; `GOV-SEMANTIC-WHKM-001` retains human review for `PARAM-004`, `PARAM-005`, and `FORM-010`.
3. UNKNOWN/HUMAN_REVIEW_REQUIRED facts: 173

## 10. 下一项可执行任务及 Acceptance

- 下一任务：`TASK-WHKM-B-001`
- 状态：`blocked`
- Acceptance：ACC-WHKM-B-001
- 选择理由：status=blocked; phase=B; current_phase=B; unmet_dependencies=none; score=108

## 11. 阻塞负责人和解除条件

- 负责人：Project owner
- 解除条件：Meet acceptance ACC-WHKM-B-001

## 12. UNKNOWN 与过期证据数量

- UNKNOWN/HUMAN_REVIEW_REQUIRED：`173`
- 过期或未绑定证据：`3`

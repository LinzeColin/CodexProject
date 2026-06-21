# OWNER_STATUS

生成方式：由 `scripts/generate_governance_dashboard.py` 从机器事实源生成；不要手工编辑。

## 1. 当前结论

EEI 当前处于 B 阶段 / GOV-SEMANTIC-EEI-001-PARTIAL-EXTRACTORS gate；CI 模式为 required，机器事实源显示模型 12 个、公式 12 个、参数 61 个。

## 2. 更新时间与 Commit

- 生成标记：`DETERMINISTIC_GENERATION`
- 仓库提交：`CURRENT_CHECKOUT`
- 最近事件时间：`2026-06-21T06:20:00Z`
- 最近事件提交证据：`PENDING`

## 3. 本轮最重要变化

Added partial EEI machine semantic extraction metadata without changing business behavior.

## 4. 模型、公式、参数旧值到新值

- 版本变化：current_gate: TASK-T1307-A209-RUNNER-REPAIR-REMOTE-CI -> GOV-SEMANTIC-EEI-001-PARTIAL-EXTRACTORS; current_iteration: ITER-20260621-015 -> ITER-20260621-016; current_phase: D -> B; product_version: 0.1.0 unchanged
- 模型/公式变化：deferred: FORM-012 threshold-control rule; machine_refs: csv_row:EEI/data/formula_registry.csv::formula_id=<legacy_formula_id>; semantic_formulas_checked: 10
- 参数变化：active_values_changed: 0; semantic_parameters_checked: 54; unknown_parameters_deferred: PARAM-052, PARAM-053, +5 more

## 5. 为什么改变及证据等级

- 原因：Added partial EEI machine semantic extraction metadata without changing business behavior.
- 证据等级：`EXTRACTED`
- 证据引用：governance/run_manifests/GOV-SEMANTIC-EEI-EXTRACT-001.json, EEI/docs/governance/parameter_registry.csv, EEI/docs/governance/formula_registry.yaml, EEI/artifacts/tests/a200/t1215_clean_room_release.json, EEI/artifacts/tests/a200/Enterprise_Ecosystem_Intelligence_clean_room_t1215.zip, EEI/artifacts/release_evidence_t1211.json, +1 more

## 6. 对输出、风险和业务决策的影响

formula_fingerprints_added: 10; human_review_required: FORM-012; runtime_behavior: unchanged

## 7. 当前置信度和证据新鲜度

- 置信度：`Medium`
- 证据新鲜度：`15 unbound event(s)`
- 语义覆盖：`in_progress`
- 语义覆盖任务：`GOV-SEMANTIC-EEI-001`
- UNKNOWN/HUMAN_REVIEW_REQUIRED 数量：`153`
- 未绑定事件数量：`15`

## 8. 需要项目所有者决定的事项

Implement real data ingestion, entity resolution and evidence chain for the Golden Vertical

## 9. 当前前三风险

1. Semantic extractor coverage is in_progress; rollout task GOV-SEMANTIC-EEI-001 remains open.
2. Blocker: 7 active motion parameters still have UNKNOWN runtime activation evidence, and FORM-012 remains HUMAN_REVIEW_REQUIRED.
3. UNKNOWN/HUMAN_REVIEW_REQUIRED facts: 153

## 10. 下一项可执行任务及 Acceptance

- 下一任务：`TASK-T1301`
- 状态：`in_progress`
- Acceptance：ACC-A202
- 选择理由：status=in_progress; phase=C; current_phase=B; unmet_dependencies=none; score=122

## 11. 阻塞负责人和解除条件

- 负责人：Codex/governance runner
- 解除条件：Meet acceptance ACC-A202

## 12. UNKNOWN 与过期证据数量

- UNKNOWN/HUMAN_REVIEW_REQUIRED：`153`
- 过期或未绑定证据：`15`

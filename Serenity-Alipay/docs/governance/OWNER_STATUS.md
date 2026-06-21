# OWNER_STATUS

生成方式：由 `scripts/generate_governance_dashboard.py` 从机器事实源生成；不要手工编辑。

## 1. 当前结论

Serenity-Alipay 当前处于 B 阶段 / GOV-REVIEW6-B-SEMANTIC-EXTRACT gate；CI 模式为 required，机器事实源显示模型 5 个、公式 12 个、参数 49 个。

## 2. 更新时间与 Commit

- 生成标记：`DETERMINISTIC_GENERATION`
- 仓库提交：`CURRENT_CHECKOUT`
- 最近事件时间：`2026-06-21T19:09:37+10:00`
- 最近事件提交证据：`PENDING`

## 3. 本轮最重要变化

Added Serenity-Alipay semantic extraction pilot for active parameters and formulas without changing business behavior.

## 4. 模型、公式、参数旧值到新值

- 版本变化：current_gate: GOV-G3-SERENITY-BASELINE -> GOV-REVIEW6-B-SEMANTIC-EXTRACT; current_iteration: ITER-20260621-001 -> ITER-20260621-002; current_phase: A -> B; product_version: 0.1.0 unchanged
- 模型/公式变化：FORM-001..FORM-012: implementation_refs, implementation_fingerprint, verified_at, evidence_hash added; FORM-008: post-renormalization cap caveat recorded; max weights for 1..5 candidates machine-observed
- 参数变化：PARAM-001..PARAM-049: source_selector, extracted_value, verified_at, last_verified_commit, evidence_hash added; active_values_changed: 0

## 5. 为什么改变及证据等级

- 原因：Added Serenity-Alipay semantic extraction pilot for active parameters and formulas without changing business behavior.
- 证据等级：`EXTRACTED`
- 证据引用：Serenity-Alipay/docs/governance/parameter_registry.csv, Serenity-Alipay/docs/governance/formula_registry.yaml, tests/governance/test_project_governance_validator.py, scripts/validate_semantic_extractors.py

## 6. 对输出、风险和业务决策的影响

formula_fingerprints_added: 12; runtime_behavior: unchanged; semantic_extractors_enabled_for: Serenity-Alipay

## 7. 当前置信度和证据新鲜度

- 置信度：`Medium`
- 证据新鲜度：`3 unbound event(s)`
- 语义覆盖：`machine_verified`
- 语义覆盖任务：`TASK-B-003`
- UNKNOWN/HUMAN_REVIEW_REQUIRED 数量：`0`
- 未绑定事件数量：`3`

## 8. 需要项目所有者决定的事项

Close empirical calibration UNKNOWNs for score weights, grade thresholds, and Top5 allocation constants.

## 9. 当前前三风险

1. Blocker: semantic extractor pilot currently covers Serenity-Alipay only; other projects need separate migration tasks.
2. Unbound or stale evidence events: 3
3. Review6-B is a Serenity pilot; other projects still need semantic extractors before the full Review6 objective is complete.

## 10. 下一项可执行任务及 Acceptance

- 下一任务：`TASK-B-001`
- 状态：`planned`
- Acceptance：ACC-B-001
- 选择理由：status=planned; phase=B; current_phase=B; unmet_dependencies=TASK-A-002; score=59

## 11. 阻塞负责人和解除条件

- 负责人：Project owner
- 解除条件：Complete dependencies TASK-A-002

## 12. UNKNOWN 与过期证据数量

- UNKNOWN/HUMAN_REVIEW_REQUIRED：`0`
- 过期或未绑定证据：`3`

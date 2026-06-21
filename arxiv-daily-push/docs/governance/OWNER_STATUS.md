# OWNER_STATUS

生成方式：由 `scripts/generate_governance_dashboard.py` 从机器事实源生成；不要手工编辑。

## 1. 当前结论

arxiv-daily-push 当前处于 E 阶段 / GOV-SEMANTIC-ADP-PLANNED gate；CI 模式为 required，机器事实源显示模型 29 个、公式 31 个、参数 153 个。

## 2. 更新时间与 Commit

- 生成标记：`DETERMINISTIC_GENERATION`
- 仓库提交：`CURRENT_CHECKOUT`
- 最近事件时间：`2026-06-22T12:35:00+10:00`
- 最近事件提交证据：`PENDING`

## 3. 本轮最重要变化

Merged latest main governance requirements and added a planned semantic_coverage rollout contract for arXiv Daily Push without claiming machine-verified semantic extraction or changing runtime behavior.

## 4. 模型、公式、参数旧值到新值

- 版本变化：current_gate: GOV-SEMANTIC-ADP-PLANNED; current_iteration: ITER-20260621-031; current_phase: E; product_version: 0.11.19
- 模型/公式变化：Added FORM-ADP-030 trial start workflow contract gate.
- 参数变化：Added PARAM-ADP-144 through PARAM-ADP-148.

## 5. 为什么改变及证据等级

- 原因：Merged latest main governance requirements and added a planned semantic_coverage rollout contract for arXiv Daily Push without claiming machine-verified semantic extraction or changing runtime behavior.
- 证据等级：`EXTRACTED`
- 证据引用：governance/projects.yaml, arxiv-daily-push/docs/governance/delivery_tasks.yaml, governance/run_manifests/GOV-SEMANTIC-ADP-PLANNED-001.json

## 6. 对输出、风险和业务决策的影响

Added MOD-ADP-028 adp-trial-start-workflow-v1.

## 7. 当前置信度和证据新鲜度

- 置信度：`Medium`
- 证据新鲜度：`38 unbound event(s)`
- 语义覆盖：`planned`
- 语义覆盖任务：`GOV-SEMANTIC-ADP-001`
- UNKNOWN/HUMAN_REVIEW_REQUIRED 数量：`0`
- 未绑定事件数量：`38`

## 8. 需要项目所有者决定的事项

Plan machine semantic coverage for arXiv Daily Push active parameter values and formula implementation fingerprints under the latest CodexProject governance standard.

## 9. 当前前三风险

1. Semantic extractor coverage is planned; rollout task GOV-SEMANTIC-ADP-001 remains open.
2. Blocker: Semantic coverage remains planned and not machine verified; production launch remains blocked while PR #14 is draft and unmerged; production acceptance still requires a passing default-branch trial start workflow run, live source ingest pass on the runner, real SMTP and Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries; those are not claimed by this handoff.
3. Unbound or stale evidence events: 38

## 10. 下一项可执行任务及 Acceptance

- 下一任务：`GOV-SEMANTIC-ADP-001`
- 状态：`planned`
- Acceptance：ACC-SEMANTIC-ADP-001
- 选择理由：status=planned; phase=E; current_phase=E; unmet_dependencies=none; score=112

## 11. 阻塞负责人和解除条件

- 负责人：Codex/governance runner
- 解除条件：Meet acceptance ACC-SEMANTIC-ADP-001

## 12. UNKNOWN 与过期证据数量

- UNKNOWN/HUMAN_REVIEW_REQUIRED：`0`
- 过期或未绑定证据：`38`

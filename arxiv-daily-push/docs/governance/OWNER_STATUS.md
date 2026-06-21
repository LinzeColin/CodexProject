# OWNER_STATUS

生成方式：由 `scripts/generate_governance_dashboard.py` 从机器事实源生成；不要手工编辑。

## 1. 当前结论

arxiv-daily-push 当前处于 E 阶段 / GOV-SEMANTIC-ADP-EXPANDED gate；CI 模式为 required，机器事实源显示模型 29 个、公式 31 个、参数 153 个。

## 2. 更新时间与 Commit

- 生成标记：`DETERMINISTIC_GENERATION`
- 仓库提交：`CURRENT_CHECKOUT`
- 最近事件时间：`2026-06-22T03:31:12+10:00`
- 最近事件提交证据：`PENDING`

## 3. 本轮最重要变化

Expanded arXiv Daily Push semantic coverage to 72 active parameters and all 31 active formulas while leaving 80 active parameters HUMAN_REVIEW_REQUIRED.

## 4. 模型、公式、参数旧值到新值

- 版本变化：current_gate: GOV-SEMANTIC-ADP-EXPANDED; current_iteration: ITER-20260621-034; current_phase: E; product_version: 0.11.19
- 模型/公式变化：Added semantic metadata and implementation fingerprints for the remaining 22 active formulas; all 31 active formulas are now MACHINE_VERIFIED under GOV-SEMANTIC-ADP-001.
- 参数变化：Added implementation/config/test-backed semantic selectors for 27 more active parameters; 80 active parameters remain HUMAN_REVIEW_REQUIRED under GOV-SEMANTIC-ADP-001.

## 5. 为什么改变及证据等级

- 原因：Expanded arXiv Daily Push semantic coverage to 72 active parameters and all 31 active formulas while leaving 80 active parameters HUMAN_REVIEW_REQUIRED.
- 证据等级：`EXTRACTED`
- 证据引用：governance/run_manifests/GOV-SEMANTIC-ADP-EXTRACT-002.json, arxiv-daily-push/docs/governance/parameter_registry.csv, arxiv-daily-push/docs/governance/formula_registry.yaml

## 6. 对输出、风险和业务决策的影响

No runtime model behavior change.

## 7. 当前置信度和证据新鲜度

- 置信度：`Medium`
- 证据新鲜度：`41 unbound event(s)`
- 语义覆盖：`in_progress`
- 语义覆盖任务：`GOV-SEMANTIC-ADP-001`
- UNKNOWN/HUMAN_REVIEW_REQUIRED 数量：`80`
- 未绑定事件数量：`41`

## 8. 需要项目所有者决定的事项

Plan machine semantic coverage for arXiv Daily Push active parameter values and formula implementation fingerprints under the latest CodexProject governance standard.

## 9. 当前前三风险

1. Semantic extractor coverage is in_progress; rollout task GOV-SEMANTIC-ADP-001 remains open.
2. Blocker: Semantic coverage is now in progress with 72 machine-checked active parameters and all 31 active formulas; 80 active parameters remain HUMAN_REVIEW_REQUIRED under `GOV-SEMANTIC-ADP-001`. PR #28 is merged to `main`; production launch remains blocked by missing explicit launch confirmation and missing durable readiness refs for `default_branch_ref`, `runner_ref`, `smtp_secret_ref`, `release_target_ref`, `workflow_vars_ref`, and `trial_start_workflow_ref`; no GitHub Actions workflow runs or combined status checks exist for merge commit `cc893e4e11ffe690a8f0d6010053c7a1ab5a09b4`; production acceptance still requires a passing default-branch trial start workflow run, live source ingest pass on the runner, real SMTP and Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries.
3. UNKNOWN/HUMAN_REVIEW_REQUIRED facts: 80

## 10. 下一项可执行任务及 Acceptance

- 下一任务：`GOV-SEMANTIC-ADP-001`
- 状态：`in_progress`
- Acceptance：ACC-SEMANTIC-ADP-001
- 选择理由：status=in_progress; phase=E; current_phase=E; unmet_dependencies=none; score=120

## 11. 阻塞负责人和解除条件

- 负责人：Codex/governance runner
- 解除条件：Meet acceptance ACC-SEMANTIC-ADP-001

## 12. UNKNOWN 与过期证据数量

- UNKNOWN/HUMAN_REVIEW_REQUIRED：`80`
- 过期或未绑定证据：`41`

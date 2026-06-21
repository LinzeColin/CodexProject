# OWNER_STATUS

生成方式：由 `scripts/generate_governance_dashboard.py` 从机器事实源生成；不要手工编辑。

## 1. 当前结论

arxiv-daily-push 当前处于 E 阶段 / ADP-PHASE11-PRODUCTION-TRIAL-START-BLOCKED gate；CI 模式为 required，机器事实源显示模型 30 个、公式 32 个、参数 161 个。

## 2. 更新时间与 Commit

- 生成标记：`DETERMINISTIC_GENERATION`
- 仓库提交：`CURRENT_CHECKOUT`
- 最近事件时间：`2026-06-22T18:00:00+10:00`
- 最近事件提交证据：`PENDING`

## 3. 本轮最重要变化

Added machine-checked GitHub Actions contents: write permission requirements to the trial-start and scheduled production workflows so controlled Release evidence can be created after explicit enablement while uploads remain disabled by default.

## 4. 模型、公式、参数旧值到新值

- 版本变化：current_gate: ADP-PHASE11-PRODUCTION-TRIAL-START-BLOCKED; current_iteration: ITER-20260621-040; current_phase: E; product_version: 0.11.21
- 模型/公式变化：Refreshed FORM-ADP-020 and FORM-ADP-030 implementation fingerprints after adding Release write permission checks.
- 参数变化：Added PARAM-ADP-160 and PARAM-ADP-161 for scheduled and trial-start workflow contents: write requirements.

## 5. 为什么改变及证据等级

- 原因：Added machine-checked GitHub Actions contents: write permission requirements to the trial-start and scheduled production workflows so controlled Release evidence can be created after explicit enablement while uploads remain disabled by default.
- 证据等级：`EXTRACTED`
- 证据引用：governance/run_manifests/ADP-PHASE11-RELEASE-PERMISSIONS-20260622.json, arxiv-daily-push/docs/phase_records/PHASE_11_RELEASE_PERMISSIONS.md, .github/workflows/arxiv-daily-push-trial-start.yml, .github/workflows/arxiv-daily-push-scheduled.yml, arxiv-daily-push/docs/runbooks/PRODUCTION_TRIAL_RUNBOOK.md

## 6. 对输出、风险和业务决策的影响

No new runtime model; MOD-ADP-018 and MOD-ADP-028 now include Release write permission parameters.

## 7. 当前置信度和证据新鲜度

- 置信度：`Medium`
- 证据新鲜度：`47 unbound event(s)`
- 语义覆盖：`machine_verified`
- 语义覆盖任务：`GOV-SEMANTIC-ADP-001`
- UNKNOWN/HUMAN_REVIEW_REQUIRED 数量：`0`
- 未绑定事件数量：`47`

## 8. 需要项目所有者决定的事项

Provision durable production refs and run the default-branch trial start workflow before 30-day acceptance evidence can begin.

## 9. 当前前三风险

1. Blocker: Semantic coverage is machine_verified with 160 machine-checked active parameters and all 32 active formulas; no active semantic registry rows remain HUMAN_REVIEW_REQUIRED under `GOV-SEMANTIC-ADP-001`. Trial-start and scheduled production workflows now declare machine-checked `contents: write` permission for controlled draft Release evidence, while Release upload remains disabled by default. Production launch remains blocked by missing owner-provisioned durable readiness refs for `runner_ref`, `smtp_secret_ref`, `release_target_ref`, and `workflow_vars_ref`, missing explicit launch confirmation, and missing default-branch trial-start run evidence. Production acceptance still requires a passing default-branch trial start workflow run, live source ingest pass on the runner, real SMTP and Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries.
2. Unbound or stale evidence events: 47
3. No additional machine risk recorded.

## 10. 下一项可执行任务及 Acceptance

- 下一任务：`ADP-PHASE11-PRODUCTION-TRIAL-START-022`
- 状态：`blocked`
- Acceptance：ADP-ACC-PHASE11-PRODUCTION-TRIAL-START
- 选择理由：status=blocked; phase=E; current_phase=E; unmet_dependencies=none; score=127

## 11. 阻塞负责人和解除条件

- 负责人：Project owner
- 解除条件：Meet acceptance ADP-ACC-PHASE11-PRODUCTION-TRIAL-START

## 12. UNKNOWN 与过期证据数量

- UNKNOWN/HUMAN_REVIEW_REQUIRED：`0`
- 过期或未绑定证据：`47`

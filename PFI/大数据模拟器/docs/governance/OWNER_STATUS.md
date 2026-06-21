# OWNER_STATUS

生成方式：由 `scripts/generate_governance_dashboard.py` 从机器事实源生成；不要手工编辑。

## 1. 当前结论

PFI_BIG_DATA_SIMULATOR 当前处于 A 阶段 / GOV-P13-required-passed gate；CI 模式为 required，机器事实源显示模型 15 个、公式 15 个、参数 213 个。

## 2. 更新时间与 Commit

- 生成标记：`DETERMINISTIC_GENERATION`
- 仓库提交：`CURRENT_CHECKOUT`
- 最近事件时间：`2026-06-20T00:00:00+10:00`
- 最近事件提交证据：`PENDING`

## 3. 本轮最重要变化

Validate PFI/大数据模拟器 governance baseline and promote PFI_BIG_DATA_SIMULATOR from advisory to required without runtime logic changes.

## 4. 模型、公式、参数旧值到新值

- 版本变化：current_gate: GOV-P13-required-passed; current_iteration: ITER-20260620-PFI-002; current_phase: A; product_version: 0.1.0
- 模型/公式变化：UNKNOWN
- 参数变化：UNKNOWN

## 5. 为什么改变及证据等级

- 原因：Validate PFI/大数据模拟器 governance baseline and promote PFI_BIG_DATA_SIMULATOR from advisory to required without runtime logic changes.
- 证据等级：`EXTRACTED`
- 证据引用：PFI/大数据模拟器/docs/governance/delivery_tasks.yaml, PFI/大数据模拟器/docs/governance/DEVELOPMENT_LEDGER.md, governance/projects.yaml

## 6. 对输出、风险和业务决策的影响

No runtime model delta recorded.

## 7. 当前置信度和证据新鲜度

- 置信度：`Medium`
- 证据新鲜度：`2 unbound event(s)`
- 语义覆盖：`planned`
- 语义覆盖任务：`GOV-SEMANTIC-PFI-001`
- UNKNOWN/HUMAN_REVIEW_REQUIRED 数量：`215`
- 未绑定事件数量：`2`

## 8. 需要项目所有者决定的事项

Resolve calibration evidence for strategy catalog rule constants and indicator thresholds.

## 9. 当前前三风险

1. Semantic extractor coverage is planned; rollout task GOV-SEMANTIC-PFI-001 remains open.
2. Blocker: calibration/source rationale gaps tracked by `TASK-PFI-B-001` through `TASK-PFI-B-010`
3. UNKNOWN/HUMAN_REVIEW_REQUIRED facts: 215

## 10. 下一项可执行任务及 Acceptance

- 下一任务：`TASK-PFI-B-001`
- 状态：`blocked`
- Acceptance：ACC-PFI-B-001
- 选择理由：status=blocked; phase=B; current_phase=A; unmet_dependencies=none; score=138

## 11. 阻塞负责人和解除条件

- 负责人：Project owner
- 解除条件：Meet acceptance ACC-PFI-B-001

## 12. UNKNOWN 与过期证据数量

- UNKNOWN/HUMAN_REVIEW_REQUIRED：`215`
- 过期或未绑定证据：`2`

# OWNER_STATUS

生成方式：由 `scripts/generate_governance_dashboard.py` 从机器事实源生成；不要手工编辑。

## 1. 当前结论

EEI 当前处于 C 阶段 / TASK-T1307-A209-4H-OPERATOR-SOAK-PARTIAL gate；CI 模式为 required，机器事实源显示模型 12 个、公式 12 个、参数 61 个。

## 2. 更新时间与 Commit

- 生成标记：`DETERMINISTIC_GENERATION`
- 仓库提交：`CURRENT_CHECKOUT`
- 最近事件时间：`2026-06-21T22:35:00+10:00`
- 最近事件提交证据：`PENDING`

## 3. 本轮最重要变化

Generated local 4h operator soak evidence for T1307/A209 with 48/48 PASS windows and PARTIAL_OPERATOR_EVIDENCE status because 24h is missing.

## 4. 模型、公式、参数旧值到新值

- 版本变化：current_gate: TASK-T1307-A209-4H-OPERATOR-SOAK-PARTIAL; current_iteration: ITER-20260621-017; current_phase: C; product_version: 0.1.0
- 模型/公式变化：No scoring formula change.
- 参数变化：No canonical parameter value change; 4h run used PLAYWRIGHT_BROWSERS_PATH=/private/tmp/eei-ms-playwright.

## 5. 为什么改变及证据等级

- 原因：Generated local 4h operator soak evidence for T1307/A209 with 48/48 PASS windows and PARTIAL_OPERATOR_EVIDENCE status because 24h is missing.
- 证据等级：`EXTRACTED`
- 证据引用：EEI/artifacts/tests/a209/t1307_operator_soak_4h.json, EEI/artifacts/tests/a209/t1307_operator_soak_4h.checkpoints.jsonl, EEI/artifacts/tests/a209/t1307_operator_soak_evidence_validation.json, EEI/docs/phase/MVP_DEVELOPMENT_RECORD.md, EEI/docs/governance/VERSION_MATRIX.yaml, EEI/docs/governance/delivery_tasks.yaml, +2 more

## 6. 对输出、风险和业务决策的影响

No scoring formula change.

## 7. 当前置信度和证据新鲜度

- 置信度：`Medium`
- 证据新鲜度：`16 unbound event(s)`
- 语义覆盖：`in_progress`
- 语义覆盖任务：`GOV-SEMANTIC-EEI-001`
- UNKNOWN/HUMAN_REVIEW_REQUIRED 数量：`153`
- 未绑定事件数量：`16`

## 8. 需要项目所有者决定的事项

Implement real data ingestion, entity resolution and evidence chain for the Golden Vertical

## 9. 当前前三风险

1. Semantic extractor coverage is in_progress; rollout task GOV-SEMANTIC-EEI-001 remains open.
2. Blocker: A209/A206 remain open until 24h operator soak evidence is produced and CI-validated; 7 active motion parameters still have UNKNOWN runtime activation evidence, and FORM-012 remains HUMAN_REVIEW_REQUIRED.
3. UNKNOWN/HUMAN_REVIEW_REQUIRED facts: 153

## 10. 下一项可执行任务及 Acceptance

- 下一任务：`TASK-T1301`
- 状态：`in_progress`
- Acceptance：ACC-A202
- 选择理由：status=in_progress; phase=C; current_phase=C; unmet_dependencies=none; score=122

## 11. 阻塞负责人和解除条件

- 负责人：Codex/governance runner
- 解除条件：Meet acceptance ACC-A202

## 12. UNKNOWN 与过期证据数量

- UNKNOWN/HUMAN_REVIEW_REQUIRED：`153`
- 过期或未绑定证据：`16`

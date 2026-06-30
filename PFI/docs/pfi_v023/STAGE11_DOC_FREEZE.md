# PFI v0.2.3 Stage 11 Phase 11.2 Doc Freeze

## Scope

本文件只覆盖 Stage 11 Phase 11.2 文档冻结，不执行 Phase 11.3，不执行 Stage 11 whole-stage review，不上传 GitHub main，不声明用户已验收。

## Candidate Status

- 当前状态：Stage 11 Phase 11.2 candidate pass。
- user_acceptance_claimed=false。
- Phase 11.1 回归测试已完成本地候选提交。
- Phase 11.2 只冻结 README、未来开发约束、历史废弃政策和剩余风险。
- Phase 11.3 最终候选交付未执行。

## Future Development Constraints

后续 PFI v0.2.3 开发必须遵守以下合同：

- 固定 10 个一级入口：首页总览、账户与资产、账本流水、投资管理、消费管理、数据源与上传、建议与复盘、报告与洞察、市场与研究、设置。
- 市场与研究 是正式一级入口。
- 历史 9 入口约束作废。
- 禁止虚构财务数据；真实数据不足时只能显示中文真实状态、阻断原因和下一步。
- 每次 run work 最多只解决一个 phase；整个 Stage 完成后才能做 whole-stage review。
- 用户明确验收前只能写候选通过。
- 不得以 README 或 docs 声明替代真实验证。
- 不得用字符串标记替代真实浏览器证据、JSON evidence、测试输出或 app/localhost 健康检查。
- 中间 phase 不上传 GitHub main；只有 whole-stage review 修复通过后才上传。

## Frozen History Policy

历史资料只能作为参考，不能覆盖 v0.2.3 当前合同。冻结后不得恢复以下约束：

- 一级入口 9 个。
- 市场与研究 不能作为一级入口。
- 旧 UI shell 继续补丁式堆叠。
- README/docs 写完成即可 closeout。
- 演示型财务数据可进入验收。

如未来文档、代码或 evidence 与本文件冲突，以本文件、`HISTORY_DEPRECATION_POLICY.md`、`DATA_TRUST_RULES.md` 和真实验证结果为准。

## Residual Risks

- 用户手动验收未完成。
- Stage 11 Phase 11.3 最终候选交付未执行。
- Stage 11 whole-stage review 未执行。
- Stage 11 GitHub main upload 未执行。
- Phase 11.2 只冻结文档和约束，不重新生成最终截图索引。
- Phase 11.2 不改变 app bundle、localhost 运行入口、read model 或报告生成逻辑。
- 阻塞项数量：0。

## Evidence

- Phase 11.1 回归测试：`PFI/reports/pfi_v023/stage_11/phase_11_1/evidence.json`
- Phase 11.2 文档冻结证据：`PFI/reports/pfi_v023/stage_11/phase_11_2/evidence.json`
- 文档冻结测试：`PFI/tests/test_v023_regression.py`

## Scope Guard

本轮没有写最终完成声明。本轮没有声明用户已验收。本轮没有进入 Phase 11.3。

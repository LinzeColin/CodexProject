# PFI v0.2.5 Stage 5 Phase 5.3 模型验证实施记录

## Run Contract

- Iteration：`ITER-20260715-PFI-V025-S5-P53`
- Contract：`PFI-V025-STAGE5-PHASE53-MODEL-VALIDATION`
- Acceptance：`ACC-PFI-V025-S5-P53-MODEL-VALIDATION`（项目治理分配；来源 Roadmap 未提供 Phase ACC-*）
- Task：`S5-P3-T1..T4`
- Route：`T3_FINANCIAL_MODEL_VALIDATION_PRIVACY`
- 基线 commit：`61a14d9366c68a8c849c0c056a107116d5b377d1`

## 目标与最小范围

1. 从 immutable Git object 重放 Stage 3 已接受的真实交易快照，全程只读且不使用 fixture fallback。
2. 将发布的 CNY ledger events 映射到 Phase 5.2 financial-event contract，验证双口径精确守恒、去重和四项 metamorphic properties。
3. 在真实快照上运行 7/21/30/60/90/180/360 窗口敏感性和空窗口 false-zero 边界。
4. 生成 model validation card；缺少余额、负债、持仓、价格、成本、费用、税、FX、完整 XIRR chain 或 ground truth 时保持 blocked。
5. 验证 homepage/consumption/report consumer payload 同 hash，同时如实记录实际 Web/report renderer 尚未绑定四组件。

## 非范围

- 不写真实数据或数据库，不补造余额、持仓、价格、FX、分类 labels 或 XIRR cashflow chain。
- 不修改 Web/report renderer 源；本 Phase 只验证 Stage 5 Allowed Files 内的 consumer contract。
- 不执行 Stage 5 whole-stage review、Stage 6、production/final acceptance、network、push 或 App install。

## 验收与停止条件

- 真实 source identity 读取前后完全一致，8,815 条输入完整分区为 6,879 published + 1,936 review + 0 silent drop。
- 双口径 difference 精确为 0，permutation/duplicate/positive-scaling/date-translation metamorphic tests 通过。
- 七窗口 record count 随窗口非递减；无事件边界必须为 `filtered_empty/null`，不能发布假零。
- 公开证据不含财务金额、逐行标识、描述或绝对私有路径。
- 任一 source mutation、双计、不变量失败、私有值泄漏、参数冲突或把缺失覆盖写成 pass，立即停止。

## 回滚

只回滚 Phase 5.3 本地原子提交；immutable source、数据库、历史公式版本和 Phase 5.1/5.2 evidence 均不改写。

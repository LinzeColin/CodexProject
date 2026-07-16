# Phase 5.3 风险与回滚

- 真实数据风险：只通过 immutable Git blob 重放；记录 source identity before/after，禁止 DB 和 source write。
- 隐私风险：公开 evidence 只保留 counts、日期范围、状态与不可逆 hash，不输出财务金额、逐行标识、账户或描述。
- 覆盖风险：1,936 条 review rows、投资入金/退款链、余额/负债/持仓/价格/成本/费用/税/FX 均不得被 transaction-only evidence 覆盖。
- 模型风险：FORM-PFI-016..018 和历史/样本外验证保持 blocked；结构约束不冒充分类准确率。
- 敏感性风险：只对真实可计算的七窗口运行；缺 score vector、ground truth 或完整 XIRR chain 时不造结果。
- Consumer 风险：同 payload hash 只证明 contract 一致，不证明实际 Web/report renderer 已绑定；open requirement 必须保留给整阶段审查。
- 回滚：revert 本 Phase 单一 local commit；不改 immutable source、DB、历史公式或 Phase 5.1/5.2 evidence。

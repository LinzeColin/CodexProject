# Stage 3 Phase 3.1 风险与回滚

## 当前风险

- 当前角色注册表只定义可发布 vocabulary；任何未注册角色必须人工复核，不能自动映射。
- `account_ref` 与 `source_id` 仍是上游提供的 opaque reference；本 Phase 不证明真实账户映射正确。
- parser provenance 证明 parser/version/hash 绑定合同，不证明 parser 已正确标准化真实交易；该验证属于 Phase 3.2/3.3。
- review queue 当前是纯合同路由结果，未实现持久化、owner UI、重试或发布工作流。
- Stage 2 已知的 production FX、余额、负债、持仓和价格缺口没有被本 Phase 消除。

## 回滚

只 revert `PFI-V025-STAGE3-PHASE31-SOURCE-ACCOUNT` 对应本地提交，并把 Stage 3 恢复为 `not_started`。不得修改 Stage 2 不可变证据，不得触碰真实数据、数据库、App bundle 或 remote refs。

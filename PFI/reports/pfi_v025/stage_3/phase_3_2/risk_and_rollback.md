# Phase 3.2 Risk and Rollback

## 风险

1. 显式 link reference 本身错误时会形成错误组；本 Phase 不把金额/时间相似作为补救猜测，Phase 3.3 必须用真实只读副本对账并把差异送入 review queue。
2. Event type 由上游显式提供；未注册类型 fail-closed，但 event type 的真实映射准确性尚未由真实数据证明。
3. `activity_outflow_included` 是用户定义活动口径，不等于净资产损失；Phase 5 公式与报告必须保持该语义。
4. 多币种事件只保留逐笔 posting，不聚合金额；缺少有效 FX snapshot 时不得生成统一金额。
5. idempotency key 已证明内容与顺序稳定，但尚未执行真实重复导入、持久化 unique constraint 或并发发布测试。
6. 本 Phase 不持久化 unknown-event review item；真实 review queue 生命周期留待 Phase 3.3/Stage 7。

## 回滚

- 只 revert Phase 3.2 本地提交及其 schemas、policy、domain/application、tests、Evidence 与治理记录。
- 不回滚或修改 Stage 2/Phase 3.1 不可变证据。
- 本 Phase 无数据库 migration、真实数据、App bundle、remote ref 或外部系统副作用。

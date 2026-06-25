# 实施方案与质量保护

## M1-S 目标实现

只在既有 `scripts/lean_governance.py` 内逐步增加：

1. `check plan`：说明 changed paths 触发哪些检查及为什么升级。
2. `pre/post zero-write`：检测验证器新增写入，而不是要求本地调用前绝对干净；CI 可保留严格 clean-start。
3. `compact stdout`：不超过 2 KB 的人类摘要。
4. `full JSON evidence`：写 runner temp 或 `.git/codex-review`，不写 tracked 文件。
5. `stage timing telemetry`：记录各阶段耗时、selected-project count、render count、stdout bytes。
6. `candidate shadow`：候选只报告，不改变 legacy pass/fail。

## 不允许的“提速”

- 删除 semantic、sync、render、Acceptance 或 Evidence 检查；
- 依赖用户/Prompt 自报风险等级；
- 错误 base/diff 时当作无变化；
- 使用未按内容 hash 和工具版本键控的持久缓存；
- 让 CI 写 tracked 文件；
- 改 Required Check 名称；
- 全仓重构 `lean_governance.py`；
- 修改任何项目产品 Roadmap 或业务代码。

## 影子分类原则

候选分类只能由实际 Git diff 和仓库契约决定：

- 根 contract/schema/validator/workflow：完整 root changed-scope；
- 模型、公式、参数、schema、安全、发布、隐私、资金：T2/T3 全检查；
- canonical facts 或三个中文文件：sync + render + semantic；
- 低风险 T0 文案/格式：可候选精简，但 legacy 仍权威直至 parity；
- 未知路径、Git 错误或分类冲突：升级完整检查。

## 合并策略

- PR 1：测试 + shadow instrumentation；不改 required 行为。
- PR 2：parity/stress evidence；通常无产品行为改变。
- PR 3：有限激活（仅 S4 Gate 通过时）；保留一键 legacy rollback。

每个 PR 独立回滚，禁止把三步压成一个不可审查大提交。

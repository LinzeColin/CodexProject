# PFI v0.2.4 Stage 8 Phase 8.3 Defects

Status: 待用户人工验收

本文件只记录 Phase 8.3 人工验收前已知的开放项和用户验收后暴露的问题。当前没有经过用户确认，因此只可写为“未确认产品缺陷”，不能写成最终通过结论。

## Open Items

| ID | Type | Status | Description | Next handling |
| --- | --- | --- | --- | --- |
| D8.3-PENDING-001 | acceptance | open | 未确认产品缺陷；完整人工验收仍待用户人工验收。 | 用户按 `manual_acceptance.md` 检查后，如发现产品问题，追加具体复现步骤、截图和期望。 |
| D8.3-ENV-001 | environment | open | `/Applications/PFI.app` 当前缺失；Phase 8.2 证明 `~/Downloads/PFI.app` 存在并指向当前 checkout。 | 不在本 phase 重装；如用户要求，可在后续独立 app 入口修复或整阶段复审修复轮处理。 |

## Boundary

- 本 phase 不重装 app bundle。
- 本 phase 不清理或删除用户数据。
- 本 phase 不补造 mock/sample/synthetic/fixture/demo/fake 财务数据。
- 本 phase 不自动进入 Stage 8 whole-stage review、Stage 9 或 GitHub main upload。

# PFI v0.2.5 Stage 6 Phase 6.2 独立二级页面合同实施记录

## Run Contract

- 唯一任务：`S6-P2-T1..T4`
- 唯一验收：`ACC-PFI-V025-S6-P62-PAGE-CONTRACTS`
- 模式：`IMPLEMENT / CONTROLLED_RUN`
- 范围：45 个二级页面的 job-to-be-done、canonical URL、独有数据/主动作/状态、结构签名、breadcrumb/title/focus/scroll 与 no-JS fallback
- 非范围：Phase 6.3 完整 History API/back/forward/reload/invalid-route/a11y acceptance、Stage 6 whole-stage review、真实财务数据、数据库、push、App install
- 回滚：只 revert 本 Phase 本地提交；保留旧 query routes 作为兼容 redirect，不恢复旧 16 个一级入口
- 停止条件：Phase 6.2 candidate evidence 与治理闭合后立即停止，不进入 `S6-P3-*`

## 来源锁定

- Roadmap SHA-256：`fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b`
- Task Pack ZIP SHA-256：`591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2`
- `docs/PRODUCT_UX_ARCHITECTURE.md` 提供各工作区页面原型、独立页面语义、状态与路由规则。
- Phase acceptance ID 由项目治理分配；来源 Roadmap/Task Pack 未提供 Phase 级 `ACC-*`。

## 实施结果

| Task | 结果 | 主要证据 |
|---|---|---|
| `S6-P2-T1` | 10 个一级工作区下共 45 个二级页面均定义独立 job-to-be-done 与 canonical path | `page_contracts.json` |
| `S6-P2-T2` | 每页具有唯一 data object、primary action、layout/signature 与 loading/empty/error 状态 | `page_data_actions.json` |
| `S6-P2-T3` | Shell 同步 page title、breadcrumb、heading focus 与按 canonical route 的 scroll position | `navigation_behavior.json`, browser validation |
| `S6-P2-T4` | 45 个 path route 支持深链；45 个历史 query route 只做 redirect；no-JS 目录保留 10 个一级和 45 个非空页面 | `deep_link_fallback.json`, `nojs_navigation.png` |

## 关键决策

- `navigation.js` 是 v0.2.5 页面合同事实源；旧 Stage 4/5 页面数据仅提供既有内容区块，Shell 以 canonical contract 覆盖 route、title、state 与 layout identity。
- 所有当前二级 URL 使用 path route；旧 `/home?tab=*`、`/sources-upload?tab=*` 与其他 `?tab=` 路由仅在 registry 中归一，不成为当前页面标识。
- 页面复用 Shell 和组件，但以 45 个唯一结构签名、数据对象与主动作防止“同一卡片模板只换标题”。
- 关闭 JavaScript 时，正式 App shell 与未完成的 release gate 隐藏，直接展示可读页面目录；动态数据与 history 明确要求启用 JavaScript。
- release manifest 只重绑实际 frontend source hash；version、build id、backend hash 与 Stage 1 git-commit binding 语义不变。

## 验收与残余

- focused contract `4 passed`；Stage 5 页面差异化/状态与 Stage 6 导航回归通过。
- formal-shell desktop/mobile 分别从 `/accounts/reconcile`、`/market-research/strategy-lab` 深链进入，并逐一验证 10 个工作区代表页面；URL/route、title、breadcrumb、focus、scroll、状态和结构差异均通过。
- no-JS 隔离 Chrome 显示 10 个一级入口和 45 个非空二级页面；截图已人工复核。
- 完整 back/forward/reload/repeated-click/invalid-route、键盘矩阵和 a11y tree 仍是 Phase 6.3，不能由本 Phase 推断完成。

## 当前结论

`ACC-PFI-V025-S6-P62-PAGE-CONTRACTS = candidate_pass`。Stage 6 为 `8/12 in_progress`；下一唯一工作单元为 `S6-P3-T1..T4`，本轮停止。

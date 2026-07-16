# PFI v0.2.5 Stage 6 Phase 6.3 浏览器历史与验收实施记录

## Run Contract

- 唯一任务：`S6-P3-T1..T4`
- 唯一验收：`ACC-PFI-V025-S6-P63-HISTORY-ACCEPTANCE`
- 模式：`IMPLEMENT / T2 / CONTROLLED_RUN`
- 范围：canonical path History API、back/forward、刷新/深链、重复点击、无效 route 恢复、键盘焦点、accessibility tree 和候选 Evidence
- 非范围：Stage 6 whole-stage review、Stage 7、真实财务数据、数据库、Finder、外部网络、GitHub push、App install
- 回滚：仅 revert 本 Phase 单一提交；保留 Phase 6.1/6.2 的 10 入口与 45 页面合同
- 停止条件：Phase 6.3 candidate evidence 完整后立即停止；Stage 6 不得在未独立整阶段审查时标记通过

## 来源锁定

- Roadmap SHA-256：`fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b`
- Task Pack ZIP SHA-256：`591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2`
- Roadmap Phase 6.3 要求 `pushState/replaceState/popstate`、刷新/深链/重复点击/无效 route、AX tree 10 入口与候选 Evidence。
- `PRODUCT_UX_ARCHITECTURE.md` 要求 History API 管理 URL/state/back/forward，深链刷新恢复页面，404 有独立可行动状态，WCAG 2.2 AA 为无障碍 Gate。

## 实施结果

| Task | 结果 | 主要证据 |
|---|---|---|
| `S6-P3-T1` | 正式 HTTP Shell 使用 canonical pathname；hash 仅作兼容输入；history state 保存 route/workspace/scroll/source | `route_runtime.json` |
| `S6-P3-T2` | actual back/forward、scroll、直接深链、CDP reload、重复点击 history delta=0、无效 route 与恢复全部通过 | `playwright_result.json`, `browser_history_validation.json` |
| `S6-P3-T3` | `Accessibility.getFullAXTree` 的“一级工作区”子树恰好 10 个命名、可聚焦入口；键盘 Enter 后页面 heading 获得焦点 | `a11y_tree.json` |
| `S6-P3-T4` | Phase 候选 Evidence 完整，明确等待 Stage 6 独立整阶段审查和用户验收 | `stage_6_evidence.json`, `evidence.json` |

## 关键决策

- 对 HTTP/HTTPS 正式 Shell 使用实际 pathname；`file:`、`about:srcdoc` 等静态/组件环境保留 hash compatibility fallback，不把 hash 当 canonical URL。
- URL 是 history traversal 的页面事实源；每个 entry 同步 `routeAlias/workspace/scrollY`，浏览器 back/forward 后重挂页面并恢复 heading focus 与 scroll。
- 重复点击当前 route 使用 `replaceState`，不得制造重复 history entry。
- 无效 route 保留原 URL，显示独立 `role=alert` 页面、请求地址和“返回首页总览”动作；不静默伪装成首页。
- 使用已缓存 Playwright、本机 Google Chrome 与 CDP AX API；未安装依赖，所有网络仅为临时 `127.0.0.1`，其他请求由浏览器 route gate 拦截。

## 验收与残余

- focused Stage 6 contract：`23 passed`。
- cached Playwright actual formal shell：13 项 history/route/keyboard/a11y/network/error checks 全部 pass；console/page/http errors 均为 0。
- AX primary navigation count/unique count=`10/10`；DOM primary count=`10`；无重复隐藏一级树。
- 旧 v0.2.4/v0.2.1 route 文本测试仍有 4 条 superseded expectations，要求 `/home`、旧 query route 与旧 target label；这些在 Phase 6.1 已被 v0.2.5 canonical contract 明确替代，不作为本 Gate。
- Stage 6 whole-stage review、整改、复审与用户验收尚未开始；不能由 Phase 6.3 的绿色结果推断 Stage 6 已通过。

## 当前结论

`ACC-PFI-V025-S6-P63-HISTORY-ACCEPTANCE = candidate_pass`。Stage 6 phase tasks=`12/12 candidate_complete`，但 Stage 6 仍为 `in_progress`；下一唯一工作单元是 `S6-WHOLE-REVIEW`，本轮停止。

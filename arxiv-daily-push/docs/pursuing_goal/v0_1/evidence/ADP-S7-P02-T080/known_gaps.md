# Known gaps · ADP-S7-P02-T080｜补齐组件状态、Undo 与跨主题状态保持

诚实披露**范围**、**验证形式**、**权衡**与 NOT_DEPLOYED 语义。

## 实现与不破坏承诺
- **base CSS 组件状态矩阵**（唯一改动的合同哈希 `base_css`，approved-change 走 T078 门）：`button:active`（按下）、`button:disabled`+`button[aria-disabled]`（禁用）、`button[aria-busy]`（加载）、`:focus-visible`（键盘聚焦）、`[data-state=ok|err]`（成功/错误）、`button.undo`（撤销）、`button{transition:transform .08s …}`。**不新增 @keyframes**（keyframes 等 11 个动效哈希字节不变）。
- **grade/run 客户端 JS**（页面体，**非任何合同哈希**）：两处 grade() 重写为乐观 Undo 窗 + 加载/错误态；run() 加 try/catch + aria-busy + 错误态。经 T077/T078 合同验证 specific 变化**只有 base_css**，6 主题 per-theme + 11 动效元素**全部 byte-identical**。

## 关键权衡（延迟写，必读）
- **Undo 窗把 grade 的 D1 写入延迟 4 秒**（Gmail 式撤销）。好处：撤销**零写入**（满足 rollback「不得改写既有生产数据」——旧设计立即写，撤销需服务端反转 + 触碰数据；新设计根本不写，更干净）。**代价**：若用户在 4s 窗口内**关闭标签/导航离开**，该次评分**不被记录**。判断：学习类应用里评分可下次复习再评（`duplicate` 门本就允许当天重评），丢失一次快速评分的代价 < 误点无法撤销的代价；且 `_grading` 锁防重复、窗口结束才写、错误重试。**此权衡在此明确披露**；若 Owner 更看重「绝不丢评分」，可改为「立即写 + 服务端反转端点」（更大改动，另起任务）。
- **并发/竞态**：`_grading` 锁使窗口期间二次点击无效；`gradeUndo` 只在 `_pend` 存在时清计时器（commit 已发后撤销无害——commit 清了 `_pend`）；commit 出错重置 `_grading` 并重启用按钮。Node 行为测试覆盖 点击→撤销→再点击→窗口结束 序列。

## 验证形式（如实，含真实运行）
- **确定性审计**（component_state_audit）：状态矩阵存在性 + 判别性（pre-fix 负控制 0/7）+ undo 结构（延迟写/撤销不 fetch）+ applyTheme 无 reload/navigate/innerHTML（负控制：注入 reload 被检出）+ 只 base_css 变。
- **Node 行为测试**（真实抽取的 grade 客户端码，非重实现）：点击 0 写、撤销 0 写、窗口结束恰 1 写、写目标正确。11/11 PASS。
- **内置浏览器**（真实 CSS）：6 主题切换全保 scroll/reveal/filter/details；状态 CSS 全计算。
- **100ms 反馈的形式**：`:active` 是**浏览器原生**按下态（pointerdown 即生效，<16ms），+ 80ms transform 过渡（<100ms）；未做逐控件的高精度计时器测量（`:active` 原生性质使其无需——它不经 JS/网络）。同步反馈（picked+撤销）由 Node 测试证同步。

## 边界 / 未做
- **持久化的浏览器测试用 `setAttribute('data-theme',…)`**（applyTheme 的持久化相关行为）——审计已证真实 applyTheme 只做 setAttribute + 同步 hero/gauge，无 reload/navigate/innerHTML；hero/gauge 同步不触碰内容 DOM/滚动/输入，故不丢状态。未把整套真实主题引擎（依赖 THEMES/HEROVIDEO 等全局）搬进 harness。
- **`:active` 仅覆盖 `<button>`**（含所有按钮：grade/undo/reveal/study/run/nav）；链接 `<a>` 与 `select` 得 `:focus-visible` 聚焦态，`<a>` 的按下反馈依赖浏览器默认（导航类元素）。
- **未部署逐页真机回归**：状态/持久化在 harness + Node 证，非线上逐页。真机像素/交互留待部署后（S7 视觉 Owner 确认）。
- **性能未改**：本任务治状态与持久化，不动六主题/hero/氛围动效（S7-P03 才是性能打磨）。

## NOT_DEPLOYED 语义
改 `deploy/cloudflare/worker_cloud.js` 源 + 重算 BUILD 自哈希（`9690390a9fc8`→`40a46aa2baee`），但**不部署**。**live 仍 b189d3cc0703**（六主题+动效不变）。部署是单独 gated 步骤。T077 基线不重冻（同 T079：T078 把基线 rebase 流程留待 CI 接线时定）。

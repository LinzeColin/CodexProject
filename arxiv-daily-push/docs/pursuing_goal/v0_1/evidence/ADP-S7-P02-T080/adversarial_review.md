# 独立对抗复核 · ADP-S7-P02-T080｜补齐组件状态、Undo 与跨主题状态保持

实现者**不自签 PASS**。由独立 skeptic Agent（`general-purpose`，不共享推理）对抗复核，目标**证伪**验收。

## 结论：CONFIRMED_SOUND

复核 Agent 独立重算每条主张，无法证伪验收。逐向量：

- **(a) 点击 100ms 内反馈 — SOUND**。`button:active{transform:translateY(1px)}`（worker line 643，pointerdown 原生 <16ms）+ `button{transition:transform .08s…}`（80ms ≤ 100ms）；未被 `.picked{}`（无 transform、低优先级）遮蔽。每个动作控件（grade/undo/reveal/study/run/nav）都是 `<button>`；grade 处理器还同步渲染 picked+撤销。链接/`<select>` 得 `:focus-visible`+原生反馈——此覆盖边界在 known_gaps 明确披露，未过度声明。
- **(b) Undo 写入完整性 — SOUND 且已披露**。`gradeUndo()` 无 fetch（brace-matched 审计 + Node 测试）；单线程 `_grading` 锁 + 禁用按钮 + commit 前清 `_pend` 使重复写与撤销写不可达；**post-commit 撤销不可达**（比原 claim 更强——不只是无害）：计时器回调 `clearInterval;_pend=null;gradeCommit()` 同一同步 tick 执行，`gradeCommit` 首句 `r.textContent='记录中…'` 在 `await fetch` **之前**销毁撤销按钮，无事件循环让步点可让用户点到撤销。**真实权衡**（延迟写 4s → 中途关标签丢一次评分 + /review 每卡约 4s 税）是相对旧「立即写」的真实行为回归，但**明确准确披露**（known_gaps:10、cost_value:24）含理由（`duplicate` 门允许当天重评）与替代方案（立即写+服务端反转端点，另起任务）。**披露的权衡，非隐藏 hole**。
- **(c) 持久化保真 — SOUND**。真实 `applyTheme`（759-762）做的比 setAttribute 多（syncHeroVideo/blurTextIn/animateGauge/lsSet/meta），但每个副作用都局限于 hero 元素（#heroVideo/.hero .display .bw/#gaugeNum/#gaugeArc）、localStorage、theme-color meta——**均不重建内容 DOM、不导航、不 reload、不滚动**，且非首页早返回；`applyTheme` 本任务未改；无页面把主题切换绑到 reload/navigate（grep 干净）。**澄清**：本应用**无 `<details>`**，真实「展开」是 reveal box（`hidden` 切换，line 1016）——浏览器测试已覆盖真实机制（`revealShown:true`）；harness 里的合成 `<details>` 只是额外代理，不构成误导。
- **(d) 视觉合同 — SOUND**。经 visual_baseline 独立重算：只 `base_css`+`master_visual` 变；6 主题 per-theme + 11 动效元素**字节相同**。grade()/run() 编辑在 todayPage/systemPage/graderHTML 页面函数里，在冻结视觉表面之外，未动任何 motion 哈希；`theme_js` 不变。
- **(e) BUILD 自哈希 — SOUND**。从零重算（清 12+64 占位、sha256）→ `40a46aa2baee`，与声明一致。live 服务 `b189d3cc0703`（比 origin/main 的 9690390a9fc8 与 T080 源都旧），确证 NOT_DEPLOYED。
- **(f) 空洞性 — SOUND**。`pre_fix_worker.js` 与 origin/main 字节相同；`pre_fix_baseline.json` 与其重算哈希精确匹配；负控制独立复现（pre-fix 0/7 state_matrix、0/5 undo_defers_write；注入 location.reload 被检出；T078 门无 approval→BLOCK、带→PASS_APPROVED）；Node 测试嵌**真实逐字抽取**的 grade 码。

## 复核指出的次要点（已处置）
- **state_matrix 是子串存在性检查**（空规则体理论上会通过）——复核判定「本身非载重，但非误通过」：规则实带真实声明，且 `browser_measurements.json` 证 CSSOM **实际计算**了这些状态（success 上色/loading 变暗+拦截/disabled 变暗/:active+transition 在 CSSOM）。**载重确认来自浏览器 CSSOM 计算**（验证器已断言 `state_css_computed` 全 True），故子串检查 + 浏览器计算组合充分，无需额外加固。

## 底线
验收（1）点击 100ms 内反馈（2）切主题不丢阅读位置/答案/筛选/展开，两条均由**判别性审计 + 真实抽取码 Node 行为测试 + 内置浏览器持久化/CSSOM 证明 + 独立哈希重算**证明；build 自哈希与 NOT_DEPLOYED 诚实；延迟写权衡准确披露。

**VERDICT: CONFIRMED_SOUND**（复核原文），实现者据此提交。

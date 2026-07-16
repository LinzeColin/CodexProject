# Known gaps · ADP-S7-P03-T082｜优化环境动效而不改变视觉语义

诚实披露**范围**、**验证形式**、**FPS 测量**与 NOT_DEPLOYED 语义。

## 实现与不破坏承诺
- **唯一改的合同元素是 `keyframes`**（meteor left/top→transform）。经 T077/T078 验证 `detect_regression` specific 变化只有 `keyframes`；per_theme(6主题含 cosmos)/base_css/theme_js/fx_css/reduced_motion/hero_* **全部 byte-identical**。走 T078 approved-change（无 approval BLOCK，带 keyframes approval PASS_APPROVED）。
- **FX_PERF_JS 在 router 层注入**（htmlResp，和 RUM 并列）——**不碰任何合同哈希**；只碰 `.fx *`(暂停)与 `.meteor/.band/.neb`(低端降级)，**绝不碰前景(按钮/组件状态)选择器**（已审计 foreground_preserved）。
- **踩坑修复**：初版 FX_PERF_JS/注释里含 `.fx-cosmos …` 字面，被合同抽取正则误判为 CSS 规则、污染 fx_css/per_theme:cosmos；已改用叶子选择器(.meteor/.band/.neb)+重写注释消除污染，最终 detect_regression 只剩 keyframes。**教训:worker 里任何新注释/JS 串都不能含 `.fx-<名>`/`[data-theme=…]`/`@keyframes` 字面（会被合同抽取正则吞）**。

## meteor 屏幕路径等价（不改视觉语义的核心）
- `.fx` 是 `position:fixed;inset:0`（viewport-sized），`.meteor{left:-12%;top:8%;transform:rotate(18deg)}` base 不变。
- x：left −12%→100%（Δ=112% 视口宽）== translateX 0→112vw；y：top 8%→64%（Δ=56% 视口高）== translateY 0→56vh。
- 变换顺序 `translate(…) rotate(18deg)`：rotate 内层（保留 18° 条纹旋转），translate 在屏幕空间（同一对角线）。0% 关键帧 transform=translate(0,0)rotate(18deg)==base transform（起始不跳变）。
- **结论**：屏幕路径完全一致，只是动画技术从 layout 改为 compositor。浏览器确认 meteor 位于 base(−12%,8%) 且 transform 动画运行。

## FPS 测量形式（如实）
- **≥55 FPS 的载重证明是确定性的 compositor-only 保证**：所有环境无限循环 keyframe 只动 transform/opacity/filter → 跑在合成器线程、不产生每帧 layout/paint → 不掉主线程帧。
- **未取到可靠的实测 FPS 数值**：内置浏览器 preview 对非前台标签**节流/暂停 requestAnimationFrame**（1s rAF 采样器超时挂起）。**真实中位 FPS 数值须在前台浏览器（部署后或真机）测**。故本任务交付确定性 compositor 保证 + before/after trace + 暂停/降级/前景的行为证明，**不虚报一个 FPS 数字**。
- **filter:blur 备注**：`bwin`(hero 一次性模糊入场)含 filter:blur——但它是 hero 入场非环境无限循环，不在环境 loop 集；环境 loop 的 filter 使用(如星云的静态 blur 不在 keyframe 里动)不产生每帧重算。

## 边界 / 未做
- **无真实录屏**（deliverable「visual recordings」）：preview 节流使录屏 FPS 不可靠；以 before/after trace + 行为证明替代，真实录屏留待部署后前台浏览器。
- **懒加载/合成器提升(will-change)未加**：本任务聚焦「消除唯一 layout 动画 + 暂停 + 低端降级」这三个最高价值项；will-change 会增内存、按需再加。
- **NOT_DEPLOYED**：改源+重算 build_id(8c19387c846b→0cb3acee6bf3)，不部署；live 仍 b189d3cc0703。T077 基线不重冻（同 T079-T081）。

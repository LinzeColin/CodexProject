# TASK_REPORT · ADP-S7-P02-T079｜修复移动端溢出与数据密集布局

- **Iteration**: ITER-20260716-ADP-V01-FINAL-EXECUTION
- **Task**: ADP-S7-P02-T079（Stage S7 UI/UX, Motion & Performance / S7-P02 移动端、组件状态与状态保持，size S）
- **release_mode**: NOT_DEPLOYED（改 worker 源 + 重算 BUILD `b189d3cc0703`→`9690390a9fc8`，但不部署；live 仍 `b189d3cc0703`）
- **Depends**: ADP-S7-P01-T078（Visual/Motion Regression CI 门）

## 6 个前置问题
1. **溢出源有哪些？** — 长 URL/文号/DOI/关系文本、数据密集表格(数据源/运行历史/复习队列/往期)、内容媒体、flex 子不收缩。
2. **怎样「无全页横向滚动」？** — 长文本 `.card` overflow-wrap；表格 display:block+overflow-x:auto(局部横滚)；媒体 max-width:100%；flex 子 min-width:0(.itemrow .body 先例有)；border-box(先例)。
3. **怎样「局部表格横滚受控」？** — `@media(max-width:520px){table{display:block;overflow-x:auto;white-space:nowrap}}`——表格在自己的块内横滚，不推页；**不用 body overflow-hidden band-aid**。
4. **怎样「现有高级视觉保持」？** — 只改 base CSS；经 T077/T078 合同验证 specific 变化只有 base_css，6 主题+所有动效哈希 byte-identical；走 T078 approved-change。
5. **NOT_DEPLOYED 怎么理解？** — 改 worker 源 + 重算 build_id(b189d3cc0703→d62009f8c708) 但不 deploy；live 不变；部署是单独 gated 步骤。
6. **怎么证明不橡皮图章？** — 无 approval 时 T078 门 BLOCK(base_css)；带 base_css approval → PASS_APPROVED。守卫覆盖每个溢出源。

## 交付物
- **响应式修复**（worker_cloud.js base CSS 3 条 + BUILD 自哈希重算；L1 清理移除 `.card` 惰性 `min-width:0`）。
- **工具** `tools/mobile_overflow_audit.py`：audit(3 个 T079 载重守卫，判别性)/structural_guards(pre-exist 依赖，单列)/strip_t079_guards(负控制)/table_scroll_is_local(局部横滚+无 band-aid)/test_matrix(360/390/430×5 元素)/preserves_advanced_visual(只 base_css 变)。
- **真实渲染证明** `render_measurements.json`（内置浏览器 360/390/430 测 scrollWidth + 反事实）+ **render_harness.html**/`build_render_harness.py`（从真实 worker CSS 构造最坏页面）。
- **报告** `mobile_overflow_report.json` + **pre_fix_baseline.json**(T077 修复前冻结基线) + **pre_fix_worker.js**(origin/main worker，供负控制)。
- **test matrix**：360/390/430 × {长URL/文号/表格/关系diff/媒体} = 15。
- **known_gaps.md**：NOT_DEPLOYED 语义、真实渲染证明、L3/L4 边界。
- **独立对抗复核** `adversarial_review.md`（VERDICT: CONFIRMED_SOUND；L1/L2 已修，L5 转正）。

## 验收（PASS，verifier 独立重算）
证据：`test-results/mobile_overflow_tests.txt`（ACCEPTANCE = PASS，exit 0），verifier `t079_verify.py`。

1. **无全页横向滚动** — 3/3 T079 载重守卫存在(长文本/媒体/表格局部横滚)；2/2 pre-exist 结构守卫依赖到位；CSS 括号平衡。**真实渲染**：360/390/430 均 scrollWidth==innerWidth、0 表格外越界、nav 不越界。**判别性负控制**：pre-fix CSS 与剥离后 CSS 审计均 0/3。**反事实**：pre-fix CSS 360px 越界 1210px(修复载重)。
2. **局部表格横滚受控** — table display:block+overflow-x:auto 局部横滚(真实渲染 clientWidth 落卡片内、scrollWidth 更大)；**无 page-level overflow-x:hidden band-aid**(负控制)。
3. **现有高级视觉保持** — specific 变化只有 `base_css`；6 主题 per-theme + 每个动效元素 **byte-identical**(独立重算 vs pre-fix baseline)。**门真**：无 approval→BLOCK；带 base_css approval→PASS_APPROVED。
- **test matrix**：360/390/430 × 5 元素 = 15。**NOT_DEPLOYED**：live build b189d3cc0703 不变(源=9690390a9fc8)。

## 实时未回归
NOT_DEPLOYED：改 worker 源+重算 build_id(→9690390a9fc8)，但不部署。live `/build.json`=b189d3cc0703(六主题+动效不变)。1 次只读 GET。

## 成本（unknown 不填 0）
生产 new_requests 0；D1 0；R2 0；model 0；cloud 0；只读 GET 1；人工=响应式修复+审计工具+验证器+复核撰写。

## 独立验证
实现者**不自签 PASS**。交独立 Agent 复核(见 adversarial_review.md)。
IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION

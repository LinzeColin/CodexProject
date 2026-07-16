# 独立对抗复核 · ADP-S7-P04-T084｜精修证据、内容层级、Diff、可访问性与 Reduced Motion

- **Iteration**: ITER-20260716-ADP-V01-FINAL-EXECUTION
- **实现者不自签 PASS**：交独立 Agent（general-purpose skeptic，agent `a0c6f138eecee183e`）复核。
- **裁决**：**CONFIRMED_SOUND**（六向攻击全部证伪失败；含真实浏览器 CSSOM reduced-motion 语义复核）。

## 复核者独立重算的六向

- **(a) reduced-motion 不丢功能（最微妙，实证确认）**：复核者枚举 `CSS` 与 `HERO_CSS` 中所有 `opacity:0`/`visibility:hidden`/`display:none`/transform-hidden 规则——唯一 base `opacity:0` 内容元素是 `.fr`(592)/`.bw`(594)，装饰是 `.fx-cosmos .meteor`(708)。在真实浏览器渲染 worker CSS 并套用 reduced-motion 规则体后，`.fr`、`.bw`、**及 `.card` 均计算为 `opacity:1`（可见）**；`.card{animation:frise both}` 的担忧被正确解决（`animation:none!important` 移除动画→fill-mode 失效→`.card` 用默认 opacity 1）。`animateGauge`(772)/`syncHeroVideo`(765) 在 JS 判 `reducedMotion` 跳终态/暂停；hero 标题另有可读正文卡副本(867)。无内容/功能丢失。
- **(b) 证据/推断**：`PROVENANCE_NOTE`（`讲义·推断` 徽章 + 「非原文表述；以原文为准」）在中心 `lessonHTML` 前置，四个讲义渲染点全覆盖（todayPage 870、itemPage 讲义卡 1121、itemPage grader 1122、reviewPage grader 1047/1051），每处配 `原文` 证据链接。浏览器确认徽章与两标记渲染；todayPage 重构输出与旧内联一致（相同 `i+1` 编号、相同 `esc`）除前置标记外。
- **(c) 键盘/触屏**：8 个 `onclick` 全在原生 `<button>`；主题 `<select>`、搜索 `<input>`/`<form role=search>` 原生。浏览器确认 reveal 按钮把焦点移入 `#revealBox`(tabindex=-1)、grade 按钮可聚焦、无焦点陷阱。
- **(d) 合同/设计保持**：`VB.detect_regression=[]`（逐字节一致，无 hashed 元素变更）；self-hash 复算 `452f7c5de919…` 匹配 `BUILD`；`node --check` 通过；live `/build.json` 仍 `b189d3cc0703`（NOT_DEPLOYED 确认）。
- **(e) 验证器诚实**：独立复现 pre-fix 无 provenance 标记（`provenance_note_defined=False`）、无 reveal a11y；去掉 `.fr,.bw{opacity:1}` 恢复确实翻 `all_content_preserved`→False。内容/装饰分类正确。
- **(f) 完整性**：验收=三条（全满足）。标题「Diff」诚实归属 S5-P02-T062（真实存在），本任务不重做；无越界过度声称。

## 复核者提出的唯一 caveat（我已如实修正——worker 未改）

复核者裁 **CONFIRMED_SOUND、可提交**，但精准指出一处**证据措辞过度声称**（非验收失败）：

> 审计 `touch_and_focus` 只读 base `button{min-height:44px}` 报 `touch_target_ok=True`，**未测量** `.btn-sm{min-height:34px}`(681)——它作用于 reveal（显示答案/讲义）、study（加入复习队列）、undo（撤销）等关键任务按钮。故「44px 触屏目标」对这些控件**并非普适成立**。但这是 **pre-existing**（origin/main 既有，T084 未触碰），34px **高于** WCAG 2.5.8 AA 24px 下限，关键任务全可点+键盘可达，故验收「关键任务键盘/触屏**完成**（completable）」功能上满足；主要召回(grade)与 run 按钮为 44px。

**我的处置（诚实优先，不越界改设计）**：
1. **不改 worker**——`.btn-sm` 是广用共享类，改其尺寸=改设计+改 base_css 视觉合同，超出 T084「纯加性 polish·不重设计」范围。worker 逐字节不变（BUILD 仍 `452f7c5de919`，合同逐字节一致，live 仍 `b189d3cc0703`）。
2. **修审计使其诚实**：`touch_and_focus` 现**逐控件测量** `button`(44px, AAA) 与 `.btn-sm`(34px)，报 `primary_meets_aaa`/`all_meet_wcag_aa`/`key_task_completable`；不再声称普适 44px。
3. **新增载重负控制**：验证器把 `.btn-sm` 缩到 24px 以下时 `key_task_completable` 必翻 False（否则报「vacuous」）——完成性判定非空跑。
4. **文档如实披露**：TASK_REPORT 前置 Q3/验收 clause 1 + known_gaps 明记 `.btn-sm`=34px（> AA 24px 下限、可点+键盘、< 44px AAA，pre-existing，欲达 AAA 走后续 T078 gate）。
5. **重跑确定性验证器**：`ACCEPTANCE = PASS`，exit 0（见 `test-results/a11y_content_tests.txt`）。

此修正**只收紧声称至事实**（worker/验收结论未变，复核者已确认其 sound），符合「不得编造 test results/evidence」的诚实约束。

## 结论

复核者对 **worker 与三条验收**返回 **CONFIRMED_SOUND**；其唯一 caveat（审计触屏措辞）我已如实修正为逐控件测量+披露，worker 未改。满足「实现者不自签 PASS」的独立复核门槛，可进入治理登记与合入。

# TASK_REPORT · ADP-S7-P04-T084｜精修证据、内容层级、Diff、可访问性与 Reduced Motion

- **Iteration**: ITER-20260716-ADP-V01-FINAL-EXECUTION
- **Task**: ADP-S7-P04-T084（Stage S7 / S7-P04 证据、历史和数据密集视图精修，size M，**S7 末任务**）
- **release_mode**: NOT_DEPLOYED（改 worker 页面体，重算 BUILD `d1dfcb3b7447`→`452f7c5de919`，不部署；live 仍 `b189d3cc0703`）
- **Depends**: ADP-S7-P02-T080；ADP-S7-P03-T082；ADP-S7-P03-T083

## 6 个前置问题
1. **证据/推断怎么区分？** — 现状 item 页渲染 `原文` 链接(证据) + 讲义分节(推断)，但**讲义无标注** → 读者可能误把生成推断当原文。
2. **怎样区分清晰？** — 中心化 `lessonHTML` 前置 **provenance 标注**(`<span class="badge">讲义·推断</span> 依据「原文」自动生成的推断摘要，非原文表述；以原文为准`)，凡渲染讲义处都带；todayPage 内联渲染重构为调 lessonHTML(DRY+得标注)。
3. **关键任务键盘/触屏？** — 全部 onclick 在原生 `<button>`/`<a>`(无 div-onclick)；每 button 有可访问名(文本或 aria-label)；primary/grade/run `button` 44px(AAA 触屏)，compact reveal/study/undo `.btn-sm` **34px**(> WCAG 2.5.8 AA 24px 下限，可点+键盘操作，**未达 44px AAA**——如实披露于 known_gaps，未改设计)；`:focus-visible`(T080)；reveal 按钮加 `aria-controls`+点击**把焦点移入揭示框**(disclosure a11y)。**完成性**=每控件 ≥ AA 下限 且键盘可达。
4. **reduced-motion 不丢功能？** — 既有规则禁所有 animation/transition,但**显式恢复内容类 `.fr,.bw` 到 opacity:1**(它们 base 是 opacity:0,在 HERO_CSS);gauge/video 在 JS 里判 reducedMotion 跳到终态;唯一保持隐藏的是装饰 `.meteor`(可接受)。故内容/功能不丢。
5. **不替换设计？** — 纯加性 polish(徽章+一句 provenance+焦点行为),不重设计;改在页面体函数→**六主题合同逐字节不变**。
6. **NOT_DEPLOYED？** — 改页面体+重算 build_id,不部署;live 不变。

## 交付物
- **证据/推断标注**(PROVENANCE_NOTE + lessonHTML 前置 + todayPage 重构)。
- **reveal disclosure a11y**(aria-controls + 焦点移入揭示框 + tabindex)。
- **content hierarchy 报告 + a11y 审计**(`a11y_content_tests.txt` + browser_measurements.json)。
- **工具** `tools/a11y_content_audit.py`：interactive_native/buttons_have_names/touch_and_focus/evidence_inference_distinct/reduced_motion_preserves_content/reveal_disclosure_a11y/preserves_contract（判别性）。
- **浏览器证明** `browser_measurements.json`（内置 Chromium）、**a11y_harness.html**、**pre_fix_worker.js**、**独立对抗复核** adversarial_review.md。

## 验收（PASS，verifier 独立重算，exit 0）
证据：`test-results/a11y_content_tests.txt`（ACCEPTANCE = PASS）。

1. **关键任务键盘/触屏完成** — 8 handler 全原生 button/a;全 button 有名;primary/grade/run 44px(AAA)、compact `.btn-sm` 34px(> AA 24px 下限,可点+键盘)、`:focus-visible`;reveal 焦点移入。**完成性**判定=每控件 ≥ AA 下限且键盘可达（非声称全 44px）。**负控制**:把 `.btn-sm` 缩到 24px 以下则完成性判定翻 False（载重）。**浏览器**:grade 按钮可聚焦、reveal 移焦。
2. **证据/推断区分清晰** — 讲义带 `推断` provenance 标注(中心 lessonHTML),与 `原文`(证据)链接区分。**负控制**:pre-fix 无标注。**浏览器**:标注渲染。
3. **reduced-motion 不丢功能** — 禁动画但恢复内容 `.fr,.bw` 到 opacity:1(装饰 meteor 可隐)。**负控制**:去掉恢复则内容不保(检查载重)。**浏览器**:CSSOM 规则恢复内容。
4. **现有高级视觉保持** — 六主题合同逐字节不变(polish 在页面体)。

## 实时未回归
NOT_DEPLOYED：改页面体+重算 build_id(452f7c5de919)，不部署。live `/build.json`=b189d3cc0703（六主题+动效不变）。1 次只读 GET。

## 成本（unknown 不填 0）
生产 0（NOT_DEPLOYED）。只读 GET 1；in-app 渲染 1；人工=provenance 标注+reveal a11y+审计工具+浏览器测试+验证器+复核。**Diff 视图**：标题含「Diff」——版本 Diff/As-of 视图已在 S5-T062 实现,本任务不重做,聚焦证据/推断/a11y/reduced-motion 三条验收。

## 独立验证
实现者**不自签 PASS**。交独立 Agent 复核（见 adversarial_review.md）。
IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION

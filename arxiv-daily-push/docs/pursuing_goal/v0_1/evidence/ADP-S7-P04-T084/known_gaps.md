# Known gaps · ADP-S7-P04-T084｜精修证据、内容层级、可访问性与 Reduced Motion

诚实披露**范围**、**验证形式**与 NOT_DEPLOYED 语义。

## 实现与不破坏承诺
- **纯加性 polish**（不替换设计）：证据/推断 provenance 标注（PROVENANCE_NOTE，中心 lessonHTML 前置）+ reveal disclosure a11y（aria-controls + 焦点移入揭示框 + tabindex）。改在**页面体函数**（lessonHTML/todayPage/graderHTML）→ **六主题视觉/动效合同逐字节不变**（detect_regression=0 specific）。BUILD d1dfcb3b7447→452f7c5de919。
- **todayPage 重构**：内联讲义渲染改调中心 lessonHTML——输出=旧分节(相同编号 `i+1`、相同 esc 转义)+ provenance 标注前置，无其他变化。

## reduced-motion 不丢功能（逐元素核实）
- base opacity:0 元素仅 3 个：`.fr`(fade-in 内容)、`.bw`(hero 逐字入场,均在 HERO_CSS)、`.fx-cosmos .meteor`(装饰)。reduced-motion 规则 `*{animation:none!important}` 禁所有动画,并**显式 `.fr,.bw{opacity:1!important;transform:none;filter:none}`** → 两个内容类恢复可见;meteor(装饰,`.fx` pointer-events:none)保持隐藏,可接受。
- `.card{animation:frise both}`：`animation:none!important` **移除**动画→无 fill-mode→`.card` 用默认 opacity(1),可见(非停在 from 的 opacity:0)。
- gauge(animateGauge)/hero video(syncHeroVideo)：JS 里判 `reducedMotion` 跳到终态/暂停首帧,内容仍显。
- **结论**：reduced-motion 下无内容/功能丢失（验证器负控制证恢复载重：去掉 `.fr,.bw` 恢复则检查失败）。

## 验证形式（如实）
- **确定性源审计**（a11y_content_audit）：交互元素原生可聚焦 + button 有名 + **每控件触屏尺寸逐一测量**（primary 44px AAA、compact `.btn-sm` 34px ≥ AA 下限）+ focus-visible + provenance 标注 + reduced-motion 恢复内容 + reveal disclosure。判别性负控制（pre-fix 无标注/无 reveal a11y；去恢复→内容不保；`.btn-sm` 缩到 24px 以下→完成性判定翻 False）。
- **内置浏览器**：provenance 标注渲染、reveal 移焦、grade 按钮可聚焦、reduced-motion 规则在 CSSOM 恢复 .fr/.bw。
- **reduced-motion 未做真机媒体模拟**：内置浏览器不暴露 prefers-reduced-motion 模拟；以 CSSOM 规则检查 + 确定性恢复检查替代（规则存在且恢复 .fr/.bw 到 opacity:1）；真机 reduced-motion 逐页留待部署后。
- **无真实屏幕阅读器测试**：a11y 以语义/焦点/名称的确定性 + 焦点行为浏览器证替代;真实 SR 逐流程留待后续/部署后。

## 范围（诚实）
- **交付覆盖**：证据/推断标注(clause 2)、键盘/触屏 a11y(clause 1)、reduced-motion(clause 3)实做+证;`content hierarchy report`=审计输出。
- **「Diff 视图」**（标题含）：版本 Diff/As-of 新旧对照已在 **S5-P02-T062** 实现,本任务不重做——聚焦标题的证据/内容层级/可访问性/reduced-motion 四项精修中可验的三条验收。
- **原文未加「证据」徽章**：仅给推断加标注(读者混淆风险在推断侧);原文链接自明为来源。若需对称可后续加。
- **compact `.btn-sm` 触屏尺寸=34px（如实披露，未改）**：reveal（显示答案/讲义）、study（学这个/加入复习队列）、undo（撤销）用 `.btn-sm{min-height:34px}`——**高于** WCAG 2.5.8 AA 24px 下限、完全可点+键盘可达，但**低于** 44px AAA 增强目标。此为 **origin/main 既有**（T084 未触碰 `.btn-sm`，属 pre-existing），且本任务范围是「纯加性 polish·不重设计」，故**不**在 T084 内改动共享 `.btn-sm` 尺寸（那会改设计并改 base_css 视觉合同）。验收「关键任务键盘/触屏**完成**」按完成性判定（每控件 ≥ AA 下限且键盘可达）成立；审计已逐控件测量、不再声称全 44px。**若欲达 44px AAA**，可作后续独立 polish（走 T078 approved-change gate）。
- **NOT_DEPLOYED**：live 仍 b189d3cc0703;T077 基线不重冻。

# Known gaps · ADP-S7-P01-T078｜建立 Visual/Motion Regression CI

诚实披露本任务的**范围**、**门粒度**与**未接线部分**。

## 对抗复核 fatal 已修：THEME_JS/HEAD_INIT/base-CSS 动效层此前 PASS（现 BLOCK）
- **复核发现 FATAL false-negative**：T077 合同里 `THEME_JS`(跑 blurTextIn/animateGauge/syncHeroVideo/reduced-motion 的**客户端动效行为**)、`HEAD_INIT`(防闪烁主题引导)、**base-CSS**(body/卡片)此前**只喂 master_visual(aggregate)、无 specific hash**——而门过滤 aggregate、只按 specific BLOCK，故掏空 THEME_JS 关键动效**竟 PASS**，defeat「Motion Regression CI」目标。**已修(扩展 T077 共享工具 visual_baseline，additive)**：加 specific hash `theme_js`/`head_init`/`base_css`(剥离已被 per_theme/fx_css/keyframes 覆盖的规则、不重叠)/`fx_css`(氛围动画 CSS);`theme_js`/`head_init`/`fx_css` 归为 **motion**。现掏空 THEME_JS 动效/HEAD_INIT 引导/氛围动画 CSS **全 BLOCK 且进 recording_checks.motion_regressions**。**additive 修复:master_visual/per_theme 哈希不变,T077 verifier 仍 PASS**。
- **复核第二轮再指出同类更窄一处**：`_base_css` 曾**剥掉 `${HERO_CSS}` 注入 token**——而它是 hero 样式到达任何页面的唯一路径，删它 → hero 无样式渲染，但 base_css 被剥后逐字节不变、只 master_visual 动 → **PASS**。**已修**：`_base_css` **保留 `${HERO_CSS}`**(它是布线文本非 HERO_CSS 内容、不与 hero_css 重叠)；现删 `${HERO_CSS}` 注入 → BLOCK on base_css。加负控制。**核:改 HERO_CSS 内容仍 flag hero_css、删注入 flag base_css、二者不重叠**。
- **复核 CONFIRMED_SOUND 后闭合 1 维护 latent**：`fx_css` 曾硬编码 fx 列表而 `_base_css` 剥任意 `.fx-*` 名——未来加未登记氛围层会成新逃逸。已改 `fx_css` **从 THEME_FX 派生** + 加 `partition_consistency` 断言源中每个 `[data-theme=X]`/`.fx-X` 名已登记(负控制:注入 `.fx-aurora` 被标 unregistered)。分区不能静默发散。
- 附带闭合复核 3 个 latent：①氛围动画 CSS(`.fx-cosmos .stars{animation}`)现进 motion 通道(fx_css)非仅 visual；②**像素阈值诚实标注**为「文档化 policy、本任务不执行(无 PNG 采集)」`pixel_layer_enforced=False`,唯一执行的是源级精确 diff;③`_valid_approvals` 加类型守卫,malformed approvals(非 list/非 dict entry/缺键)**fail-safe BLOCK 不崩**。

## 门的语义与边界
- **NOT_DEPLOYED / 纯门逻辑**：`visual_regression_ci.run_ci` 只在候选 worker 源与 T077 冻结基线之间跑 `detect_regression`，**不部署、不改 worker/主题**，实时 build `b189d3cc0703`(==T040)不变。
- **源级精确门 + 像素层容差**：对**源哈希**层门是**二值精确**(任一主题/动效源改动 diff=1 即 regression，无容差)；对**截图/像素**层(T077 180-cell schema)有**文档化容差** `PIXEL_DIFF_TOLERANCE=0.1%`(字体抗锯齿/GPU 渲染噪声)。**「允许的像素差有说明」=每个 approved-change 带非空 reason+approver，且像素容差在 thresholds.note 明述**。
- **approved-change 是 per-element 且需说明**：放行一个变化必须有 `{element, 非空 reason, 非空 approver}`；空 reason/空 approver/错 element 均不放行；**aggregate 元素(master_visual/contract_root)在 AGGREGATE 集、被过滤，不能用来 blanket-允许**任何 specific 变化(已核：approve master_visual/contract_root 仍 BLOCK)。

## 门覆盖(继承 T077 合同的完整性)
- 门的检测面**完全继承 T077** `detect_regression`(19 负控制、七轮复核 CONFIRMED_SOUND)：6 主题 token/组件/氛围 CSS+DOM、hero 标记、blurChars/sparkSVG 生产者、keyframes、THEME_JS、PAGE/heroSection/todayPage 三层布线、5 主题键数据、hero 视频字节、reduced-motion。**已核 6 主题 token 块删除 + 所有 fx 层/keyframe/hero 视频/生产者/reduced-motion 删改全 BLOCK,无 false-negative**。
- **over-detection 是安全方向**：删一个主题的**全部**规则(经组合选择器)可能连带 flag 邻近主题/hero_css——对**回归门**这是安全的过度敏感(仍 BLOCK),非漏报。演示用**干净的 token 块删除**只 flag 目标主题。

## 未做 / 后续
- **无真实 CI runner 接线**：本任务交付**门逻辑 + 模拟 PR 验证**，未把它挂进 GitHub Actions workflow(那是产品 CI 集成、需 workflow 文件 + 基线 checkpoint 存储,属后续/生产阶段)。当前 approved-change 记录是**内存对象**,未定义持久化格式(如 `approvals.yaml`)——留待接线时定。
- **无真实像素截图 diff**：像素容差是**声明的阈值**,未跑真实截图 SSIM/像素比对(那需 T077 未采集的 180 张 PNG + headless 浏览器,属后续)。当前源级门是确定性、可离线、可提交的骨干。
- **基线更新流程**：approved-change 放行一个 PR 后,如何**更新冻结基线哈希**(rebase 基线)未在本任务定义——留待 CI 接线时定(通常=approved 后重算 baseline 并记录 approval 到审计日志)。
- **motion 分类是元素级非语义级**：`recording_checks` 按元素(keyframes/fx/hero/producers=motion)分类,非逐条动画的语义 diff;足够 surface「动效损失」,但不区分「动画时长改了 vs 删了」。

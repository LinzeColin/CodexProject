# Adversarial review · ADP-S7-P01-T078｜建立 Visual/Motion Regression CI

独立对抗复核（general-purpose skeptic），职责是**证伪**验收（找 false-negative/橡皮图章门/approval 绕过/vacuous 控制/误导），非确认。**两轮 HOLE_FOUND（均为 false-negative，dangerous direction）→ 修复 → CONFIRMED_SOUND**。

## 攻击向量
(a) 门是否橡皮图章/有无 false-negative(删主题/动效却 PASS)；(b) approved-change 是否可绕过；(c) 控制是否 vacuous、verifier 是否独立重算；(d) 交付物(阈值/recording checks/approval)是否诚实；(e) edge/malformed;(f) NOT_DEPLOYED/纯度。

## 第一轮 HOLE（FATAL false-negative）
- **THEME_JS/HEAD_INIT/base-CSS 只喂 aggregate master_visual、无 specific hash**——门过滤 aggregate、只按 specific BLOCK，故掏空 THEME_JS 里的**关键动效**(blurTextIn/animateGauge/syncHeroVideo/reduced-motion 尊重/主题切换 onchange)与 HEAD_INIT 引导、base-CSS 改**全 PASS**，defeat「Motion Regression CI」。复核实证 6 例 PASS。approval process 本身 sound(无绕过)。
- **已修(additive 扩展共享工具 visual_baseline)**：加 specific hash `theme_js`/`head_init`/`base_css`(剥离已覆盖规则、不重叠)/`fx_css`(氛围动画 CSS);theme_js/head_init/fx_css 归 motion。6 例现全 BLOCK 且进 recording_checks.motion_regressions。附带闭合 3 latent(氛围 CSS 进 motion 通道、像素阈值诚实标注 pixel_layer_enforced=False、malformed approvals 类型守卫 fail-safe)。**master_visual/per_theme 哈希不变、T077 verifier 仍 PASS**;T077 manifest 重生保持一致(14→18 键、master 不变)。

## 第二轮 HOLE（同类更窄：${HERO_CSS} 注入）
- 复核指出 `_base_css` **剥掉 `${HERO_CSS}` 注入 token**——它是 hero 样式到达任何页面的唯一路径(`<style>${CSS}</style>` 里 CSS 含 `${HERO_CSS}`),删它 hero 无样式、但 base_css 被剥后逐字节不变、只 master_visual 动 → **PASS**。同 aggregate-only 逃逸机制、迁移到 HERO_CSS 布线。
- **已修**：`_base_css` **保留 `${HERO_CSS}`**(布线文本非内容、不与 hero_css 重叠);现删 → BLOCK on base_css。加负控制(删注入 BLOCK / HERO_CSS 内容变仍 flag hero_css 证不重叠)。

## 第二轮后：CONFIRMED_SOUND（复核明确无剩余 aggregate-only 逃逸）
- **决定性问题**：还有无 theme/motion 改动只动 master_visual 而 PASS?复核**枚举全部 136 个 `${...}` token 逐个删**+**整文件逐行删 fuzz** → **0 个 aggregate-only 逃逸**(唯一例外=一条纯 CSS 注释 line683,零渲染效果,PASS 正确)。实现者独立复现:`detect_regression` 对 136 token 无一"仅动 aggregate 无 specific"。
- 关键布线 token 全 BLOCK on specific:`${CSS}`/`${HEAD_INIT}`/`${FX_LAYERS}`/`${THEME_JS}`/`${opts.hero}`/`${THEME_OPTIONS.map}` → page_shell;`{ hero }` → hero_wiring;heroSection return '' → hero_section_fn。CSS 常量**完全分区**:每字节动某 specific extractor hash 或 base_css。
- **无新重叠**:approved 主题变(warm --bg)→ theme:warm 无 base_css;keyframe → keyframes+hero_css;.fx-cosmos → fx_css+theme:cosmos;HERO_CSS 内容 → hero_css(非 base_css,证 token 与内容独立)。theme:forest approval 仍 PASS_APPROVED。
- 无 vacuous 控制;确定性;T077+T078 verifier PASS;生产/media 未触。

## 复核指出的 latent(未来维护风险,已主动闭合)
- `fx_css` 曾硬编码 fx 列表 `("cosmos","minimal","techno")`,而 `_base_css` 剥 `.fx-[a-z]+` 任意名——未来加第 4 氛围层(如 `.fx-aurora`)未登记则 base_css 剥它、fx_css 不覆盖 → 新 aggregate-only 逃逸;`[data-theme=[a-z]+]` vs 固定 THEMES 同理。**已闭合**：①`fx_css` 改为**从 THEME_FX 映射派生** fx 名(自动同步 strip 集);②加 `partition_consistency` 断言源中每个 `[data-theme=X]`/`.fx-X`/`[data-fx=X]` 名**已登记**(X∈THEMES / THEME_FX 值),否则 inconsistent;verifier 负控制:注入 `.fx-aurora` → 被标 unregistered。现分区不能静默发散。

## 结论
两轮 HOLE_FOUND(FATAL THEME_JS/HEAD_INIT/base-CSS aggregate-only → 修;${HERO_CSS} 注入同类 → 修)→ **CONFIRMED_SOUND**：门阻断每个可构造的主题/氛围/动效删除与布线/注入移除(含 THEME_JS 关键动效、HEAD_INIT、氛围动画 CSS、hero 布线、${HERO_CSS} 注入),benign 不过度阻断,approved-change per-element 需说明且 malformed fail-safe,确定性;复核枚举 136 token + 逐行 fuzz 证**无剩余 aggregate-only 逃逸**;partition 自校验防未来发散。共享工具 visual_baseline additive 扩展(T077 master/per_theme 不变、verifier 仍 PASS、manifest 重生一致)。NOT_DEPLOYED(纯门逻辑读源哈希+1 只读 GET,生产未触,实时 build b189d3cc0703==T040)。判定：**可交独立验证 / SHIP**。

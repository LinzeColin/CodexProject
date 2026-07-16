# Known gaps · ADP-S7-P01-T077｜冻结六主题视觉与关键动效录屏基线

诚实披露本任务的**范围**、**截图证据形式**与**Owner gate 边界**。

## Owner gate：实现者不自签（最重要）
- 验收「**Owner 确认基线**」是**人工签署**，不是机器能自动 PASS 的。本包只完成**机器可验证的骨干**（合同提取 + asset hash + 覆盖矩阵 + reduced-motion 单独 + schema），并把结果**交付给 Owner 确认**。verifier 输出明确标注 `owner_confirmation_required=True` 且「不自签」。**S7 视觉 Owner gate 的最终确认待 Owner**。

## 截图形式：确定性 asset hash 为骨干，live 合同校验替代二进制截图
- **不可删除合同的真正后盾是确定性 asset hash，且覆盖完整视觉/动效表面**：①**master_visual hash** 覆盖整个 CSS + HERO_CSS + THEME_JS + HEAD_INIT + FX_LAYERS + 四映射——**任何视觉/动效源改动都改它**（完整性保证，非只 token 块）；②**per-theme hash** 覆盖每主题**全部** `[data-theme="X"]...` 规则（token 块 + 组件 + hero + nav 覆写，如 forest 12 条/cosmos 3 条）**加**其氛围动效 CSS（`.fx-cosmos .stars/.band/.meteor` 等，cosmos 11 条 fx 规则）——用于**归因**是哪个主题变了；③reduced-motion 独立 hash；④keyframes / fx-layers / hero-css 独立 hash。任一主题规则/氛围动效 CSS/hero CSS 或视频/reduced-motion/keyframe 被删改，`detect_regression` 都告警（verifier 8 个负控制逐一证明：删主题/改 token/改 fx 映射/改视频/改氛围 CSS/改组件规则/改 HERO_CSS/改 keyframe 全告警，benign 非视觉编辑不误报）。这是**机器可验证、可提交、可被 T078 阈值门复用**的基线。
  - **hero/dashboard DOM 也已纳入**：hero 视频与 cosmos 仪表盘标记(`<video id="heroVideo">`/`gaugeArc`/`.dash` 网格/`cosmic-live` LIVE 点)是 `heroSection()` 函数内的**局部 const**（非顶层模板字面量），`_hero_markup` 专门提取两段 hero section 并入 master_visual + 视频主题(minimal/techno/forest)/cosmos 的 per-theme hash + 独立 `hero_markup` hash。verifier 负控制(i)(j)：删 `<video id=heroVideo>` → 告警(hero_markup+视频主题)；改 cosmos gaugeArc → 告警(theme:cosmos)。live 实测 serve `id="heroVideo"`/`gaugeArc`/`.dash`。
  - **DOM 生产函数也已纳入**：hero section 内联调用的**视觉 DOM 生产函数** `blurChars`(techno 模糊入场 `.bw` span)与 `sparkSVG`(cosmos 仪表盘火花线)是顶层 `function` 定义(非模板字面量)，`_fn_body` 用括号匹配提取其函数体并入 master_visual + techno/cosmos 的 per-theme hash + 独立 `dom_producers` hash。verifier 负控制(k)(l)：掏空 `blurChars`(techno 模糊入场死) → 告警(theme:techno)；`sparkSVG` 描边改色 → 告警(theme:cosmos)。已核 heroSection 内**仅** blurChars/sparkSVG 两个视觉 DOM 生产者(其余 esc 是转义、toFixed/Number 是内建、var/url/rotate 是 hero 标记内的 CSS 语法已被 `_hero_markup` 覆盖)，故此层完整。
  - **三轮修复记录**：①初版 per-theme hash 只覆盖 token 块，漏氛围动效 CSS/组件规则/HERO_CSS → 改 master_visual 完整表面 + per-theme 全规则 + fx 规则（补 4 完整性控制）；②复核指出 hero/dashboard DOM 在 heroSection 局部 const 逃逸（删 hero 视频/gauge 不告警=schema 点名"关键动效"无保护）→ 加 `_hero_markup`（补 i/j）；③复核再指出 hero 内联调用的 DOM 生产函数 blurChars/sparkSVG 函数体逃逸（掏空 blurChars→techno 模糊入场死却无告警）→ 加 `_fn_body` 提取（补 k/l）。现共 **12 个**不可删除合同负控制。

## PAGE 壳「布线层」也已纳入（第四轮修复）
- **合同不仅冻结成分定义，也冻结把它们注入每页的布线**：`const PAGE = (…) => \`…\`` 是**箭头函数**(worker :767)，`_tmpl` 原只匹配 `const NAME = \``、够不到它。PAGE 是**把 `${CSS}`/`${HEAD_INIT}`/`${FX_LAYERS}`/`${THEME_JS}`/`${opts.hero}`、主题 `<select>`、`data-theme="warm"` 默认注入每页**的地方——**被冻结的成分若 PAGE 停止注入就 inert**（如删 `${FX_LAYERS}` → 全站氛围层不渲染，但 FX_LAYERS 常量未变、其 hash 不变）。**已修**：`_tmpl` 扩展支持箭头函数(`(?:\([^)]*\)\s*=>\s*)?`)，提取 PAGE 壳(1359 字符，含 `</html>`、未被行 780 嵌套 `<option>` 反引号截断)并入 master_visual + 独立 `page_shell` hash。verifier 负控制(m)(n)：删 `${FX_LAYERS}` 注入 / 删 `<script>${THEME_JS}</script>` 注入 → 告警(page_shell)。核实 PAGE 内 8 处布线注入删除现全部告警。现共 **14 个**不可删除合同负控制。

## THEME_OPTIONS 主题枚举也已纳入（第五轮修复）+ 主题集一致性交叉校验
- **合同不仅冻结成分定义与布线，也冻结「哪六个主题存在于 UI」的枚举**：`const THEME_OPTIONS = [['warm','暖纸学习'],…]`(worker :561)是 `<select id=theme>` **offered** 的六主题权威列表。删掉 `['cosmos','宇宙星河']` → cosmos 在切换器中不可达、用户永远选不到第六主题(其 CSS/映射沦为不可达死代码)，而 FX/CSS 常量未变、hash 不变。这是**主题身份数据**(与已 hash 的 THEME_NAV/FX/HERO/HERO_VIDEO 四映射平行——现五个主题键数据结构全部冻结)。**已修**：`_theme_options` 提取数组并入 master_visual + 每主题 per-theme(其 entry) + 独立 `theme_options` hash。verifier 负控制(o)(p)：删主题 entry → 告警(theme_options + theme:cosmos)；改 value key(cosmos→cosmosX，applyTheme 回退 warm 不可达) → 告警。
- **主题集一致性交叉校验**：`theme_set_consistency` 断言 **工具 THEMES == THEME_OPTIONS 键 == THEME_NAV 键**(此前工具硬编码六主题集与 worker 实际 offered 集**解耦**、从不读 THEME_OPTIONS)。删任一主题 → `consistent:False, missing_from_options:[该主题]`。现共 **16 个**不可删除合同负控制。

## heroSection 组装布线 + hero 视频字节也已纳入（第六轮修复）
- **A. heroSection() 组装布线**：`heroSection()` 的 `return video + dash`(worker :838)决定**实际组装出哪段 hero DOM**——改 `return video`→cosmos 仪表盘 hero(gauge 计数=点名动效)不再产出；`return ''`→今天页无 hero。它是 PAGE 的 `${opts.hero}` 与已 hash 的 hero 片段之间的**渲染布线**(与 PAGE 布线同类、更深一层)。**已修**：`_fn_body(heroSection)` 函数体并入 master_visual + 四个 hero 主题(minimal/techno/forest/cosmos)per-theme + 独立 `hero_section_fn` hash。负控制(q)：`return video`/`return ''` → 告警。**至此 PAGE→heroSection→video/dash 字面量→blurChars/sparkSVG 整条源链全 hash，无渲染布线残留**。
- **B. hero 视频字节**：三支 hero 视频(`assets/media/{velorah,voyage,aethera}.mp4`，git-tracked，1.5–2.5MB)是 minimal/techno/forest 的 hero 动效(点名"hero-video 播放")。此前只 hash HERO_VIDEO **路径**，同路径**换字节**不可检测——而 deliverable 字面是"asset hashes"。**已修**：`_asset_sha` 对每支视频**文件字节** sha256(64 字符摘要，非存 2.5MB blob，不违反 Low-Token/no-binaries)并入 video 主题 per-theme + 独立 `hero_video_assets` hash。负控制(r)：独立重算三支 sha256 互异且==工具所 hash(换字节可测)，bogus 路径→MISSING 标记。现共 **18 个**不可删除合同负控制。
- **修正 line 9 旧述**：此前"视频…被删改都告警"过宽——现**确实**如此(路径 via HERO_VIDEO/page_shell + 字节 via hero_video_assets 双覆盖)。

## todayPage hero 布线链最后一环 + live check 去空跑（第七轮修复）
- **A. 离线 hero 布线守卫**：PAGE 注入 `${opts.hero}`，而 `opts.hero` 由 `todayPage` 的 `PAGE('/', …, { hero })`(worker :849,:872)提供。丢掉 `{ hero }` → hero 视频与 cosmos 仪表盘(点名动效)不再插入今天页。它在 `todayPage`(页面内容函数)内、属声明的出范围边界，但**它是 hero 的最后渲染布线**。**已修**：`_hero_wiring` **结构化**捕获(`const hero = heroSection(...)` 行 + `{ hero }` 传递计数=2)并入 master + 独立 `hero_wiring` hash——**不 hash todayPage 内容**，故内容编辑不误触(已证 benign 内容改不告警)。负控制(s)：丢 `{ hero }` → hero_wiring 告警。
- **B. live check 去空跑(关键)**：`live_contract_check.py` 旧 `hero videos` 检查断言三个 `.mp4` 文件名在 HTML——但它们在**永远内联的 THEME_JS HEROVIDEO map**里、每页都有，**与 hero 是否渲染无关=tautological**(hero 全断线时仍 True)。**已修**：改为断言 hero **区块真渲染**——`id="heroVideo"`(hero-video 区块)+ `hero-cosmic`/`gaugeArc`(cosmos 仪表盘)在服务端今天页 HTML 中(两 hero 区块恒在 DOM，hero=none 主题由 CSS 隐藏)。现 live check 真验证 hero 渲染、非空跑。**修正 line 34 旧述**：live check 此前不覆盖 hero 存在(只覆盖 JS map)——现已覆盖。现共 **19 个**不可删除合同负控制。

## 一处透明披露（复核确认非 hole）
- 若有人**新增**一条 todayPage 条件式无-hero 返回路径(如 `if (rareCond) return PAGE('/', body);`)，`const hero =` 行与两处 `{ hero }` 传递**仍在**，故 `_hero_wiring` 与哈希不动；live check 仅当该条件在默认抓取触发时才抓。**这不是 hole**：它是**净新增的分歧行为(feature addition，常规 review 抓)**，非对冻结基线的**删除/改动**——现有 hero 定义/组装/布线/两条渲染路径全部完好冻结。覆盖它需 hash 整个 todayPage body(声明的出范围页面内容、且对每次合法内容编辑脆弱)=错误权衡。**当前设计(冻结身份定义+全布线链 + 非空跑 live check)是复核确认的 sound 边界**。

## 冻结范围：主题/动效身份层 + 布线 + 资产，非全站内容/通用结构生成器（如实界定）
- **冻结**：六主题 + 动效身份层的**成分定义**(主题 token/组件规则、氛围 fx CSS+DOM、hero 标记 video/dash + 动效生产者 blurChars/sparkSVG、reduced-motion、keyframes、theme JS、HERO_CSS、HEAD_INIT、映射) **+ PAGE 壳布线**(注入上述成分)。
- **不冻结**：①一般页面内容渲染(todayPage/radarPage/卡片正文)；②**通用结构生成器函数**(navLinks/navActive/vitalsCard 等)——它们产出**主题无关**的结构(同样的导航/卡片 DOM，仅由 PAGE 传入的 cls 与 CSS 区分主题)，被主题 token/CSS **消费**但本身非「令六主题相异」或「驱动动效」的身份成分。gutting navLinks 会同等破坏所有主题的导航结构=结构回归，非主题身份回归。这是**刻意且一致的边界**：master_visual 的「nothing can change」精确指**主题/动效身份 + 其布线**，非每个页面/导航的结构 DOM。若未来要把某结构也纳入，另加其提取到工具即可。

## Owner 备注：字体 token 引用但未 web 加载（先例，非本任务引入）
- 主题 token 引用 `Instrument Serif`/`Space Grotesk`，但 worker **未** `@font-face`/`@import`/link 加载它们（仅有 favicon link）——在没有这两款本地字体的机器上，该「视觉合同」的字体维度是 inert（回退系统字体）。这是**worker 先例行为，非 T077 引入**；本基线**如实冻结现状**（含这一未加载的字体引用）。**建议 Owner 在确认基线时留意**：若要字体也成为真实视觉合同，需另起任务加 `@font-face`/字体资产（超出 T077 冻结范围）。
- **未提交二进制 PNG 截图**：Low-Token 合同要求排除二进制；且内置浏览器本次 `preview_start` 超时（环境不稳）。因此「6主题×路由×5视口截图」以两种更强/更省的形式交付：①`visual_baseline_manifest.json` 的 **180-cell 矩阵 + 截图 schema**（`{theme}__{route}__{viewport}.png` 命名，覆盖全矩阵）；②`live_contract_check.py/.txt` **实测 live 生产站 serve 完整六主题合同**（6 token 块 + 4 fx 层 + reduced-motion + 映射 + hero 视频，build b189d3cc0703==T040）——这比像素截图更强地证明「基线==线上生产」。**实际像素 PNG 由 Owner 在确认时截取，或 T078 视觉 diff 阶段生成**（T078 deliverable=visual diff thresholds）。
- 诚实说：本任务**没有**逐 cell 采集 180 张 PNG，也**没有**录制视频 gif。交互「录屏」以 **schema + 动效合同指纹**形式冻结（motion themes=minimal/techno/cosmos/forest；录制项含主题切换/hero 播放暂停/cosmos gauge/techno blur/fx 层 + reduced-motion 变体）。像素级录制留待 Owner 确认或 T078。

## reduced-motion 单独记录
- reduced-motion 规则有**独立 hash**（与 contract_root 不同），schema 有独立 `reduced_motion_variant`（每条录制在 `prefers-reduced-motion:reduce` 下重跑，动画/过渡禁用、视频暂停）。verifier 负控制：删除 reduced-motion 规则 → 独立 hash 变 → 告警。

## 边界 / 未做
- **asset hash 是源级合同非像素级**：它检测**源代码**层面的主题/动效删改，不检测浏览器**渲染**差异（字体回退、GPU 抗锯齿等像素级漂移）。像素级 diff 是 **T078**（visual diff thresholds）的职责；T077 冻结的是源合同 + 覆盖 schema。
- **矩阵是 schema 非已采集资产**：180 cell 是覆盖矩阵定义 + 截图命名 schema，不是 180 个已存在的 PNG 文件。
- **动态路由未纳入矩阵**：/board/:id 与 /item/:id 是动态页，本基线只覆盖 6 个静态路由(today/queue/radar/system/history/search)；动态页视觉留待需要时扩展。
- **live 校验依赖网络**：`live_contract_check.py` 是联网只读 GET，非确定性单测；确定性骨干是 `t077_verify.py`（离线、从 worker 源重算 hash）。

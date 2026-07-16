# Known gaps · ADP-S7-P02-T079｜修复移动端溢出与数据密集布局

诚实披露**范围**、**验证形式**与 NOT_DEPLOYED 语义。

## 修复内容与不破坏承诺
- **base CSS 载重变更**（worker_cloud.js，3 处）：①`.card{…;overflow-wrap:break-word}`（长 URL/文号/DOI/关系换行）；②`main img,main svg,main video{max-width:100%}`（内容媒体不溢出）；③`@media(max-width:520px){table{display:block;overflow-x:auto;white-space:nowrap;-webkit-overflow-scrolling:touch}}`（宽表格**局部**横滚）。
  - 复核（skeptic）指出 `.card{min-width:0}` 对普通块级 `.card` 是**惰性无操作**（`main` 非 flex/grid），已**删除**该无操作声明，只保留载重的 `overflow-wrap`。
- **依赖但未新增的结构守卫**（pre-exist，本任务只依赖不改）：`.itemrow .body{flex:1;min-width:0}`（flex 子可收缩）、`*{box-sizing:border-box}`。审计单列为 `PREEXISTING_STRUCTURAL`，**不计入 T079 守卫**。
- **现有高级视觉逐字节保持**：经 T077/T078 合同验证——`detect_regression(pre-fix baseline, fixed worker)` 的 specific 变化**只有 `base_css`**；6 主题 per-theme + 所有动效元素（theme_js/keyframes/fx_layers/fx_css/reduced_motion/hero_markup/dom_producers/hero_section_fn/hero_video_assets/head_init/hero_css）**全部 byte-identical**。修复走 T078 **approved-change**（无 approval 会 BLOCK，带 base_css approval → PASS_APPROVED）。

## 验证形式（如实，已含真实渲染）
- **真实浏览器渲染证明**（`render_measurements.json`）：从**真实 worker base+HERO CSS**（post-L1 build `9690390a9fc8`）构造最坏情况页面（104 字符不可断 URL 作卡片文本 + 长文号/DOI + 8 列宽表 + 1600px 图 + topbar nav），内置 Chromium 在 **360/390/430** 渲染，测 `documentElement.scrollWidth`：三宽度均 `scrollWidth == innerWidth`、**无全页横滚**、**表格外 0 越界元素**、nav 不越界（navScrollWidth==navClientWidth==320@360）。
- **载重反事实**：同内容用 `origin/main`（pre-fix）CSS 在 360px → `scrollWidth 1210`（越界 850px）→ 证明修复是**必要且载重**的，非装饰。
- **判别性负控制**：真实 pre-fix CSS 审计得 **0/3**，剥离 T079 标记后也 **0/3** → 审计非空洞、有判别力。
- **确定性哈希重算**：6 主题 + 11 动效元素对 `origin/main` 逐哈希相同；BUILD 自哈希从零重算有效。

## NOT_DEPLOYED 语义（重要）
- **改 worker 源但不部署**：修复应用到 `deploy/cloudflare/worker_cloud.js`（product source of truth）并**重算 BUILD 自哈希**（`b189d3cc0703`→`d62009f8c708`→ L1 清理后 `9690390a9fc8`），但**不 `wrangler deploy`**。**live 站仍服务 b189d3cc0703**（六主题+动效不变）。源 build_id 与 live 暂时分歧=**已暂存未部署**的正常状态；**部署是单独 gated 步骤**（S7 exit 或专门部署任务），届时 live build_id 变为 9690390a9fc8。
- **T077 基线不重冻（本次）**：T078 known_gaps 明确「基线更新流程（approved-change 后如何 rebase 冻结基线哈希）留待 CI 接线时定」，且 approved-change 记录尚未定义持久化格式。故本任务**不**改 T077 `visual_baseline_manifest.json`——基线保持冻结在**已部署 live 构建 b189d3cc0703**。T079 只把源级 base_css 变更作为**文档化 approved-change** 落地（approval 记录在 `mobile_overflow_report.json` 的 gate_with_approval），基线 rebase 待「基线更新流程定义 + 本修复部署（live 变为 9690390a9fc8）」时再做。这比把基线重冻到**未部署源**更诚实、与 NOT_DEPLOYED 一致。

## 边界 / 未做（L3/L4，如实）
- **L3（架构·潜在，非阻断）**：守卫按溢出源逐一，`overflow-wrap` 只落在 `.card`，**无 body 兜底**（有意——band-aid 会裁剪内容而非受控滚动）。今天不存在卡片外可见不可断长文本（渲染确认 0 越界）；未来若在 hero/header/footer 放长文本需复查。
- **L4（范围外）**：表格 media query 门限 `max-width:520px`；**521–760px** 宽表会再越界（无 band-aid）。超出本任务 360/390/430 范围，留待后续。
- **`.btn-sm{white-space:nowrap}`（先例）**：小按钮文本不换行；当前按钮文案短（"学这个"/"深度追问"），不溢出；未来加长文案按钮需复查。
- **性能/动效未改**：本任务只治溢出，不动六主题/hero/氛围动效（S7-P03 才是性能打磨）。

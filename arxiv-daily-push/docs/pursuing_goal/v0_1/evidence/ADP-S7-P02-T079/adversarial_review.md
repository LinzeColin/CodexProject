# 独立对抗复核 · ADP-S7-P02-T079｜修复移动端溢出与数据密集布局

实现者**不自签 PASS**。由独立 skeptic Agent（`general-purpose`，与实现者不共享推理）对抗复核，目标是**证伪**三条验收，而非确认。

## 结论：CONFIRMED_SOUND（对抗复核后，再关闭 2 项潜在项）

复核 Agent 独立完成：枚举每个横向溢出源；用**真实浏览器**在 360/390/430 渲染最坏情况页面并测 `documentElement.scrollWidth`；跑**反事实**（pre-fix CSS）；对 `origin/main` **逐哈希重算** 6 主题 + 11 动效元素；从零**重算 BUILD 自哈希**。三条验收在经验上与确定性上均成立。

### 逐向量结论
1. **无全页横向滚动 — SOUND（真实渲染证明）**。复核 Agent 用**真实 worker CSS**（base+HERO 合并）构造最坏页面（4 列宽表 + 104 字符不可断 URL 作为卡片文本 + 74 字符 DOI + 长文号 + vitals 网格 + topbar `nav-top`），真实渲染：

   | 宽度 | 全页横滚 | scrollWidth | 表格外越界元素 |
   |---|---|---|---|
   | 360 | false | 360 | 0 |
   | 390 | false | 390 | 0 |
   | 430 | false | 430 | 0 |

   卡片外的每个不可断长串都换行（`overflow-wrap:break-word` 是继承属性，覆盖 `.card` 全部后代）。逐一排查了它点名的候选：`<pre>/<code>`（worker 中不存在）、`nav-top`（`flex:1` 无 wrap，但 4 个短 CJK 链接 min-content≈296px<320px 表头宽度，**恰好容纳**）、`nav-side`（≤640 隐藏）、`.dash` 200px 固定列（≤780 塌陷为 1fr）、hero 标题（逐字符 `inline-block` 会换行）、hero 视频（absolute + `.hero{overflow:hidden}`）。**范围内无未守卫的溢出源。**
2. **局部表格横滚受控 — SOUND**。渲染表格 `display:block`、`overflow-x:auto`、`clientWidth` 落在卡片内、`scrollWidth` 更大 → 在**卡片内**横滚，不推页；`display:block` 未破坏单元格布局（浏览器生成匿名表格盒）；无 page-level `body/html{overflow-x:hidden}` band-aid。
3. **现有高级视觉保持 — SOUND（独立重算）**。复核 Agent 不信任已提交报告，直接 `git diff origin/main`：worker 恰好 3 个 hunk（BUILD 行 + `.card` 的 overflow-wrap + 两条新 CSS 行）。经 `visual_baseline` 对 `origin/main` 重算：提交的 `pre_fix_baseline.json` == origin/main 实际哈希（诚实非编造）；specific 变化**只有 `base_css`**；6 主题 per-theme + 11 动效元素**全部逐字节相同**。
4. **NOT_DEPLOYED / build 完整性 — SOUND**。`origin/main` build_id=`b189d3cc0703` 且不含任何 T079 守卫 → live 站真未变。BUILD 自哈希从零重算 == 提交的 `source_sha256` 且 `[:12]` 匹配 → **自哈希有效**，且不触碰任何视觉合同哈希。**反事实**：同内容用 `origin/main` CSS 在 360px → `page_scroll:true`、`scrollWidth 1210`（越界 850px）→ **修复是必要的、载重的，非装饰**。

## 复核指出的潜在项与处置（ultracode：关闭可关的）
复核 Agent 判定这些为「cleanup，非阻断」；实现者据 ultracode 纪律**主动关闭 L1/L2，并把 L5 转为正面证据**：

- **L1（已修）— `.card` 的 `min-width:0` 是惰性无操作。** `.card` 是 `main` 的普通块级子元素（`main` 非 flex/grid，且无规则使 `.card` 成为 flex/grid item，已 grep 确认），`min-width:0` 对它无布局作用。**已从 worker 删除**（保留载重的 `overflow-wrap:break-word`），BUILD 自哈希重算 `d62009f8c708`→`9690390a9fc8`；删后真实渲染仍 `page_scroll:false`（惰性得证）。
- **L2（已修）— 审计过度计数。** 旧 `MO.audit()` 把 `min-width:0`/`box-sizing:border-box`/`max-width:100%` 也当 T079 守卫，而这些部分 pre-exist → 即使回退 T079 也会「命中」。**已重构** `mobile_overflow_audit.py`：`T079_GUARDS` 只含 3 个**载重且 T079 独有**的守卫（`overflow-wrap` 必须在 `.card{}` 规则内、media 全规则、table 局部横滚 media query），`PREEXISTING_STRUCTURAL`（`.itemrow .body{min-width:0}`、`*{box-sizing:border-box}`）单列为「依赖但非本任务新增」、不计入 T079。验证器加**载重负控制**：真实 pre-fix CSS（`pre_fix_worker.js`）审计得 **0/3**，剥离 T079 标记后也 **0/3** —— 证明审计有判别力、非空洞。
- **L3（架构·潜在）— 守卫按源逐一，无 body 兜底。** 这是**有意**的（band-aid 会裁剪内容而非受控滚动）。今天不存在卡片外的可见不可断长文本（已渲染确认 0 越界）。列入 known_gaps 供后续 hero/header/footer 若加长文本时复查。
- **L4（范围外）— 表格 media query 门限 520px。** 521–760px 宽表会再越界。超出本任务 360/390/430 范围；列入 known_gaps。
- **L5（已转正）— 缺真实截图交付物。** 已用内置浏览器在 360/390/430 真实渲染并落 `render_measurements.json`（含反事实），把原「部署后补」的缺口转为**当下正面证据**。

## 底线
三条验收（1）无全页横滚（2）受控局部表格横滚（3）保持高级视觉，均由**真实渲染 + 载重反事实 + 独立哈希重算**证明；build 自哈希与 NOT_DEPLOYED 状态诚实。复核判 gate=sound；L1/L2 已修，L5 已转正，L3/L4 如实披露且范围外。

**VERDICT: CONFIRMED_SOUND**（复核原文），实现者据此关闭 L1/L2/L5 后提交。

# 前端呈现基线 v1（权威 · 不得丢失）

> **Owner 指令（2026-07-17）**：「把 adp v1.1 写进 github main，作为前端呈现基线 v1，因为你们每次开发的时候都会丢掉 uiux 动效，后面我会不断优化，但你们不要再丢掉了，**再丢掉我本地就完全不能恢复**！」

## 这是什么

`前端重构增补包/` 是 ADP 六主题界面语言的**设计源头规格**（V1.0，2026-07-14），由 Owner 提供。
它是**唯一权威**：任何前端呈现（主题、首屏、导航、动效、视频）的取舍，以本包为准。

| 文件 | 内容 |
|---|---|
| `前端重构增补包/README.md` | 与 V0.3 交付包的关系、防冲突声明（**唯一覆盖对象** = V0.3 的 `07_UIUX交互规范.md` 六主题一节） |
| `前端重构增补包/01_六主题规范.md` | 六主题完整设计语言：对标来源 → 反向分析结论 → 令牌 → 结构 → 动效 → 视频资产 |
| `前端重构增补包/02_首屏与导航结构.md` | 四种首屏 × 三种导航的实现契约、视频资产、**实现红线**、验收口径 |

## 出处与完整性（可逐字节复原）

- 原始文件名：`ADP主题动效v1.1.zip`（Owner 于 2026-07-17 提供）
- **原始存档逐字节保留**：`_原始存档/ADP主题动效v1.1.zip`
  `sha256 = 253f7bf6881bd2df377d6a286670f1441b3c093b94de34c7b01f1406dfda91a7`
- `前端重构增补包/` 下三份 `.md` 与存档内容**逐字节一致**（解包时已核验）：
  | 文件 | sha256（前 16） |
  |---|---|
  | `01_六主题规范.md` | `a20462b2fb85249a` |
  | `02_首屏与导航结构.md` | `eb67fcc56b987382` |
  | `README.md` | `5f58934e5a148975` |
- 存档被 `.gitignore` 的 `*.zip` 规则覆盖，故**强制纳入版本控制**（`git add -f`）——**持久化正是本任务的目的**；6KB，远低于仓库大文件卫生阈值。

## 为什么同时存 .md 和 .zip

- `.md`：可读、可 diff、可 grep、可被机器门引用——将来能**被保护**，而不只是被存着。
- `.zip`：逐字节存档，保证**即使解包/改名/编码出错也能原样复原**（Owner 本地已无第二份）。

## 与线上实现的符合性（核验于 live build `204c97eb5406`，2026-07-17）

| v1.1 契约 | 线上 | 证据 |
|---|---|---|
| 四种首屏按主题切 **DOM 结构**（非仅换色） | ✅ | `data-hero` = `none`（暖纸/清新）/ `video`（简约专注/炫技/森林）/ `dash`（宇宙星河） |
| 三种导航模式 | ✅ | `data-nav` = `sidebar` / `topbar` / `dock` 齐全 |
| 实现红线 4：视频转自有存储，CDN 直链仅原型期 | ✅ | `/media/velorah.mp4`、`/media/voyage.mp4`、`/media/aethera.mp4`；**cloudfront 直链残留 0** |
| 实现红线 1：`muted`/`loop` 显式布尔 + `play()` | ✅ | `.muted=true`、`.loop=true`、`.play()` |
| 宇宙星河 = 仪表盘（环形量表 + 三格 + 七日折线） | ✅ | `/104`、`STREAK`、`RETENTION`、`REVIEW DEBT`、gauge、sparkline |
| `prefers-reduced-motion` 保静态首帧 | ✅ | 存在 |

**一处诚实偏离（非丢失）**：`02_首屏与导航结构.md` 列出的 **NOVA 深空视频**（宇宙星河底层）其 CDN 源已 **403 失效**，故线上以 CSS 四层银河 + 仪表盘替代。源已死，不是被丢掉。其余三个视频已按红线 4 转存自有存储。

## 它是怎么被保护的（不再靠人记得）

设计源规格（本目录）回答**为什么**；机器门回答**有没有被改**：

- `docs/pursuing_goal/v0_1/evidence/ADP-S7-P01-T077/visual_baseline_manifest.json` — 六主题视觉/动效契约的**首次冻结**（Owner 视觉门）。
- `docs/pursuing_goal/v0_2/evidence/ADP-V02-P05-VISUAL-REFREEZE/visual_baseline_manifest.json` — **当前权威基线**，重冻到线上 build，并记录相对 T077 的漂移与逐条归因。
- `docs/pursuing_goal/v0_1/tools/visual_regression_ci.py` — 门本体：任何主题/动效契约元素被改动而无批准记录即 **BLOCK（exit 1）**；并检查未注册主题/ambience（`partition_consistency`），堵住"只动聚合哈希"的静默逃逸。

**规矩**：改动六主题/首屏/动效 ⇒ 先对照本包 ⇒ 若确需偏离，必须留下批准记录并**重冻基线**；`per_theme` 哈希（= 六主题身份本身）变化**必须走 Owner 视觉门**，工具会拒绝自动重冻。

### 这道门现在是自动的（不再靠人记得）

`.github/workflows/arxiv-daily-push-visual-gate.yml` 在**每次改到 worker / 基线 / 门工具时自动运行**，
判 BLOCK 即**推送变红**。（此前它虽然存在却**没有任何人调用**，且裸跑 `exit 0` 零输出 = 空跑通过。）

**要做一次经批准的视觉改动**（正门，不要去删工作流）：
1. 新建 `arxiv-daily-push/docs/design/visual_change_approvals.json`，内容是一个数组：
   ```json
   [{"element": "keyframes", "reason": "为什么必须改，一句话说清", "approver": "linzezhang"}]
   ```
   `element` 取门报出的 `blocked_on` 名（如 `base_css` / `keyframes` / `theme_js` / `hero_css` / `fx_css` …）。
   **三个字段缺一不可**：缺 `reason` 或 `approver` 的残缺记录**不会放行**（工具 fail-safe，已实测）。
   该文件默认不存在 = **默认拒绝一切未批准的视觉改动**。
2. 改完后用 `docs/pursuing_goal/v0_2/tools/visual_baseline_refreeze.py --live-build-id <新build> --write` **重冻基线**；
   若漂移**不可归因**或 `per_theme` 变了，它会 **ABORT 并拒绝写盘**——那说明这不是一次该被自动祝福的改动。

## 后续

Owner 会持续优化本规格。新版本请**新增目录**（如 `前端呈现基线_v2/`）并在此说明取代关系，**不要原地覆盖**——历史版本是复原的最后一道保险。

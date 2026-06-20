# OpenAIDatabase

Local-first personal memory database for ChatGPT/Codex exports.

This repository is intended to be the durable memory database for the user.
Any AI agent should be able to use it to understand the user's preferences,
standards, memory history, project context, safety boundaries, and accepted
long-term memories.

## Governance Entry

Canonical governance files live under `docs/governance/`.

- Model specification: `docs/governance/MODEL_SPEC.md`
- Model registry: `docs/governance/model_registry.yaml`
- Formula registry: `docs/governance/formula_registry.yaml`
- Parameter registry: `docs/governance/parameter_registry.csv`
- Development ledger: `docs/governance/DEVELOPMENT_LEDGER.md`
- Delivery plan: `docs/governance/DELIVERY_PLAN.md`
- Version matrix: `docs/governance/VERSION_MATRIX.yaml`
- Traceability matrix: `docs/governance/TRACEABILITY_MATRIX.csv`

Legacy files `功能清单`, `开发记录`, and `模型参数文件` are compatibility
indexes only. Do not add new editable model, parameter, task, acceptance, or
version facts there.

It contains the `openai-memory-analysis` skill and a minimal vault layout. It
ingests manually downloaded OpenAI export ZIPs, generates redacted pending
memory candidates, creates human-readable weekly/monthly memory packs, and
exposes a read-only search/fetch layer.

The human-facing goal is not just storage. Each processing run should help the
user maximize ROI, improve personal capability growth, identify repeated low
value loops, discover future opportunities, and decide what to do next.

## Hard Boundaries

- Do not automate ChatGPT login, export download, browser profiles, cookies, or saved-memory writes.
- Do not commit raw `OpenAI-export.zip` or unredacted raw messages.
- Do not commit `.local_keys/`, secrets, tokens, passwords, private keys, or cookies.
- Do not upload plaintext high-risk secrets to GitHub. Finance/trading agents should use committed `secret_ref` metadata only to request authorized local secret access.
- Generated memory candidates stay `pending` until manually reviewed.
- Default user-facing delivery is chat output plus GitHub-backed repository updates. Do not create local delivery ZIPs or copied report packages unless explicitly requested.
- Keep local storage lean: remove transient delivery packages, copied report directories, `.DS_Store`, and Python cache after use. Do not delete source exports or encrypted raw archives without explicit authorization.
- Every run must compare current conclusions with the previous processed snapshot and explain what changed, strengthened, weakened, became obsolete, or became a new opportunity.

## Human-facing Output Standard

Every run must output a chat-ready review that a human can use. Do not only
show IDs, hashes, schemas, or agent-internal metadata.

User-facing output should be Chinese by default, except professional terms,
code identifiers, API names, model names, and source titles.

The first section must be content conclusions generated from the processed
memory records: topics, what to do, what to remember, recommendations,
opportunities, ROI implications, and personal-growth signals. Processing status
and database mechanics come after this.

The second section must compare the current conclusions with the previous
processed snapshot. It should explain new themes, stronger/weaker themes,
new decisions, changed rules, obsolete conclusions, risks, opportunities, and
what these changes mean for next actions and personalization.

The repository backup must include the exact chat-facing report as
`data/derived/chat_reports/*.chat_report.md`, but the assistant must still
paste the report into chat after every run. File paths are audit backup, not the
primary answer.

Required run output:

0. 本次资料内容结论
0.1. 本次资料与上一轮结论对比
1. 新增长期记忆、旧记忆更新、新增决策、增量变化分析
2. 已废弃的信息
3. 需要更新进 Codex 和 ChatGPT 的记忆
4. 未来回答应遵守的规则
5. 临时信息和敏感资料备份
6. ROI 最大化建议
7. 个人能力成长建议
8. 潜在发展 / 投资机会

Every processing run must also include two independent review perspectives:

1. 战略/机会/ROI reviewer: missed angles, future opportunities, investment/business possibilities, leverage points, and personal capability growth.
2. 执行/质量 reviewer: omissions, weak evidence, stale assumptions, conflicts, unsafe conclusions, and database-quality improvements.

Memory tiers:

1. 核心画像：身份、简历、成长经历、倾向、偏好、Taste、计划、规划、历史等根本信息。
2. 一般：项目、决策、重要 workflow、中长期约束、机会和可复用上下文。
3. 临时：短期事件、敏感细节、低确定性上下文、一次性信息；保留脱敏摘要和加密原文引用，默认低权重召回。

Weekly review output:

0. 本周资料内容结论
0.1. 本周资料与上一轮结论对比
1. 本周核心事件
2. 本周重要决策
3. 本周反复出现的问题
4. 本周新偏好
5. 本周项目进展
6. 本周需要 ChatGPT 未来记住的上下文
7. 本周临时信息和敏感资料备份
8. 与旧记忆冲突的地方
9. 下周行动清单

Monthly review output:

0. 本月资料内容结论
0.1. 本月资料与上一轮结论对比
1. Core Profile Memories
2. Important Mid/Long-term Memories
3. Temporary Memories
4. Deprecated/Conflicting Memories
5. Updated Profile
6. Updated Project Index
7. Updated Decision Log
8. Updated Timeline
9. 适合上传到 ChatGPT Project 的 compact context pack

## Quick Commands

```bash
python3 skills/openai-memory-analysis/scripts/openai_memory_analysis.py self-test \
  --out-dir /tmp/openai-memory-analysis-self-test

python3 skills/openai-memory-analysis/scripts/openai_memory_analysis.py run \
  --inputs /path/to/OpenAI-export.zip /path/to/chatgpt_memory_vault_codex_pack.zip \
  --database-dir . \
  --out-dir /tmp/openai-memory-analysis-run \
  --archive \
  --archive-key-file .local_keys/openai_memory_analysis.key

python3 skills/openai-memory-analysis/scripts/openai_memory_analysis.py search \
  --database-dir . \
  --query "Codex workflow" \
  --limit 10
```

## Memory Atlas

`apps/memory-atlas` is an independent Vite + React + Three.js local app for
interactive memory visualization. It is not an Obsidian/Notion/Chrome plugin.

The app is one merged platform with multiple selectable data-source slices.
The homepage data-source selector must expose exactly three choices:
`总数据源` (all data sources together), `ChatGPT`, and `Codex`. Galaxy,
Notion Map, ROI, Obsidian Graph, Timeline, Contribution Grid, Word Cloud,
Search, Summary & Iteration, and recommendations all share the same visual
shell; only the selected analysis source changes.

Future platform sources are registered in
`config/data_sources/source_registry.json`. Current active internal sources are
`memory_atlas` (shown as `ChatGPT`) and `codex` (shown as `Codex`); planned
compatible sources include `wechat`, `xiaohongshu`, and `douyin`. Planned
sources remain registry-only until the selector is explicitly expanded. They
must not create fake records or appear as empty homepage options. A future
ingestor should emit canonical redacted derived events with `source_id`,
`record_id`, `occurred_at`, `record_type`, `summary`, `sensitivity`,
`memory_tier`, `importance`, `confidence`, and `dedupe_key`. Raw platform
exports, full messages, media, credentials, cookies, sessions, and plaintext
high-risk secrets must stay out of GitHub.

The app consumes the redacted, derived snapshot
`data/derived/visualization/memory_atlas.json` through runtime fetch at
`/memory_atlas.json`, generated from the existing memory database. It must not
read raw exports or mutate `active_memory.jsonl` directly.

The committed snapshot is `public_redacted_read_only_visualization`: private
memory statements are represented as low-sensitive summaries, and public JSON
must not contain source refs, record hashes, record indexes, local absolute
paths, conversation refs, writeback conflict tokens, frontend proposal refs,
statement policy flags, retrieval-weight internals, source-kind internals, or
sensitivity detail fields. Full memory content remains in the database/search
layer for authorized agents.

Writeback goes through versioned change proposals. The frontend can create,
compare, export, and rollback proposal JSON from the Inspector, but it cannot
mutate `active_memory` directly. Each proposal carries a readable diff,
version-chain metadata（版本链）, parent proposal id, and rollback proposal contract. A
controlled agent must reload the current database, check conflicts/sensitivity,
write proposal history, and commit a rollback point before changing long-term
memory.

Project documentation entry points for future agents:

- `docs/USER_REQUIREMENTS.md`: durable user requirements and output rules.
- `docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md`: real model assumptions,
  inputs, processing methods, outputs, formulas, thresholds, and iteration
  policy. This file is the source of truth for "model parameters"; it is not a
  feature list.
- `docs/MEMORY_ATLAS_DELIVERY_RECORD.md`: historical process record, delivery
  and run modes, acceptance standards, backlog, and handoff checklist.

Current visualization modes:

- Visual density rule: every navigation page must keep 视觉化程度 80%+ as the
  default reading surface. Lists and text can exist as drill-down, but Galaxy,
  Notion Map, ROI Dashboard, Obsidian Graph, Timeline, Contribution Grid, Word
  Cloud, Search, and Summary & Iteration must all expose evidence-bearing visual
  marks, charts, graphs, grids, timelines, or signal cards synchronized with the
  current filters.
- Interaction Lens: every view shares a compact focus layer between filters and
  the visualization. It shows the current selected node or contribution period,
  active filter chips, previous/next focus buttons, theme focus, and reset
  controls. Filter chips clear individual filters without mutating the memory
  database; theme focus only changes the current browser view.
- Galaxy: Three.js scene. WebGL 正常时不叠加 HTML 点层，并使用不透明 WebGL 背景和逐帧清屏，避免 2D 残影；WebGL 内部程序化星云纹理负责旋臂、核心辉光、尘埃带和星云云团，避免退回只有光点的点云；只有 WebGL fallback 才启用可点击点层。Galaxy 支持 hover 最近星体预览、点击选中后相机自动飞近并聚焦、关联边高亮、关联邻居节点脉冲高亮、右上角视角重置和缩放按钮；hover 只做预览，点击才同步右侧 Inspector。聚焦后必须使用局部邻域布局：高权重邻居进入内环 primary layer，次级邻居进入外环 secondary layer；高连接主题节点只显示 Top 局部邻居和有限焦点边线，其余显示为折叠数量，避免一次性拉出过多边线。选中节点后，画布边缘显示内环邻居小型详情卡，卡片包含标签、层级/分类、权重排名，并可点击跳转到对应邻居节点。
- Notion Map: project/document nodes linked through atlas edges. 顶部保留简短状态条，说明当前图谱按主题簇、节点详情和项目/决策关系读取。
- ROI Dashboard: memories sorted by `metrics.roi.leverage_score`. It must show
  synchronized mini-bar visual summaries for level assets, topic categories, and
  recommended actions so the page is not just numeric cards plus a list.
- Obsidian Graph: lazy-loaded force-directed graph scene modeled on Obsidian's
  built-in Graph View contract. It supports global graph/local graph, local
  depth, search-file filtering, tag/attachment/existing-file/orphan toggles,
  color groups, arrows, text fade threshold, node size, link thickness,
  time-order animation, center/repel/link force controls, link distance,
  wheel/+/- zoom, drag-to-pan, drag-to-position nodes, hover neighbor
  highlighting, click-to-sync Inspector, and a right-click context menu.
  图谱设置必须可折叠，折叠后保留清晰的“图谱设置”入口。节点显示名必须采用
  `层级 · 主题 · 关键词`，关键词不得重复层级或主题词。图谱中必须显式显示
  `Focus - Connectivity`，包括当前焦点、连接数、可见邻居数、关系密度和层级，
  不能只靠边线高亮表达连接状态。
- Timeline: memory, decision, project, and timeline-event nodes are positioned
  by real event dates. 横轴必须显示可读的真实事件日期标签，淡色月份网格只作为背景定位参考。
  Timeline is a dynamic interactive workspace, not a table/list or static dot
  chart: it has a 动态窗口, zoom controls, replay 播放游标, wheel zoom, density
  track, density backdrops, hover detail strip, and click-to-sync Inspector.
- Contribution Grid: daily/weekly/monthly/yearly interaction and memory
  increment proxy. 贡献网格一屏优先：日/周显示全年 365/366 格，月/年显示
  连续两年 24 列；尺度按钮和增量指标合并，主网格必须优先保留全景空间，
  热度标尺必须常驻显示，并采用短长方形连续渐变趋势条；图例和热力单元必须让
  0、低频、中频、高频明显分离，使用 log 映射和平滑蓝色系色带把低频从空值里拉出来，
  从近黑、冷蓝灰、深海蓝、钴蓝、亮蓝过渡到冰蓝，表达从 0 使用到深度使用，
  避免黄色、橙色、脏绿和刺眼蓝紫断层。标尺不显示冗余文字说明，
  宽度约等于日表格下 3 列。日/周必须共用同一个全年 7 行 x 52-54 列坐标面：
  日视图是一格一格的正方形，周视图是一整列一整列的可点击整体板块，
  内部必须显示与日视图同源同色阶的 7 个日段，而不是另一张表或单条大色块。
  月视图保留连续两年 24 列坐标面；年视图使用左右并排的两张年度对比卡片，
  便于同一屏比较两个年份。周、月内部趋势保持从上到下读取，并通过连续渐变实现
  平滑过渡：周格内部按 7 天纵向排列，月格内部按每日颗粒度纵向排列，年卡片内部按
  12 个月从左到右的横向热度条、季度轴、年度分数、消息数、记忆数和环比摘要显示连续趋势，
  年卡片不得在狭窄月柱内部显示 1月/2月 这类微型文字，不能退回
  大色块年视图。移动端使用独立紧凑 layout，压缩 toolbar 与 gap，保持无横向页面溢出和全年全景。日视图按周一到周日排列并
  显示左侧星期标签；周视图必须使用当前年份内的自然周列聚合，避免 ISO week 在
  年初/年末把同一周切到相邻列。日/周/月/年标签旁有年份下拉，只显示有历史记录
  的年份。
- Word Cloud: 词云洞察是独立导航板块，包含 `Heatmap`、`Bubble Chart` 和
  `Word Cloud` 三层。Heatmap 显示主题 x 记忆层级密度；Bubble Chart 显示
  主题 ROI 与近期增量；Word Cloud 显示高频语义词。三层都必须可点击并同步右侧
  Inspector，不能只是静态装饰图。
- Summary & Iteration: 总结与迭代是独立导航板块。它必须显示本次切片的
  核心画像、决策、近期增量、可行动线索，并内置给 ChatGPT / Codex 等 agent
  使用的建议 `Personalization / Memory`、`Agents.md / 执行规则`、`config.toml`
  和 `Memory` 内容，同时显示更新时间。新增、修改、降权/删除含义必须在
  personalization/config 层表达，不代表删除底层历史备份。
- Human Summary: Inspector 和搜索复盘页默认展示人能直接使用的内容：
  目前记录了什么、需要做什么、记得做什么、机会/增长方向、风险提醒；低敏
  数据库摘要保留为折叠详情，避免把 agent 内部字段当成主要信息。回答规则、
  决策、项目背景等分类不能只显示模板句，必须提炼成主题化短标题；同类重复
  只在显示层合并并标注数量，不删除底层历史。搜索复盘页必须有当前结果分布、
  高频主题、记忆层级、近期/决策等可视化摘要，不能退回纯搜索结果列表。
- Recommendations: 搜索复盘页内置两个建议板块：
  `Memory（给 ChatGPT / Codex Personalization）：未来回答与个性化` 和
  `Meta Data（给 ChatGPT / Codex Agents.md）：执行规则与验收标准`。每个板块显示新增、修改、
  降权/不再默认使用和当前有效项。降权只是 personalization 层的召回/权重建议，
  不是删除历史备份；展开详情里仍保留给 ChatGPT / Codex 使用的结构化字段。

Real Codex local data sync:

- `scripts/sync_codex_memory_data.py` reads real local Codex session logs from
  `~/.codex`, writes redacted derived summaries under `data/processed/codex/`
  and `data/derived/codex/`, and can rebuild `memory_atlas.json`.
- Agent entry points for GitHub-backed Codex usage records:
  - `data/processed/codex/codex_activity_snapshot.json`: latest aggregate
    range, session count, message/tool-call totals, top topics, top tools, and
    backup policy.
  - `data/processed/codex/codex_daily_activity.jsonl`: daily activity buckets
    for Contribution Grid and time-series behavior analysis.
  - `data/processed/codex/codex_session_manifest.jsonl`: per-session redacted
    manifest for agent behavior, topic, tool, and preference analysis.
  - `data/derived/codex/codex_behavior_report.md`: human-readable Codex usage
    and personalization report.
  - `data/derived/codex/codex_agent_recommendations.json`: structured Memory
    and Meta Data recommendations for ChatGPT/Codex personalization and
    `AGENTS.md` style behavior.
  - `data/derived/visualization/memory_atlas.json`: merged redacted snapshot
    consumed by Memory Atlas; select `codex` as the analysis source to isolate
    Codex usage data.
- The sync output is GitHub-safe by design: no raw transcript, cookies,
  sessions, local absolute paths, private keys, API keys, broker credentials,
  or plaintext high-risk secrets. Finance/trading agents discover credentials
  through `secret_ref` metadata and controlled local resolvers, not GitHub
  plaintext.
- `scripts/install_codex_weekly_sync.py --load` installs a macOS LaunchAgent
  that runs every Monday 09:00 local time, rebuilds the Atlas snapshot, commits
  the redacted Codex-derived data, and pushes to GitHub.

Notion Map 的图内节点不渲染文字标签；详情通过 title、aria 和 Inspector 查看。
Obsidian Graph 按 Obsidian Graph View 的文字淡出阈值显示节点标签：默认保持克制，
缩放、悬停、选中或高连接节点才显示标签，同时通过 hover 邻接高亮和 Inspector 保留
具体信息入口。记忆节点标签统一显示为 `层级 · 主题 · 关键词`，关键词不能重复层级或
主题词；设置面板支持折叠，Focus - Connectivity 状态条必须常驻显示焦点连接强度。
Galaxy 低高度视口保留最小画布高度，HUD 自动换行且不裁切，避免选择卡片压出
银河画面或遮挡核心区域。

macOS launcher 只打开一个启动页，服务 ready 后由该页面自动跳转到本地
Memory Atlas，避免点击 `.app` 后连续打开两个网页。

Deployment route: keep local Vite + React + Three.js as the primary dev mode,
support Cloudflare Pages + Access for protected static sharing, and reconsider
Tauri only after the data contract, writeback proposal flow, and visualization
performance are stable. See `docs/MEMORY_ATLAS_DEPLOYMENT.md`.
For authorized Cloudflare deployment, use
`docs/MEMORY_ATLAS_CLOUDFLARE_RUNBOOK.md` and the templates under
`config/cloudflare/`.
The final goal audit is explicit about the external gate: without real
Cloudflare Pages deployment and Access verification evidence it reports
`LOCAL_PASS_EXTERNAL_AUTHORIZATION_REQUIRED`, not complete.

```bash
python3 scripts/build_memory_atlas_data.py \
  --database-dir . \
  --output data/derived/visualization/memory_atlas.json
python3 scripts/build_agent_context_pack.py --database-dir .
python3 scripts/sync_codex_memory_data.py --database-dir . --build-atlas
python3 scripts/install_codex_weekly_sync.py --load

npm ci --prefix apps/memory-atlas
npm run build --prefix apps/memory-atlas
python3 scripts/audit_memory_atlas_release.py --publish-dir apps/memory-atlas/dist
python3 scripts/audit_memory_atlas_visual_acceptance.py
python3 scripts/audit_memory_atlas_acceptance.py --publish-dir apps/memory-atlas/dist
python3 scripts/audit_memory_atlas_goal_completion.py --publish-dir apps/memory-atlas/dist
python3 scripts/preflight_cloudflare_pages_access.py --publish-dir apps/memory-atlas/dist
python3 scripts/deploy_memory_atlas_cloudflare.py
npm run dev --prefix apps/memory-atlas
```

After cleaning transient frontend folders or after local launcher install, use
the source/runtime readiness audit without `--publish-dir`:

```bash
python3 scripts/audit_memory_atlas_goal_completion.py
```

Cloudflare Pages build settings:

```text
Root directory: repository root
Build command: npm ci --prefix apps/memory-atlas && npm run build --prefix apps/memory-atlas
Build output directory: apps/memory-atlas/dist
```

Install local macOS launchers:

```bash
python3 scripts/install_memory_atlas_app.py
python3 scripts/audit_memory_atlas_acceptance.py --require-local-apps
python3 scripts/audit_memory_atlas_goal_completion.py --require-local-apps
```

This creates `Memory Atlas.app` in `~/Downloads` and `/Applications`. The app
launcher has a custom galaxy graph icon, installs a source workspace under
`~/Library/Application Support/OpenAIDatabase/MemoryAtlas/source`, prepares a
static local runtime under
`~/Library/Application Support/OpenAIDatabase/MemoryAtlas/runtime`, refreshes
the runtime copy of the redacted visualization snapshot from that Application
Support source workspace, starts a lightweight
local static server on `http://127.0.0.1:4177`, and opens the browser. It is a thin local launcher, not
a Tauri package and not a third-party plugin. First install can take a few
minutes because it builds the runtime. Normal launches do not wait for the Vite
dev server, but they do rebuild the latest redacted source snapshot from the
installed source workspace before serving the page, so the displayed snapshot
generation time is not a stale cached build time. The runtime includes
`memory_atlas_build.json`; if the launcher sees that the cached runtime commit
does not match the installed source commit, it stops the stale local server and
rebuilds the static runtime before opening. `MEMORY_ATLAS_REFRESH=1` now forces
a complete static runtime rebuild as well as the default snapshot refresh. The
launcher opens a small local starting page immediately, then redirects to Memory
Atlas when the latest snapshot has passed release/acceptance audit and the
local server is ready; it does not open a second browser target after the server
starts.
The page reads `memory_atlas.json` with a cache-busting runtime request and
shows both the snapshot generation time and the current page load time. The
local static server writes its PID under
`~/Library/Application Support/OpenAIDatabase/MemoryAtlas/server.pid`; the
browser page sends a same-origin heartbeat while open, and the server exits
when closing tab/page triggers the same-origin release endpoint. The frontend
also clears transient `sessionStorage`, Memory Atlas cache entries, and matching
service-worker registrations during release; local writeback proposal history is
preserved for version control and rollback. `MEMORY_ATLAS_IDLE_SECONDS=45`
remains only as a fallback if page release cannot be delivered, so closing the
page does not leave a stale background process. `MEMORY_ATLAS_TTL_SECONDS=7200`
is still kept as a hard maximum session length; set it to `0` only when you
intentionally want to disable that fallback cap. 关闭 tab 必须释放本地服务并清理临时浏览器缓存。

The normal launcher path no longer reads the `Documents` repository on every
open. It runs from the installed Application Support source workspace, which is
refreshed by rerunning the installer from the trusted main repo:

```bash
cd /Users/linzezhang/Documents/Codex/2026-06-15/files-mentioned-by-the-user-chatgpt/work/CodexProject/OpenAIDatabase
python3 scripts/install_memory_atlas_app.py
```

The launcher log is
`~/Library/Logs/OpenAIDatabase/memory-atlas-launcher.log`.

Local generated folders such as `apps/memory-atlas/node_modules`,
`apps/memory-atlas/dist`, and `*.tsbuildinfo` are ignored and should not be
committed. `memory_atlas.json` is committed as a redacted visualization
snapshot so future agents can run the app without reprocessing raw exports.
The installer removes transient frontend build folders after updating the
runtime cache and now fails if cleanup leaves `node_modules`, `dist`, or
`tsconfig.tsbuildinfo` behind. On macOS the installer also fails if the custom
`.icns` icon cannot be generated; `--require-local-apps` verifies both the icon
file and the runtime commit manifest. Use `audit_memory_atlas_goal_completion.py
--publish-dir ...` before installer cleanup when auditing a deploy artifact, and use
`audit_memory_atlas_goal_completion.py` or
`audit_memory_atlas_goal_completion.py --require-local-apps` after installer
cleanup when auditing cleaned local source/runtime state.

Authorized Cloudflare deployment is intentionally a separate step. Dry-run:

```bash
python3 scripts/deploy_memory_atlas_cloudflare.py
```

Execute only after explicit authorization and live env setup:

```bash
export MEMORY_ATLAS_CLOUDFLARE_AUTHORIZED=I_AUTHORIZE_THIS_DEPLOY
export CLOUDFLARE_ACCOUNT_ID="<account id>"
export CLOUDFLARE_API_TOKEN="<token>"
export MEMORY_ATLAS_ACCESS_HOSTNAME="<hostname>"
export MEMORY_ATLAS_ALLOWED_EMAIL="<email>"

python3 scripts/deploy_memory_atlas_cloudflare.py --execute
```

## Data Layout

```text
skills/openai-memory-analysis/
config/memory_schema.json
data/memory/active/active_memory.jsonl
data/memory/active/active_memory.md
data/memory/curation/core_profile_review.json
data/memory/candidates/*.memory_candidates.jsonl
data/memory/secret_refs/*.secret_refs.jsonl
data/derived/profile/CORE_PROFILE.md
data/derived/weekly/*.weekly_memory_pack.md
data/derived/monthly/*.monthly_memory_pack.md
data/derived/human_reviews/*.human_memory_review.md
data/derived/incremental/*.incremental_change_report.md
data/derived/context_packs/*.md
data/derived/agent_context/AGENT_CONTEXT.md
data/derived/agent_context/agent_context_pack.json
data/derived/chat_reports/*.chat_report.md
data/derived/project_index/PROJECT_INDEX.md
data/derived/decision_log/DECISION_LOG.md
data/derived/timeline/TIMELINE.md
data/derived/visualization/memory_atlas.json
data/processed/conversations/conversation_manifest.jsonl
data/processed/indexes/memory_index.sqlite
apps/memory-atlas/
```

`active_memory.jsonl` stores all three tiers with retrieval weights. Core
profile is high weight, important mid/long-term is medium weight, and general
short-term is low weight. SQLite is a derived read index.

`data/derived/profile/CORE_PROFILE.md` is the quickest personalization entry
for future agents. It is generated from active memory plus
`data/memory/curation/core_profile_review.json`, which records manual review
decisions that keep project-specific workflows out of high-weight core profile.

`data/derived/agent_context/AGENT_CONTEXT.md` and
`data/derived/agent_context/agent_context_pack.json` are the fixed latest entry
points for any new agent. They merge core profile, Codex-derived Memory /
Meta Data recommendations, behavior stats, top topics, safety boundaries, and
read order into a stable Markdown + JSON pack.

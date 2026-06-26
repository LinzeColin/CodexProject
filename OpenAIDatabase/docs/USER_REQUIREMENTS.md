# User Requirements For OpenAI Memory Analysis

This document summarizes the user's durable requirements for the memory database and skill.

## Core Purpose

`LinzeColin/OpenAIDatabase` is the durable memory database for ChatGPT/Codex.

The system must help the user:

- preserve deep, long-range memory across years of interactions
- let any future AI agent understand the user's preferences, standards, project history, and boundaries
- produce human-readable reviews that improve ROI, personal capability growth, opportunity discovery, and execution quality
- process and back up all memory while separating it into core profile, important mid/long-term, and general short-term tiers
- keep durable derived memory and reports backed up in GitHub while avoiding unnecessary local delivery packages and cache buildup

## User-facing Output Requirement

After each processing run, output a chat-ready human review. The user does not want only IDs, hashes, schemas, or agent-internal metadata.

Default delivery is the chat output itself. The GitHub repository is the durable backup surface. Do not create local delivery ZIPs, copied report folders, or extra packages unless explicitly requested. Clean transient package outputs, `.DS_Store`, and Python cache after use; do not delete source exports or encrypted raw archives without explicit authorization.

Every processing run must paste the analysis report, weekly review, and monthly review into the chat. The same chat-facing report should be backed up to `data/derived/chat_reports/`, but files must not replace the chat output.

Use Chinese by default. Keep professional terms, API names, model names, code identifiers, and source titles in English when that is more precise.

The output should explain:

- first: conclusions generated from the processed memory content itself, not from the processing task
- second: comparison with the previous processed conclusions, including new themes, stronger/weaker themes, changed decisions, changed rules, obsolete conclusions, risks, opportunities, and next-action implications
- what topics appeared
- what changed
- what should be remembered
- what should be done next
- what should become core profile, important mid/long-term, or general short-term memory
- what opportunities or development directions emerged
- what repeated problems or capability gaps appeared
- how to maximize ROI and personal growth

After each processing run, include at least two independent review perspectives:

1. 战略/机会视角：新的发展机会、投资机会、业务机会、能力杠杆、ROI 优先级、未来方向。
2. 执行/质量视角：遗漏信息、没有想到的角度、弱证据、冲突、低质量候选、可继续优化的地方。

If true subagents are available, use two separate agents. If not, still produce two independent reviewer passes in the generated reports and chat output.

## Required Incremental Sections

0. 本次资料内容结论：必须根据记忆资料内容包生成，而不是描述本轮处理流程。至少覆盖话题、需要做什么、需要记得做什么、建议做什么、潜在发展/投资/业务机会、个人能力成长信号。
0.1. 本次资料与上一轮结论对比：必须说明相对上一轮新增、增强、减弱、废弃、冲突、机会变化和行动影响。
1. 新增长期记忆、需要更新的旧记忆、新增决策、分析增量变化
2. 已废弃的信息
3. 需要更新进 Codex 和 ChatGPT 的记忆
4. 未来回答应遵守的规则
5. 临时信息和敏感资料备份
6. ROI 最大化建议
7. 个人能力成长建议
8. 潜在发展 / 投资机会

All memory must be processed and backed up. Do not delete, discard, or fail to back up historical memory. Classify every item into:

1. 核心画像: 身份、简历、成长经历、倾向、偏好、Taste、计划、规划、历史等根本信息。
2. 一般: 项目、决策、重要 workflow、中长期约束、机会和可复用上下文。
3. 临时: 短期事件、敏感细节、低确定性上下文、一次性信息；保留脱敏摘要和加密原文引用，默认低权重召回。

The full database flow must also maintain `active_memory`, Project Index, Decision Log, Timeline, weekly/monthly reports, chat report backups, candidates, secret refs, and the SQLite search/fetch index.

## Memory Atlas And Codex Data Visualization

Memory Atlas is one local-first visualization platform, not a third-party
plugin and not multiple separate apps. It must support selectable analysis
sources on the homepage:

1. 总数据源: 所有数据来源放在一起
2. ChatGPT
3. Codex

Selecting a source changes the analyzed dataset only. Galaxy, 数据导图, ROI
Dashboard, Obsidian Graph, Timeline, Contribution Grid, Search/Review, and
Recommendation views must remain synchronized and share the same navigation.

Future platform data must use the shared source registry and canonical event
contract. Planned sources such as 微信、小红书、抖音 stay registry-only until
the homepage selector is explicitly expanded; they must not be shown as empty
selectable homepage options and must not fabricate nodes, activity, memories,
interactions, or behavior signals before real redacted ingestion exists. Future
ingestors should output redacted derived summaries for relationship memory,
taste/profile analysis, attention patterns, opportunity discovery, ROI review,
and agent personalization while keeping raw exports, private full messages,
media, tokens, cookies, sessions, and plaintext high-risk secrets out of GitHub.

The current Codex analysis object is the user's real local Codex data: usage
records, chat/session records, development records, tool-call patterns, error
signals, preference signals, and behavior history. The system should convert
this into agent-usable personalization/profile/preference/context data and
human-usable ROI/growth/action insights.

Memory Atlas must include a Recommendation view with two sections:

1. `Memory（给 ChatGPT / Codex Personalization）`
2. `Meta Data（给 ChatGPT / Codex Agents.md）`

Each section must show added, modified, deleted/demoted, and current items.
Deleted/demoted means "do not continue using this as active personalization";
historical records are still backed up and auditable.

Timeline must be a real dynamic and interactive timeline, not a static scatter
plot, table, or list. It must support real event-date positioning, zoom,
timeline window selection, replay cursor/playback, density track, visible event
density backdrops, hover details, and click-to-sync Inspector. It should help
the user understand sequences, bursts, project phases, decisions, and behavior
change over time.

Frontend writeback must stay proposal-only but be useful enough for controlled
agents to apply later. It must show a readable diff, proposal version chain,
parent proposal id, exportable proposal history, rollback proposal generation,
and pending-agent-apply status. The frontend may request a change, but it must
not directly mutate active long-term memory.

Every project must maintain true model-parameter documentation. "Model" means
assumptions, data inputs, processing method, strategy, outputs, and iteration
policy. "Parameters" means formulas, functions, thresholds, weights, gates,
and numeric values, for example how activity score or emotion score is
computed. If a model such as emotion score is not implemented, the document
must say so directly instead of inventing a formula. Feature lists, development
logs, delivery/run modes, acceptance standards, risks, and history belong in
separate delivery/requirement records, not in the model-parameter section.

The Contribution Grid must support year selection for day/week/month/year
scales. The year selector should only show years with history. Day/week must
share the same yearly coordinate plane: 7 Monday-to-Sunday rows by 52-54 natural
week columns. Day mode selects individual square day cells; week mode selects
one whole natural week column, avoiding ISO-week splits across adjacent columns.
Month/year must share the same 24-column two-year coordinate plane, using the
selected year as the ending year. Month mode selects one vertical month column;
year mode selects one 12-column half-width year block.

The Contribution Grid heat legend must be a rectangular continuous trend bar,
not a row of separate color blocks. It should be shortened to roughly three
day-grid columns and should not include redundant explanatory text. The legend
and heat cells should transition naturally from the interface's default low-heat
cell color to blue, making 0 usage through deep usage visually distinguishable.

Week and year views must preserve lower-level trend detail inside the larger
click target. Week view uses one selectable week column per natural week, with
7 internal day-granularity trend cells. Year view uses one selectable half-width
year block per year, with 12 internal month-granularity trend cells.

## Required Weekly Review

If the current update is at least one week after the prior accepted update, or the user asks for weekly review, output:

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

The action list should be ranked by ROI, confidence, and smallest next action.

The weekly review must be written for the user as a self-improvement, ROI, project, opportunity, and decision review. Do not make it only an agent maintenance checklist.

## Required Monthly Review

If the current update is at least one month after the prior accepted monthly update, or the user asks for monthly review, output:

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

The monthly review must be written for the user as a profile, capability, project portfolio, decision log, opportunity map, and next-direction synthesis. Do not make it only a database maintenance report.

## Finance / Trading Agent Secret Requirement

The user wants finance, trading, and other high-impact agents to be able to use the memory database when they need credential context.

Implementation requirement:

- The database may store `secret_ref` metadata: purpose, intended agent/workflow, risk, approval requirement, local resolver hint, and source reference.
- The database must not upload plaintext high-risk secrets to GitHub.
- Plaintext secrets, broker credentials, API keys, cookies, session tokens, private keys, and `.env` values stay in local secret storage or another explicit secret manager.
- Future finance/trading agents can discover that a credential exists and request authorization, but must fail closed before any real broker, payment, or trading action unless the user explicitly approves the concrete action.

## Safety And Review Rules

- Do not automatically write to ChatGPT Memory.
- Do not automate ChatGPT login or scrape ChatGPT UI.
- Do not commit raw unencrypted exports.
- Do not commit plaintext secrets, even if a downstream agent may need them.
- Do not expose raw sensitive content in chat.
- Generated memory candidates remain pending until human review.
- Active memory must be concise, useful, source-backed, and low-noise.

## Quality Bar

A memory output is good only if it helps the user make better future decisions.

Low-value outputs include:

- long lists of record IDs without human meaning
- leading with processing status instead of conclusions from the memory content
- raw hashes as primary content
- schema dumps
- unranked candidate lists
- failing to back up historical memory at least as redacted summary plus encrypted raw reference
- vague suggestions without next actions

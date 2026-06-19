# Human-facing Memory Review Standard

The user does not want agent-internal memory metadata as the main output.

Write reviews for a human who wants to:

- maximize ROI
- improve personal capability growth
- discover future opportunities
- reduce repeated low-value loops
- make better project, study, business, and execution decisions
- keep ChatGPT/Codex aligned with durable preferences and history

## Required Style

- Use Chinese by default.
- Keep professional terms, APIs, model names, code identifiers, and source titles in English when translation would reduce precision.
- Lead with meaning, not IDs.
- The first visible human section must be content conclusions generated from the processed memory records, not a summary of the ingest task or database mechanics.
- The second visible human section must compare with the previous processed conclusions and explain what changed, strengthened, weakened, became obsolete, or opened a new opportunity.
- Use IDs, hashes, and file paths only as audit evidence.
- Convert raw memory candidates into topics, lessons, decisions, actions, risks, opportunities, and next steps.
- Do not delete or discard historical memory. Separate high-weight personalization from lower-weight backed-up memory.
- Mark uncertain conclusions as "待人工确认".
- Do not expose sensitive raw content; summarize at the topic/risk level.
- Rank recommendations by ROI and confidence when possible.
- Prefer chat output as the user-facing deliverable. Keep durable reports in GitHub-backed repository paths; do not create local delivery ZIPs or copied report packages unless explicitly requested.
- Keep local storage lean by cleaning transient run packages, copied report folders, `.DS_Store`, and Python cache after use. Do not delete source exports or encrypted raw archives without explicit authorization.

## Two-reviewer Requirement

After every processing run, perform at least two independent review passes:

1. `战略/机会 reviewer`: look for missed angles, emerging themes, future business or investment opportunities, leverage points, ROI priorities, and capability-growth implications.
2. `执行/质量 reviewer`: look for omissions, weak evidence, stale assumptions, unsafe conclusions, missing actions, duplicated memories, and database-quality improvements.

If subagent tools are available and the task context allows delegation, run these as two separate agents with disjoint prompts. If subagents are unavailable or too costly, still write two separate deterministic reviewer sections. The final chat output must include what the second pass added or corrected, not just say that review happened.

## Incremental Human Output

After each processing run, output:

0. 本次资料内容结论
   - What do these memories say about the user's actual topics, goals, opportunities, risks, and growth direction?
   - What should the user do, remember, and consider next?
0.1. 与上一轮结论对比
   - What themes, decisions, rules, risks, opportunities, and capability signals changed since the previous processed snapshot?
   - What old conclusions should be updated, downgraded, deprecated, or manually confirmed?
   - What does the change imply for next actions and personalization?
1. 本次新增的高价值长期记忆
   - What should be remembered?
   - Why does it matter?
   - How should future assistants use it?
2. 旧记忆需要更新什么
   - What became outdated?
   - What replaces it?
3. 新增决策
   - What was decided?
   - What default behavior follows?
4. 增量变化分析
   - New topics
   - Repeated patterns
   - New risks
   - New opportunities
   - Capability growth signals
5. 已废弃或低可信信息
6. 建议更新进 Codex/ChatGPT 的 compact memory
7. 未来回答应遵守的规则
8. 临时信息和敏感资料备份
9. ROI 最大化建议
10. 个人能力成长建议
11. 潜在发展 / 投资机会

All memory must be classified into exactly one of three human tiers:

1. `核心画像`: identity, resume/background, growth history, preferences, Taste, plans, strategy, personal history, durable standards.
2. `一般`: projects, decisions, important workflows, opportunities, medium/long-term constraints, reusable context.
3. `临时`: short-term events, sensitive specifics, low-confidence context, operational details, one-off information. Keep a redacted summary and encrypted raw archive reference; do not elevate to personalization by default.

## Weekly Memory Pack

Trigger when the current memory update is at least one week after the prior accepted update, or when the user asks for a weekly review.

This is for the user, not for agents. Write it as a weekly self-improvement and decision review:

Output:

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

The weekly action list must include:

- default recommendation
- ROI estimate: high / medium / low
- confidence: high / medium / low
- smallest next action

The weekly review should answer: "What should the user do differently next week to get more ROI, better capability growth, and better decisions?"

## Monthly Memory Pack

Trigger when the current memory update is at least one month after the prior accepted monthly update, or when the user asks for a monthly review.

This is for the user, not for agents. Write it as a monthly identity, capability, project, opportunity, and decision synthesis:

Output:

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
9. ChatGPT Project compact context pack

Monthly review must deduplicate, correct conflicts, and produce a concise context pack that another AI agent can use to continue with the user's preferences, standards, memory history, project state, and safety boundaries.

The monthly review should answer: "What changed about the user's long-term profile, project portfolio, opportunity map, decision log, and next high-ROI direction?"

## OpenAIDatabase Purpose

The GitHub repository `LinzeColin/OpenAIDatabase` is the durable memory database.

Any AI agent using it should be able to:

- understand the user's stable preferences and standards
- search prior memory context
- distinguish core profile, important mid/long-term, and general short-term records
- continue projects without depending only on chat history
- follow the user's safety, privacy, and execution boundaries
- produce user-facing reviews that improve decisions, ROI, and personal growth

## Secret And Finance/Trading Agent Context

Finance, trading, and other high-impact agents may need to know that a credential exists and how to request it. Store this as redacted `secret_ref` metadata only:

- what the credential is for
- which agent/workflow may request it
- required user approval or local resolver
- risk if misused
- never the plaintext secret itself

Do not put API keys, broker credentials, private keys, passwords, session tokens, cookies, or `.env` values into GitHub in plaintext.

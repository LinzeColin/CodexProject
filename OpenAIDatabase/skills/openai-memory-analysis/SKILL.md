---
name: openai-memory-analysis
description: Analyze ChatGPT/OpenAI data export ZIPs, Codex memory packs, and repo-backed personal memory vaults. Use when Codex needs to build, update, audit, deduplicate, redact, summarize, or retrieve long-term ChatGPT/Codex memories; generate weekly/monthly memory packs; compare incremental memory changes; create human-reviewable memory candidates; or expose a read-only local search/fetch memory layer.
---

# OpenAI Memory Analysis

## Operating Rules

Keep this workflow local-first, deterministic, and review-gated.

- Use Chinese for user-facing output by default, except professional terms, code identifiers, API names, model names, and source titles.
- Do not automate ChatGPT login, ChatGPT UI export, browser profiles, cookies, sessions, or saved-memory writes.
- Do not commit raw OpenAI export ZIPs, unredacted raw messages, credentials, browser state, `.env`, cookies, private keys, or session tokens.
- Do not send raw sensitive export content to a model unless the user explicitly authorizes that exact transfer.
- Treat generated run-local memory candidates as pending until a governed
  writer records the review outcome in the canonical V2 dataset.
- Prefer redacted JSONL/Markdown as the durable surface; SQLite is a local, ignored, rebuildable search index.
- Do not create raw ZIP/tar/bundle copies. Complete private-origin recovery belongs in owner-controlled private Release storage; this skill records only redacted SHA-256-backed references.
- Do not upload plaintext secrets to GitHub. If finance, trading, or other agents need credentials, store only redacted `secret_ref` metadata, intended use, authorization boundary, and local secret-resolver instructions in the memory database.
- Default delivery is chat output plus GitHub-backed repository updates. Do not create local delivery ZIPs or copied report packages unless the user explicitly asks.
- Keep the local machine lean: use temporary run directories for transient files, remove cache/package outputs after use, and keep durable derived memory in the repository for GitHub backup.
- Every processing run must compare the current conclusions with the previous processed snapshot and explain what changed, strengthened, weakened, became obsolete, or became a new opportunity.

## Standard Workflow

1. Inspect inputs with `scripts/openai_memory_analysis.py inspect`.
2. Run a sample pass before a full pass when inputs are large.
3. Run the full pass without creating a second raw archive or bundle.
4. Review generated reports:
   - `incremental_change_report.md`
   - `weekly_memory_pack.md`
   - `monthly_memory_pack.md`
   - `chatgpt_project_context_pack.md`
   - `codex_memory_update_pack.md`
   - `human_memory_review.md`
   - `dual_agent_review.md`
5. Output the human layer in the chat after processing. Link files only as audit backup, not as the main deliverable.
6. Generate `chat_report.md` as the repository backup of the exact chat-facing report, but still paste the report into the chat.
7. Read canonical memory from `data/memory/records/manifest.json`. Candidate,
   active, disputed, and retired records share `config/memory.schema.json`;
   never write the retired legacy memory directories.
8. Maintain `data/derived/profile/CORE_PROFILE.md` as a derived fast-entry view
   of verified canonical `active` records.
9. Maintain `PROJECT_INDEX.md`, `DECISION_LOG.md`, and `TIMELINE.md` so future agents can use the database directly.
10. Commit and push durable derived memory, reports, requirements, and index changes to GitHub when the user wants repository backup.
11. Rebuild/query the read-only retrieval index with `search`, `fetch`, or `serve-mcp`.
12. Clean local transient outputs such as copied report folders, ZIP delivery packages, `.DS_Store`, and `__pycache__` after the run. Do not delete source exports or private Release recovery assets without explicit authorization plus verified replacement.

## Commands

Use the bundled script directly:

```bash
python3 scripts/openai_memory_analysis.py inspect \
  --inputs /path/to/OpenAI-export.zip /path/to/codex-pack.zip \
  --out-dir /path/to/run/inspect

python3 scripts/openai_memory_analysis.py run \
  --inputs /path/to/OpenAI-export.zip /path/to/codex-pack.zip \
  --database-dir /path/to/OpenAIDatabase \
  --out-dir /path/to/run/full

python3 scripts/openai_memory_analysis.py search \
  --database-dir /path/to/OpenAIDatabase \
  --query "Codex workflow" \
  --limit 10

python3 scripts/openai_memory_analysis.py fetch \
  --database-dir /path/to/OpenAIDatabase \
  --id mem_xxx
```

For validation:

```bash
python3 scripts/openai_memory_analysis.py self-test --out-dir /tmp/openai-memory-analysis-self-test
python3 /path/to/skill-creator/scripts/quick_validate.py /path/to/openai-memory-analysis
```

## Output Contract

Every run must produce two layers:

1. **Machine layer**: JSONL/SQLite records for retrieval and audit.
2. **Human layer**: a chat-ready review that helps the user improve ROI, personal capability growth, decision quality, opportunity discovery, and execution focus.

The first visible human section must be **memory-content conclusions** derived from the processed records themselves, not from the processing task. It must answer:

1. 这批记忆资料说明了什么核心主题和长期叙事。
2. 用户需要做什么。
3. 用户需要记得做什么。
4. 建议用户做什么。
5. 有哪些潜在发展、投资、业务、能力成长机会。
6. 哪些内容只适合低权重保留或人工确认。

The second visible human section must be **comparison with the previous processed conclusions**. It must answer:

1. 相对上一轮新增了什么主题、决策、规则、机会或风险。
2. 哪些主题更强、哪些主题变弱或本轮没有继续出现。
3. 哪些旧结论需要更新、降权、废弃或人工确认。
4. 这些变化对用户下一步行动、ROI、个人成长和未来 agent personalization 有什么影响。

Processing status, candidate counts, backup status, indexes, hashes, and validation details must come after the content conclusions.

Every run must also include at least two independent review perspectives:

1. **Strategic reviewer**: find missed opportunities, new development or investment angles, leverage points, ROI priorities, and long-term capability implications.
2. **Execution reviewer**: find omissions, quality issues, stale assumptions, unsafe conclusions, missing follow-up actions, and places where the memory database can be improved.

If real subagent tools are available and authorized, use two separate agents for these review passes. If not, run two separate deterministic reviewer passes and write them into `dual_agent_review.md` and `human_memory_review.md`.

Do not answer the user with only IDs, hashes, schema fields, or agent-internal status. Use IDs and hashes only as supporting evidence or audit handles.

The human layer must translate memory records into:

- Topics discussed.
- What changed.
- What the user should remember.
- What the user should do next.
- What should be core profile, important mid/long-term memory, or general short-term memory.
- Potential opportunities, leverage points, and development directions.
- Risks, constraints, and blind spots.
- Suggested actions ranked by ROI and confidence.
- Two-reviewer findings: new angles, omitted context, better conclusions, and optimization suggestions.

The full-flow durable database must include:

- `data/memory/records/manifest.json` and `records-NNNN.jsonl`: the one
  canonical V2 dataset for candidate, active, disputed, and retired state.
- `data/derived/profile/CORE_PROFILE.md`: compact, human-readable core profile for future agent personalization.
- Run-local candidate output: human-review evidence only; no parallel durable
  candidate store or implicit activation.
- `data/derived/project_index/PROJECT_INDEX.md`: theme/project index.
- `data/derived/decision_log/DECISION_LOG.md`: decisions and default implications.
- `data/derived/timeline/TIMELINE.md`: chronological memory timeline.
- `data/derived/chat_reports/*.chat_report.md`: backup copy of the chat-facing report.
- `data/processed/indexes/memory_index.sqlite`: local read-only search/fetch index, ignored by Git and rebuilt automatically when absent.

The former `data/memory/active/`, `candidates/`, `curation/`, and
`secret_refs/` trees are read-only migration evidence. Do not modify, append,
or dual-write them.

Every memory candidate must include:

- `date`
- `source`
- `category`
- `importance`: `高`, `中`, or `低`
- `validity`: `长期`, `半年`, `项目结束前`, or `临时`
- `confidence`
- `reason`
- `memory_tier`: `核心画像`, `一般`, or `临时`
- `backup_status`

Do not delete, discard, or refuse to back up historical memory just because it is short-term or sensitive. Process every item into one of three tiers:

1. `核心画像`: identity, resume/background, growth history, tendencies, preferences, Taste, plans, strategy, personal history, and durable standards.
2. `一般`: projects, decisions, important workflows, medium/long-term constraints, opportunities, and reusable context.
3. `临时`: short-term events, sensitive specifics, low-confidence context, operational details, and one-off information. Store as a redacted summary plus a private Release recovery reference when one is authorized; do not elevate it to high-weight personalization unless explicitly relevant.

The incremental report must include:

0. 本次资料内容结论：根据记忆资料内容包生成主题、行动、机会、成长信号和注意事项。
1. 新增长期记忆：用自然语言说明“需要记住什么、为什么值得记、会如何影响未来决策”。
2. 需要更新的旧记忆：说明旧认知哪里过时、要改成什么。
3. 新增决策：说明用户做了什么选择、未来执行默认按什么处理。
4. 分析增量变化：说明本次相对上次出现了哪些新主题、新风险、新机会、新偏好或能力成长方向。
5. 已废弃的信息：说明哪些内容不再可靠或不应继续影响决策。
6. 需要更新进 Codex 和 ChatGPT 的记忆：只列用户真正希望未来模型记住的 compact context。
7. 未来回答应遵守的规则：说明未来助手应该怎样协作、怎样避免踩线。
8. 临时信息和敏感资料备份：说明哪些资料只应低权重检索，不提升为核心画像；只记录脱敏结果与经授权的 private Release recovery reference。

The weekly report must include:

0. 本周资料内容结论：说明本周记忆内容对用户 ROI、成长、机会和行动的真实含义。
1. 本周核心事件：给用户看的主题、变化、机会和影响，不要只列记录 ID。
2. 本周重要决策：决策、默认执行策略、影响范围、为什么重要。
3. 本周反复出现的问题：卡点、模式、低 ROI 循环、能力缺口、下次如何避免。
4. 本周新偏好：沟通、学习、研究、工程、交易、安全边界等偏好，以及未来助手应如何适配。
5. 本周项目进展：项目状态、下一阶段、关键风险、最小可执行推进动作。
6. 本周需要 ChatGPT 未来记住的上下文：可直接粘贴到 ChatGPT Project 的 compact context。
7. 本周临时信息和敏感资料备份：说明低权重临时资料如何保留、何时召回、为什么不提升为核心画像。
8. 与旧记忆冲突的地方：新事实如何替换旧事实，对未来判断有什么影响。
9. 下周行动清单：按 ROI 排序，给默认推荐、预估影响、最小下一步。

The monthly report must include:

0. 本月资料内容结论：说明本月记忆内容对用户画像、能力、项目组合、机会地图和下月方向的真实含义。
1. Core Profile Memories：本月确认的核心画像、身份、简历、成长经历、偏好、Taste、计划、规划、历史，以及它们对未来选择的影响。
2. Important Mid/Long-term Memories：项目、决策、长期工作流、机会和稳定约束，按用户价值解释。
3. Temporary Memories：临时资料、敏感资料、低确定性内容的脱敏备份摘要和召回条件。
4. Deprecated/Conflicting Memories：冲突事实、可信来源、建议保留版本、对用户判断的影响。
5. Updated Profile：用户能力、目标、偏好、约束、协作方式的更新。
6. Updated Project Index：项目列表、状态、下一步、风险、机会。
7. Updated Decision Log：本月关键决策、原因、后续影响。
8. Updated Timeline：本月关键事件时间线。
9. 适合上传到 ChatGPT Project 的 compact context pack：短、准、低噪音、可直接用。

When the user asks for chat output after processing, use the human layer first. Include machine metadata only if it helps verification.

## Memory Atlas / Codex Data Sync Output

When the processing target includes Codex or Memory Atlas data:

- Treat Memory Atlas as one merged platform with selectable data-source slices, not separate third-party plugins or separate apps.
- Use the `codex` source slice for real local Codex usage/session/development behavior analysis.
- Only store redacted derived Codex summaries in GitHub; never commit raw Codex transcripts, cookies, sessions, local absolute paths, plaintext secrets, broker credentials, or `.env` values.
- Output and back up two recommendation sections after each run:
  1. `Memory（给 ChatGPT / Codex Personalization）`
  2. `Meta Data（给 ChatGPT / Codex Agents.md）`
- For both sections, clearly mark `新增`, `修改`, `删除/降级`, and `当前有效`.
- `删除/降级` means active personalization should stop using or lower the weight of that item; it does not mean deleting historical memory backup.
- Contribution Grid analysis must support source selection and year selection. Day/week use the selected year; month/year use the selected year as the ending year for a two-year comparison.

## References

- Read `references/schema.md` before changing output fields or database layout.
- Read `references/security-policy.md` before changing redaction, archival, Git, or MCP behavior.
- Read `references/retrieval.md` before changing `search`, `fetch`, or MCP behavior.
- Read `references/human-review.md` before writing chat-facing memory review, weekly review, monthly review, ROI review, or personal growth review.

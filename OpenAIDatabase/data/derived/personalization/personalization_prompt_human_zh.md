# Personalization Prompt 中文人类说明

- schema_version: openai_database.provider_projection.v1
- provider: provider-neutral
- bundle_id: sha256:2ae361e34f27137b48cc74f7d749f73add7598dde98f8cbb966cbe73eb69965f
- canonical_source_hash: sha256:f14ef93c25472711e9200b5b1be005f4015639e7096cbffe3a280db8e1cc1275
- task_id: MA-V12-S12P2
- acceptance_id: ACC-MA-V12-S12P2
- prompt_version: personalization_prompt.v1_2_s12_p2
- generated_at: 2026-07-16T23:07:55Z
- source: OpenAIDatabase redacted derived context
- artifact_contract: Derived / Read-only / Regenerate, do not hand edit
- raw_private_data_included: false
- plaintext_secrets_included: false

## 结论

已生成 ChatGPT、Codex、Claude、other agent 可用的最新 Personalization Prompt；共享 identity 由 `data/derived/personalization/memory_bundle_manifest.json` 证明。

本文件是中文人类说明；每个目标文件都包含 `机器可复制文本` fenced block，可直接复制到对应 agent 的 personalization 或启动上下文。

## 来源报告

- `data/derived/personalization/personalization_export.json`
- `data/derived/behavior_intelligence/events.json`
- `data/derived/behavior_intelligence/clusters.json`
- `data/derived/behavior_intelligence/latent_signals.json`
- `data/derived/behavior_intelligence/self_iteration_suggestions.json`
- `data/derived/behavior_intelligence/decision_debt_ledger.json`
- `data/derived/agent_collaboration/agent_collaboration_quality_report.json`

## 摘要

latest memory:
- OpenAIDatabase 是 durable memory source / GitHub 上的 OpenAIDatabase 应作为任意 agent 可读取的长期记忆、画像、偏好和历史上下文数据库。 / high
- 任意 agent personalization / 所有 agent 访问后都应能生成适配用户的 profile、preference、project context、rules 和 history summary。 / high
- 真实数据优先 / 用户明确要求使用真实 Codex / ChatGPT / GitHub 数据，不接受 mock、伪进度或只给概念演示。 / high
- 默认中文输出 / 用户长期偏好中文输出；代码、API、库名、错误信息和专业术语可保留英文。 / high
- 报告面向人类 ROI 和成长 / 处理记忆或行为数据后，应输出人能直接使用的话题、行动、建议、机会、ROI、能力成长和风险提醒。 / high

behavior:
- 项目：Memory Atlas / 该行为簇基于 90 条带证据引用的事件，主要围绕「项目：Memory Atlas」。来源包含 codex、future_agent，时间覆盖 2026-07，常见任务类型为 design、engineering，语言以 mixed、en 为主。该摘要只描述事件聚合，不做个人状态判断或无证重大结论。
- AI 记忆与 agent 工作流 / 该行为簇基于 49 条带证据引用的事件，主要围绕「AI 记忆与 agent 工作流」。来源包含 chatgpt、codex，时间覆盖 2026-01、2026-03、2026-05、2026-06，常见任务类型为 未标注、engineering、data，语言以 mixed、en、zh 为主。该摘要只描述事件聚合，不做个人状态判断或无证重大结论。
- 经营与管理决策 / 该行为簇基于 26 条带证据引用的事件，主要围绕「经营与管理决策」。来源包含 chatgpt，时间覆盖 2025-11、2025-12、2026-01、2026-02，常见任务类型为 未标注、design，语言以 zh 为主。该摘要只描述事件聚合，不做个人状态判断或无证重大结论。
- 项目：Finance / 该行为簇基于 17 条带证据引用的事件，主要围绕「项目：Finance」。来源包含 chatgpt、codex，时间覆盖 2026-01、2026-06、2026-07，常见任务类型为 未标注、design、automation，语言以 mixed、zh、en 为主。该摘要只描述事件聚合，不做个人状态判断或无证重大结论。
- 项目：KMFA / 该行为簇基于 13 条带证据引用的事件，主要围绕「项目：KMFA」。来源包含 codex、chatgpt，时间覆盖 2026-01、2026-04、2026-07，常见任务类型为 design、未标注、writing，语言以 mixed、zh 为主。该摘要只描述事件聚合，不做个人状态判断或无证重大结论。
- 项目：Notion / 该行为簇基于 12 条带证据引用的事件，主要围绕「项目：Notion」。来源包含 chatgpt、codex，时间覆盖 2026-06、2026-07，常见任务类型为 未标注、design、engineering，语言以 mixed、en 为主。该摘要只描述事件聚合，不做个人状态判断或无证重大结论。
- 产品、设计与可视化 / 该行为簇基于 12 条带证据引用的事件，主要围绕「产品、设计与可视化」。来源包含 chatgpt，时间覆盖 2026-02、2026-06、2026-07，常见任务类型为 design、product，语言以 mixed、zh、en 为主。该摘要只描述事件聚合，不做个人状态判断或无证重大结论。
- 自动化与流程治理 / 该行为簇基于 10 条带证据引用的事件，主要围绕「自动化与流程治理」。来源包含 chatgpt，时间覆盖 2025-12、2026-01、2026-03、2026-06，常见任务类型为 未标注、automation，语言以 zh、mixed 为主。该摘要只描述事件聚合，不做个人状态判断或无证重大结论。

latent:
- 可能存在把「经营与管理决策」固化为可恢复资产的复利空间。 / medium / 只沉淀能被另一 agent 从 GitHub 恢复并运行的最小资产；无法复跑的说明先不扩写。
- 可能存在把「AI 记忆与 agent 工作流、项目：Finance」收束为 dry-run 脚本、validator 或固定运行门禁的复用空间。 / medium / 下一轮只选一个最高分候选，验证是否能用一个 dry-run 命令减少重复操作；若不能，就降级为记录项。
- 可能存在把「经营与管理决策、自动化与流程治理、财务与价值分析」先压缩成单个交付件、验收命令或停止条件的收口空间。 / medium / 下次出现同类主题时，先要求一个可验收文件或命令；若无法定义，就归档为暂不推进候选。
- 可能存在「AI 记忆与 agent 工作流、产品、设计与可视化、经营与管理决策」需要先设质量上限，而不是继续增加细节优化的信号。 / medium / 下一次同类优化前写明质量上限和停止条件；达到上限后只修阻断验收的问题。
- 可能存在「AI 记忆与 agent 工作流、项目：Finance、项目：KMFA」在多来源、多任务之间扩张时，需要更早锁定 run contract 的信号。 / medium / 下一次同类 run 开始前写出非目标列表；若新增需求不在非目标例外内，就进入下一 phase 而非本轮扩张。

self_iteration:
- memory / 下一次交接时可更快恢复 可能存在把「经营与管理决策」固化为可恢复资产的复利空间。，但只有通过复跑证据后才写入长期记忆。 / 可能存在把「经营与管理决策」固化为可恢复资产的复利空间。
- config / 若 下一轮只选一个最高分候选，验证是否能用一个 dry-run 命令减少重复操作；若不能，就降级为记录项。 成立，可减少重复操作；若不成立，proposal 到期后归档。 / 可能存在把「AI 记忆与 agent 工作流、项目：Finance」收束为 dry-run 脚本、validator 或固定运行门禁的复用空间。
- AGENTS / 下一次同类 run 可更早锁定非目标列表，但不会在本 phase 改写 AGENTS。 / 可能存在「AI 记忆与 agent 工作流、项目：Finance、项目：KMFA」在多来源、多任务之间扩张时，需要更早锁定 run contract 的信号。
- style / 人类页面应更短、更可读；若影响验收可追溯性，则不采纳。 / 可能存在「AI 记忆与 agent 工作流、产品、设计与可视化、经营与管理决策」需要先设质量上限，而不是继续增加细节优化的信号。
- personalization / 后续对话可更快形成可验收产物；若没有复用价值，proposal 到期归档。 / 可能存在把「经营与管理决策、自动化与流程治理、财务与价值分析」先压缩成单个交付件、验收命令或停止条件的收口空间。

## 输出文件

- ChatGPT: `data/derived/personalization/chatgpt_personalization.md`
- Codex: `data/derived/personalization/codex_personalization.md`
- Claude: `data/derived/personalization/claude_personalization.md`
- other agent: `data/derived/personalization/other_agent_personalization.md`
- machine: `data/derived/personalization/personalization_export.json`
- bundle manifest: `data/derived/personalization/memory_bundle_manifest.json`

## 机器可复制文本

- ChatGPT: `data/derived/personalization/chatgpt_personalization.md`
- Codex: `data/derived/personalization/codex_personalization.md`
- Claude Code: `data/derived/personalization/claude_personalization.md`
- other agent: `data/derived/personalization/other_agent_personalization.md`

## 边界

- No automatic send。
- No GitHub main upload。
- No remote push。
- No raw mutation。
- No proposal apply execution。
- No S12 P3 ChatGPT deep explore execution。

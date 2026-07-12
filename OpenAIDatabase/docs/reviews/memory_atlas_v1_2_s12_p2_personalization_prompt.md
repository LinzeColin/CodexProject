# Memory Atlas v1.2 S12 P2 Personalization Prompt Review

状态：`phase_s12_p2_personalization_prompt_completed_pending_s12_p3`。

任务 ID：`MA-V12-S12P2`。

验收 ID：`ACC-MA-V12-S12P2`。

Validator：`validate:v1.2-s12-p2`。

Prompt 合同版本：`personalization_prompt.v1_2_s12_p2`。

S12 P2 已生成 ChatGPT、Codex、other agent 可用的 Personalization Prompt。每个目标文件都包含中文人类说明和 `机器可复制文本`，机器 JSON 记录来源报告 freshness、prompt targets、safety boundary 和 prompt output contract。

## Source Reports

- latest memory: `data/derived/personalization/personalization_export.json`
- behavior: `data/derived/behavior_intelligence/events.json`
- behavior: `data/derived/behavior_intelligence/clusters.json`
- latent: `data/derived/behavior_intelligence/latent_signals.json`
- self_iteration: `data/derived/behavior_intelligence/self_iteration_suggestions.json`
- decision debt: `data/derived/behavior_intelligence/decision_debt_ledger.json`
- collaboration: `data/derived/agent_collaboration/agent_collaboration_quality_report.json`

## Outputs

- 中文人类说明：`data/derived/personalization/personalization_prompt_human_zh.md`
- ChatGPT：`data/derived/personalization/chatgpt_personalization.md`
- Codex：`data/derived/personalization/codex_personalization.md`
- other agent：`data/derived/personalization/other_agent_personalization.md`
- machine：`data/derived/personalization/personalization_export.json`

## Acceptance

- `python3 scripts/atlasctl.py generate-personalization-prompt` 可生成 S12 P2 outputs。
- `python3 scripts/atlasctl.py generate-personalization-prompt --dry-run` 保留 no-write/no-send 合同。
- ChatGPT、Codex、other agent 三类 prompt 均包含中文人类说明与机器可复制文本。
- prompt 内容来自 latest memory、behavior、latent、self_iteration 以及协作质量等脱敏派生报告。
- `personalization_export.json` 记录 `source_report_freshness`、`prompts`、`targets`、`safety`。

## Boundaries

- No automatic send。
- No GitHub main upload。
- No remote push。
- No raw mutation。
- No proposal apply execution。
- No S12 P3 ChatGPT deep explore execution。
- 当前下一步是 pending S12 P3。

Machine-readable boundary summary: Memory Atlas v1.2 S12 P2; MA-V12-S12P2; ACC-MA-V12-S12P2; phase_s12_p2_personalization_prompt_completed_pending_s12_p3; validate:v1.2-s12-p2; personalization_prompt.v1_2_s12_p2; ChatGPT; Codex; other agent; 中文人类说明; 机器可复制文本; latest memory; behavior; latent; self_iteration; No automatic send; No GitHub main upload; No remote push; No raw mutation; No proposal apply execution; No S12 P3 ChatGPT deep explore execution; pending S12 P3.

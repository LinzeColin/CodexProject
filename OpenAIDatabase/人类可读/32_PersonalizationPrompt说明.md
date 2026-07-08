# 32 Personalization Prompt 说明

## 结论

S12 P2 已完成 Personalization Prompt。任务 ID 为 `MA-V12-S12P2`，验收 ID 为
`ACC-MA-V12-S12P2`，状态为
`phase_s12_p2_personalization_prompt_completed_pending_s12_p3`，validator 为
`validate:v1.2-s12-p2`，prompt 合同为 `personalization_prompt.v1_2_s12_p2`。

本阶段生成 ChatGPT、Codex、other agent 三类可复制提示词。每类文件都有中文人类说明和
`机器可复制文本`。这些提示词来自 latest memory、behavior、latent、self_iteration、
decision debt 和 agent collaboration 等脱敏派生报告。

## 输出文件

| 目标 | 文件 | 说明 |
|---|---|---|
| 中文人类说明 | `data/derived/personalization/personalization_prompt_human_zh.md` | 汇总来源、目标和边界。 |
| ChatGPT | `data/derived/personalization/chatgpt_personalization.md` | 可复制到 ChatGPT personalization 或新对话启动上下文。 |
| Codex | `data/derived/personalization/codex_personalization.md` | 可复制到 Codex 任务启动上下文。 |
| other agent | `data/derived/personalization/other_agent_personalization.md` | 给后续其他 agent 的通用个性化入口。 |
| machine | `data/derived/personalization/personalization_export.json` | 机器可读 prompt、来源 freshness 和安全边界。 |

## 运行方式

- `python3 scripts/atlasctl.py generate-personalization-prompt`
- `python3 scripts/atlasctl.py generate-personalization-prompt --dry-run`

## 边界

- No automatic send。
- No GitHub main upload。
- No remote push。
- No raw mutation。
- No proposal apply execution。
- No S12 P3 ChatGPT deep explore execution。
- 下一步是 S12 P3。

Machine-readable boundary summary: Memory Atlas v1.2 S12 P2; MA-V12-S12P2; ACC-MA-V12-S12P2; phase_s12_p2_personalization_prompt_completed_pending_s12_p3; validate:v1.2-s12-p2; personalization_prompt.v1_2_s12_p2; ChatGPT; Codex; other agent; 中文人类说明; 机器可复制文本; latest memory; behavior; latent; self_iteration; S12 P3; No GitHub main upload; No remote push; No raw mutation; No proposal apply execution.

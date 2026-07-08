# 33 ChatGPT 深度探索说明

S12 P3 已完成 ChatGPT 深度探索入口。任务 ID 为 `MA-V12-S12P3`，验收 ID 为
`ACC-MA-V12-S12P3`，状态为
`phase_s12_p3_chatgpt_deep_explore_completed_pending_s12_review`，validator 为
`validate:v1.2-s12-p3`，合同为 `chatgpt_deep_explore.v1_2_s12_p3`。

本阶段只完成用户触发的 ChatGPT 深度探索入口。默认模式是 `prefill_only`：生成最新记忆
分析报告和深度探索提示，并构造 ChatGPT 预填充 URL。`auto_submit` 是配置受控模式，必须
同时满足配置和显式确认；默认不发送。

## 产物

| 产物 | 路径 | 用途 |
|---|---|---|
| Prompt payload | `data/derived/chatgpt_deep_explore/latest_memory_analysis_prompt.md` | 机器可复制文本和探索提示。 |
| Machine export | `data/derived/chatgpt_deep_explore/chatgpt_deep_explore_export.json` | launch URL、source freshness 和安全边界。 |
| Gate config | `机器治理/运行门禁/chatgpt_deep_explore.v1_2_s12_p3.json` | prefill_only / auto_submit 配置门禁。 |
| atlasctl | `scripts/atlasctl.py chatgpt-deep-explore` | 用户触发的 dry-run、生成和 open 命令。 |

## 用户触发命令

- `python3 scripts/atlasctl.py chatgpt-deep-explore --mode prefill_only --dry-run`
- `python3 scripts/atlasctl.py chatgpt-deep-explore --mode prefill_only`
- `python3 scripts/atlasctl.py chatgpt-deep-explore --mode prefill_only --open`

## 边界

- 用户触发。
- `prefill_only` 默认只填入。
- `auto_submit` 必须显式配置和确认。
- No silent send。
- No cookie/token/secret export。
- No GitHub main upload。
- No remote push。
- No raw mutation。
- No proposal apply execution。
- 下一步是 pending S12 Review。

Machine-readable boundary summary: Memory Atlas v1.2 S12 P3; MA-V12-S12P3; ACC-MA-V12-S12P3; phase_s12_p3_chatgpt_deep_explore_completed_pending_s12_review; validate:v1.2-s12-p3; chatgpt_deep_explore.v1_2_s12_p3; ChatGPT 深度探索; prefill_only; auto_submit; 用户触发; No silent send; No cookie/token/secret export; No GitHub main upload; No remote push; No raw mutation; No proposal apply execution; pending S12 Review.

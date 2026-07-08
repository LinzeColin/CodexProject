# 31 Command Palette 命令面板说明

## 结论

S12 P1 已完成命令面板。任务 ID 为 `MA-V12-S12P1`，验收 ID 为
`ACC-MA-V12-S12P1`，状态为
`phase_s12_p1_command_palette_completed_pending_s12_p2`，validator 为
`validate:v1.2-s12-p1`，运行合同为 `command_palette.v1_2_s12_p1`。

本阶段只完成低负担命令入口，不完成 S12 P2 的完整 personalization prompt 产物，
不完成 S12 P3 的 ChatGPT deep explore 发送或跳转自动化。

## 可用命令

| 命令 | command_id | 用途 |
|---|---|---|
| 同步 ChatGPT | `sync_chatgpt` | 用户触发后查看 ChatGPT 同步 dry-run 命令。 |
| 同步 Codex | `sync_codex` | 用户触发后查看 Codex 同步 dry-run 命令。 |
| 生成本周报告 | `generate_weekly_report` | 用户触发后进入 summary 视图，查看周报生成入口。 |
| 查看待授权 proposal | `view_pending_proposals` | 用户触发后进入 summary 视图，只查看 proposal，不执行 apply。 |
| 生成 personalization prompt | `generate_personalization_prompt` | 用户触发后查看 ChatGPT、Codex、other agent 可用 prompt 的 dry-run 合同。 |

## 安全边界

- No automatic send。
- No GitHub main upload。
- No remote push。
- No raw mutation。
- No proposal apply execution。
- No cookie、token、secret 输出。
- 下一步是 S12 P2。

## 运行与验证

- `python3 scripts/atlasctl.py generate-personalization-prompt --dry-run`
- `pnpm --dir apps/memory-atlas run validate:v1.2-s12-p1`

Machine-readable boundary summary: Memory Atlas v1.2 S12 P1; MA-V12-S12P1; ACC-MA-V12-S12P1; phase_s12_p1_command_palette_completed_pending_s12_p2; validate:v1.2-s12-p1; command_palette.v1_2_s12_p1; 同步 ChatGPT; 同步 Codex; 生成本周报告; 查看待授权 proposal; 生成 personalization prompt; generate_personalization_prompt; ChatGPT; Codex; other agent; No automatic send; No GitHub main upload; No remote push; No raw mutation; No proposal apply execution; S12 P2.

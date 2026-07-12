# Codex与FutureAgent同步

任务 ID：`MA-V12-S04P2`。

验收 ID：`ACC-MA-V12-S04P2`。

状态：`phase_s04_p2_codex_agent_sync_completed_pending_s04_p3`。

## 结论

S04 P2 已建立 Codex local sync 和 future-agent minimal adapter 的最小可运行入口。
本阶段把每个来源的输出合同固定为 raw + derived + run log：

- Codex local sync：`scripts/sync_codex_memory_data.py` 可读取本地 Codex session，生成
  `data/public_raw/codex/` 下的 append-only public raw snapshot，并同步 derived summary
  到 `data/derived/codex/codex_activity_snapshot.json`，run log 写入 `data/run_logs/sync_runs/`。
- future-agent minimal adapter：`scripts/sync_future_agent_data.py` 可接收人工提供的本地 JSON，
  输出 `data/public_raw/agents/{agent_id}/`、`data/derived/agents/{agent_id}/agent_sync_summary.json`
  和 `data/run_logs/sync_runs/`。

## 可运行入口

- `python scripts/atlasctl.py sync --source codex --dry-run`
- `python scripts/atlasctl.py sync --source future-agent --dry-run`
- `python scripts/atlasctl.py build-atlas --dry-run`

dry-run 只返回合同，不写文件。apply 模式必须有真实本地输入；future-agent 没有输入时不能生成伪数据。

## 安全边界

- credential is not memory；cookie、session token、password、API key、private key、OAuth token 不进入 public raw。
- Codex public raw 只保存 redacted summary，不提交原始本地 transcript。
- future-agent adapter 只接受本地人工提供输入，不自动登录、不抓取外部平台。
- raw public 输出使用 append-only；已存在不同内容时失败。

## 本阶段不做

- 不实现 GitHub backup；那是 S04 P3。
- 不 push GitHub main。
- 不读取或保存任何密码/验证码。
- 不修改 ChatGPT 会话状态。

下一步是 S04 P3。

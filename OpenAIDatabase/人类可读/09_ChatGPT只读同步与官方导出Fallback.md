# ChatGPT只读同步与官方导出Fallback

任务 ID：`MA-V12-S04P1`。

验收 ID：`ACC-MA-V12-S04P1`。

状态：`phase_s04_p1_chatgpt_sync_completed_pending_s04_p2`。

## 结论

S04 P1 已建立 ChatGPT 只读同步的最小可运行入口。当前实现不尝试登录、不读取密码、
不保存 cookie 或 session token，也不会发送消息/删除/归档/重命名会话。
浏览器 connector 的硬边界是不得发送消息/删除/归档/重命名会话。

浏览器 connector 在本阶段是只读 contract：只能读取已登录状态下的 conversation title、
conversation content 和 metadata；一旦遇到密码/验证码立即停止。

可执行 fallback 是 official export ZIP/conversations.json fallback。`scripts/sync_chatgpt_memory_data.py`
可以解析官方导出的 `conversations.json` 或 ZIP，在 dry-run 下只统计不写文件，在 apply
模式下写入 `data/public_raw/chatgpt/`、`data/derived/chatgpt/chatgpt_sync_summary.json`
和 `data/run_logs/sync_runs/`。

## 使用边界

- `python scripts/atlasctl.py sync --source chatgpt --dry-run` 只返回可运行合同，不写文件。
- `python scripts/sync_chatgpt_memory_data.py --official-export <path> --dry-run` 验证导出文件可解析，不写文件。
- apply 模式必须提供 official export；没有输入时不能生成伪数据。
- 任何 credential pattern 会先失败，不进入 public raw。
- 已存在 public raw 文件不允许被覆盖。

## 本阶段不做

- 不实现 Codex local sync；那是 S04 P2。
- 不实现后续 agent adapter；那是 S04 P2。
- 不实现 GitHub backup dry-run/apply；那是 S04 P3。
- No GitHub main upload in this phase。

下一步是 S04 P2。

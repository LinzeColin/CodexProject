# Webhook Bridge Design

D2 是未来的 fully automatic entry point。当前任务只记录设计，不部署。

## Target Shape

Owner 在 ChatGPT 或其他工具中批准 dual-plane Task Pack 后，外部 bridge 接收
该 Task Pack，并触发 GitHub `repository_dispatch`：

```text
ChatGPT / connector / form
-> webhook bridge
-> GitHub repository_dispatch: agent_loop_taskpack
-> Agent Loop workflow
```

## Cloudflare Workers

Cloudflare Workers 可以作为个人自动化 bridge。小规模个人用量通常 Free plan
即可；本设计不要求付费订阅。

Worker 责任：

- 接收已批准 Task Pack。
- 校验共享 secret 或等价签名。
- 校验 body 包含 `AGENT_LOOP_METADATA`。
- 调用 GitHub `repos/LinzeColin/CodexProject/dispatches`。
- event type 固定为 `agent_loop_taskpack`。

Worker 禁止：

- 不在 repo 中存储 secret。
- 不重新生成 Task Pack。
- 不用 LLM 从 issue 或聊天文本推断需求。
- 不部署生产业务系统。
- 不记录 API key 或 Task Pack 中可能的敏感内容到公开日志。

## Security Notes

- GitHub token 必须存放在 bridge 平台 secret 中，不能提交到仓库。
- Shared secret 必须由 bridge 校验，失败直接拒绝。
- Bridge 只做转发和最小格式校验，事实源仍是 Owner 批准的 Task Pack。

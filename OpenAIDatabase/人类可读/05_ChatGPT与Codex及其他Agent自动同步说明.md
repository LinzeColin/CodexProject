# ChatGPT 与 Codex 及其他 Agent 自动同步说明

## 当前结论

本页是 Memory Atlas v1.2 S02 P3 的人类同步说明。

- task: `MA-V12-S02P3`
- acceptance: `ACC-MA-V12-S02P3`
- status: `phase_s02_p3_human_sync_explanation_completed_pending_s02_review`
- registry: `机器治理/同步与备份/sync_source_registry.json`
- next: pending S02 Review

本页不是 connector 实现，不会读取浏览器、不会写 raw archive、不会上传 GitHub main。
它只解释 ChatGPT、Codex、后续其他 agent 数据备份进 GitHub 的范围、边界和接入规则。

## 同步范围

1. ChatGPT
   - 使用 source registry 中的 `chatgpt` source。
   - 同步策略是 ChatGPT browser connector + official export fallback。
   - browser connector 的边界是只读 conversation/title/metadata，不抓取密码、cookie、session token。
   - official export fallback 用于浏览器只读同步不可用时的人工导出导入路径。

2. Codex
   - 使用 source registry 中的 `codex` source。
   - 同步策略是 Codex local sync。
   - 范围是本地 Codex session transcripts、消息文本、工具摘要和必要 metadata。
   - 不采集 tokens、API keys、env secrets、本机临时缓存或本地 app 私有状态。

3. 后续其他 agent
   - 使用 source registry 中的 `future_agent_template`。
   - source_type 必须是 `other_agent`，connector_type 必须是 `future_agent_adapter`。
   - 允许能力可来自 local_file、browser_readonly、api 或 manual_import。
   - 新 agent 必须先注册为 source，再进入后续 raw/manifest/derived/report 流程。

## 哪些数据会进入 GitHub

进入 GitHub 的前提是用户授权、source registry 通过、后续 raw append-only gate 通过。
S02 P3 本身不写 raw，只说明未来会进入 GitHub 的类别：

| Source | GitHub raw root | 可公开内容 |
|---|---|---|
| ChatGPT | `data/public_raw/chatgpt` | conversation_title、conversation_content、message_text、timestamp、speaker_role、metadata、tool_call_summary、attachment_reference |
| Codex | `data/public_raw/codex` | conversation_title、conversation_content、message_text、timestamp、speaker_role、metadata、tool_call_summary、attachment_reference |
| other_agent | `data/public_raw/agents/{agent_id}` | 与 transcript 等价的消息、标题、时间、角色、metadata、工具摘要和附件引用 |

所有 source 的 `public_backup_mode` 必须是 `plaintext_public`。这表示用户授权后的 transcript
可以明文公开进入 GitHub，但不表示凭证、密钥或账户控制信息可以进入 GitHub。

后续阶段会把 raw manifest、hash、derived data 和 reports 接入 GitHub 备份链路；S02 P3 不创建这些运行产物。

## transcript/credential 边界

规则是 `transcript/credential` 分离，credential boundary 是 `credentials_not_transcript`。

永远不能提交：

- cookies
- session tokens
- passwords
- API keys
- private keys
- OAuth tokens
- browser_credential_store
- 本机登录态、验证码、浏览器凭证库、env secrets

这些内容不是 agent 数据源内容。任何同步、导出、导入、GitHub backup 或 deep explore payload
一旦包含这些内容，都必须 fail closed。

## 后续 agent 如何接入

后续 agent 不能绕过 source registry。接入步骤：

1. 在 `sync_source_registry.json` 中按 `future_agent_template` 新增 source。
2. 填写 `source_id`、`source_type`、`agent_name`、`raw_root`、`sync_mode`、
   `public_backup_mode`、`connector_capability`。
3. 保持 source_type 为 `other_agent`，并保留 transcript_boundary 与 credential_boundary。
4. allowed action 可以包含 `register_source`；forbidden action 必须包含 `capture_credentials`。
5. 通过 S02/S03/S04 的 validator、credential gate、raw append-only gate 后，才能进入 GitHub 备份链路。

## 本 phase 边界

- No GitHub main upload in this phase.
- No connector implementation.
- No raw archive change.
- No app reinstall.
- 不进入 S02 Review；下一轮才能做 S02 Review。
- 不实现自动登录、自动发送、删除、归档、重命名 ChatGPT 会话。
- 不要求 Codex 获取或保存密码、验证码、cookie、session token。

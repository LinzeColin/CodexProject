# Agent Loop 自动化说明

## 三种入口

Agent Loop 支持三种 Task Pack ingestion mode。三种入口都会先把批准的
dual-plane Task Pack 写入 raw 文件：

```text
/tmp/agent_loop/taskpack.raw.md
```

然后通过 routing/autofill 层生成 normalized 文件：

```text
/tmp/agent_loop/taskpack.md
```

后续 Codex plan、implementation、validation、review、autofix、merge policy
都只读取 normalized 文件。

| 入口 | 触发方式 | Task Pack 来源 | Audit issue |
|---|---|---|---|
| Manual fallback | `workflow_dispatch` | `taskpack` input | workflow 创建 |
| C2 Issue automation | `issues` opened/edited/labeled | issue body | 触发 issue 本身 |
| D1/Future integration | `repository_dispatch` `agent_loop_taskpack` | `client_payload.taskpack` | workflow 创建 |

## 不是 Planner Agent

GitHub Actions 只消费 Owner 已批准的 Task Pack：

- 不运行 Planner Agent。
- 不从 issue 文本重新生成 Task Pack。
- 不让 LLM 从模糊 issue 推断需求。
- 不要求 Custom GPT Action。
- 不要求 GitHub Developer settings。
- 不要求 PAT。
- 不在 plan 与 implementation 之间等待 Owner 审批。

## Trigger Rules

`workflow_dispatch`:

- `taskpack` input 必须包含 `AGENT_LOOP_METADATA`。
- Workflow 创建新的 audit issue。

`issues` opened/edited/labeled:

- Issue body 必须包含 `AGENT_LOOP_METADATA`。
- Issue 必须有 `source:chatgpt-approved`。
- Issue 必须有 `agent:run`。
- Issue 不得已有 `agent:running`、`agent:done`、`agent:blocked`。
- Metadata 中 `source` 必须是 `chatgpt-approved`。
- 这个 issue 本身就是 audit issue。
- Workflow 开始时添加 `agent:running`。
- 成功时移除 `agent:running`、添加 `agent:done`、关闭 issue。
- 失败时移除 `agent:running`、添加 `agent:blocked`、评论失败摘要。

`repository_dispatch`:

- Event type 必须是 `agent_loop_taskpack`。
- `client_payload.taskpack` 必须包含 `AGENT_LOOP_METADATA`。
- 可选 payload 字段 `title`、`risk_tier`、`source` 只能作为审计提示；
  workflow 真实路由仍以 Task Pack metadata 为准。
- Workflow 创建新的 audit issue。

## Task Pack 是事实源

Audit issue 只用于追踪和审计。若 Task Pack 与 issue 评论、payload title、
payload risk tier 或 workflow 输入说明冲突，以 `/tmp/agent_loop/taskpack.md`
中的 Task Pack 为准。

Workflow 不猜项目。路由字段必须来自 metadata：

- `project`
- `allowed_paths`
- `forbidden_paths`
- `risk_tier`
- `plan_required`
- `validation_commands`

如果 `project` 缺失、为空、占位或同时指向多个项目，Task Pack validation 必须失败。

## Routing / Autofill

Owner 不需要记忆每个项目的 `allowed_paths` 和 `forbidden_paths`。

- 路由事实源是 `PROJECT_ROUTING_MATRIX.md` 的
  `AGENT_LOOP_ROUTING_MATRIX_JSON` block。
- `route_taskpack.py` 判断 project 是否唯一。
- `autofill_taskpack_metadata.py` 只补全缺失的 routing metadata。
- 如果路由模糊、多项目、或缺少可运行 validation command，workflow 标记
  `agent:blocked` 并评论候选项目和缺失字段。
- 该层不生成需求、不运行 Planner Agent、不把 T2 降为 T1。

## C2/C3/D1 使用方式

- C2: Owner 创建 issue，把完整 Task Pack 放在 issue body，并带上
  `source:chatgpt-approved` 与 `agent:run`。Workflow 自动运行。
- C3: Owner 使用 `.github/ISSUE_TEMPLATE/codex-task.yml`。表单只有一个大
  textarea，不要求手选 project 或 risk；这些字段必须来自 metadata。
- D1: 可选本地工具。Owner 不需要默认运行脚本；C2/C3 是默认入口。
- D2 future: 可由 Cloudflare Workers 或类似 webhook bridge 转发已批准的
  Task Pack 到 `repository_dispatch`。本阶段不实现。
- D3 future: 可由 ChatGPT connector、MCP 或外部 action 直接提交已批准的
  Task Pack。当前不依赖。

## T1 和 T2

| Tier | 含义 | Owner approval | Plan-first | Auto-merge |
|---|---|---|---|---|
| T1 | 旧 T1/T2，低/中风险任务 | 不需要 | 按 Task Pack 要求 | gates 通过后允许 |
| T2 | 旧 T3/T4，高/关键风险任务 | 不需要 | 必须 | gates 通过后允许 |

T2 的 plan-first 是自动化质量门，不是人工审批门。Plan 必须列出读取文件、
拟修改文件、验证命令、rollback、stop conditions，并且 plan 阶段不得修改仓库。

## 阻断合并的条件

- Task Pack 缺失或 metadata 无效。
- `source` 不是 `chatgpt-approved`。
- `repository` 不是 `LinzeColin/CodexProject`。
- `project` 缺失或不明确。
- `auto_merge` 不是 `true`。
- T2 没有 `plan_required: true`。
- plan 阶段产生文件改动。
- 变更文件超出 `allowed_paths`。
- 触碰 `forbidden_paths`。
- 检测到 secrets、env 文件或未授权依赖变更。
- validation commands 失败。
- Codex review 或 Architect Review 发现未解决 P0/P1。
- 生产部署被尝试执行。
- `BLOCK_MERGE=true`。

## 日志位置

- Workflow run summary: GitHub Actions run 页面。
- Audit issue: workflow 自动创建或复用，并评论 plan、validation、review、merge 结果。
- Artifacts: plan、result pack、review、architect review、validation summary。
- PR: 自动创建的实现 PR。

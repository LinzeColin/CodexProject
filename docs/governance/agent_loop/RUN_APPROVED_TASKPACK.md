# 运行已批准 Task Pack

## 入口 1: workflow_dispatch 手动粘贴

1. 在 ChatGPT 中讨论需求。
2. 要求 ChatGPT 输出 dual-plane Task Pack。
3. Owner 检查 machine plane 和 human plane。
4. 明确授权这份 Task Pack。
5. 打开 GitHub Actions。
6. 选择 `Agent Loop - Run Approved Task Pack`。
7. 点击 `Run workflow`。
8. 把完整 Task Pack 粘贴到 `taskpack`。
9. 如只想校验和生成计划，设置 `dry_run=true`。
10. 启动 workflow。

## 入口 2: C2 Issue-triggered Task Pack

1. 创建 issue，或使用 `Codex Task Pack` Issue Form。
2. 把完整 dual-plane Task Pack 放在 issue body。
3. 可信 issue 作者不需要手动添加 labels。
4. Workflow 触发后使用这个 issue 作为 audit issue。

触发条件：

- Issue body 必须包含 `AGENT_LOOP_METADATA`。
- Metadata 中 `source` 必须是 `chatgpt-approved`。
- Issue 作者必须是 repository owner、member 或 collaborator。
- Issue 不得有 `agent:running`、`agent:done`、`agent:blocked`。

状态标签：

- 开始时自动创建缺失 labels，并添加 `source:chatgpt-approved`、`agent:run`、
  `agent:running` 和 `risk:T1/T2`。
- 成功时移除 `agent:running`，添加 `agent:done`，并关闭 issue。
- 失败时移除 `agent:running`，添加 `agent:blocked`，并评论失败摘要。

## 入口 3: C3 Issue Form / prefilled issue

推荐 Owner 默认使用 GitHub 的 `Codex Task Pack` Issue Form。表单只有一个大文本框：

- 粘贴完整 Task Pack。
- 不需要手选 project。
- 不需要手选 risk tier。
- Issue Form 声明了 `source:chatgpt-approved` 和 `agent:run` convenience
  labels，但 workflow 不依赖它们预先存在。

也可以生成预填 issue URL：

```bash
python3 scripts/agent_loop/build_prefilled_issue_url.py \
  --taskpack path/to/taskpack.md \
  --repo LinzeColin/CodexProject
```

如果 URL 太长，直接使用普通 issue 表单粘贴 Task Pack；D1 只是可选本地工具。

旧 issue 重新触发：部署修复后，编辑 issue body，例如添加
`<!-- rerun: after-c3-opened-trigger-fix -->`，即可触发 `issues: edited`。
如果路由仍然模糊，预期结果是 issue 变成 `agent:blocked`，不会创建 PR、
不会 merge、不会部署生产。

## 入口 4: D1 local gh submitter

本地脚本使用已有 `gh` 登录，不要求 PAT、不保存 token。它不是 Owner 默认路径；
默认路径仍然是 C2 issue 或 C3 Issue Form。

```bash
python3 scripts/agent_loop/submit_taskpack.py \
  --taskpack path/to/taskpack.md \
  --mode issue \
  --repo LinzeColin/CodexProject
```

可选模式：

- `--mode issue`: 创建 Task Pack issue，并按顺序添加触发标签。
- `--mode dispatch`: 发送 `repository_dispatch`。
- `--mode workflow`: 触发 `workflow_dispatch` 兜底入口。
- `--dry-run-local`: 只做本地校验和打印动作，不调用 GitHub。

## 入口 5: repository_dispatch

用于未来 ChatGPT/connector/webhook 集成。Event type 必须是：

```text
agent_loop_taskpack
```

Payload:

```json
{
  "taskpack": "完整 dual-plane Task Pack",
  "title": "可选标题",
  "risk_tier": "T1 或 T2，可选提示",
  "source": "chatgpt-approved"
}
```

Workflow 会从 payload 创建新的 audit issue。真实项目路由仍以 Task Pack
metadata 为准。

D2 webhook bridge 可以使用 Cloudflare Workers 或类似服务转发已批准 Task
Pack，但当前 bootstrap hardening 不实现该桥。详见
`docs/governance/agent_loop/WEBHOOK_BRIDGE_DESIGN.md`。D3 direct ChatGPT
connector、MCP 或 external action 也是未来入口，不是当前依赖。

## dry_run

`dry_run=true` 只适用于 `workflow_dispatch`，执行：

- Task Pack validation。
- Audit issue creation。
- Codex plan。
- Plan validation。
- Plan artifact upload。
- Audit issue plan comment。

它不会实现、不会创建 PR、不会合并。

## 结果阅读

成功时：

- Audit issue 会记录 final result。
- PR 会被 squash merge。
- 工作分支会被删除。
- Audit issue 会关闭。

失败时：

- Audit issue 会显示失败阶段。
- Workflow summary 会记录 `BLOCK_MERGE` 或具体失败原因。
- Artifacts 中保留 plan、validation、review 或 autofix 结果。

## BLOCK_MERGE 出现时

Owner 应先读取 audit issue 和 workflow summary。常见处理方式：

- 修正 Task Pack allowed/forbidden paths 后重新运行。
- 明确添加缺失 validation commands。
- 缩小任务范围。
- 把 production deploy 从当前 Task Pack 中拆出去。
- 对无法自动修复的 P0/P1 问题，另开新的 Task Pack。

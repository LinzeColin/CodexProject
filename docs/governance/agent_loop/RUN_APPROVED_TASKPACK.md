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

## 入口 2: issues:labeled

1. 创建 issue。
2. 把完整 dual-plane Task Pack 放在 issue body。
3. 给 issue 添加 `source:chatgpt-approved`。
4. 给 issue 添加 `agent:run`。
5. Workflow 触发后使用这个 issue 作为 audit issue。

触发条件：

- 新增标签必须是 `agent:run`。
- Issue body 必须包含 `AGENT_LOOP_METADATA`。
- Issue 必须有 `source:chatgpt-approved`。
- Metadata 中 `source` 必须是 `chatgpt-approved`。

## 入口 3: repository_dispatch

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

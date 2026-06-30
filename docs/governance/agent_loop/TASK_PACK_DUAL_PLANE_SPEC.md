# Dual-Plane Task Pack Spec

Task Pack 必须同时包含 machine-readable contract 和 human-readable
Markdown。Machine plane 供 workflow 严格校验；human plane 供 Owner 和
review 读取。

## Plane A: Machine-Readable Contract

必须使用以下 HTML 注释 wrapper：

```text
<!-- AGENT_LOOP_METADATA
{
  "agent_loop_version": "1.0",
  "source": "chatgpt-approved",
  "repository": "LinzeColin/CodexProject",
  "risk_tier": "T1",
  "auto_merge": true,
  "plan_required": false,
  "production_deploy": false,
  "project": "agent-loop",
  "roadmap_task_id": "AGENT-LOOP-T01",
  "acceptance_id": "AGENT-LOOP-A01",
  "allowed_paths": ["docs/governance/agent_loop/**"],
  "forbidden_paths": ["AGENTS.md", "Alpha/**"],
  "validation_commands": ["python3 scripts/agent_loop/validate_taskpack.py --taskpack taskpack.md"],
  "max_autofix_loops": 1
}
END_AGENT_LOOP_METADATA -->
```

JSON 必须能用 Python 标准库 `json` 解析。不得包含注释、尾逗号或
YAML-only 语法。

## 必填字段

| Key | 要求 |
|---|---|
| `agent_loop_version` | 非空字符串 |
| `source` | 必须是 `chatgpt-approved` |
| `repository` | 必须是 `LinzeColin/CodexProject` |
| `risk_tier` | `T1` 或 `T2` |
| `auto_merge` | 必须是 `true` |
| `plan_required` | T2 必须是 `true` |
| `production_deploy` | 默认并应保持 `false` |
| `project` | 当前项目或治理域；必须明确，不能是 `unknown`、`TBD`、`multiple` 等占位 |
| `roadmap_task_id` | 当前任务 ID |
| `acceptance_id` | 当前验收 ID |
| `allowed_paths` | 非空列表 |
| `forbidden_paths` | 非空列表 |
| `validation_commands` | 命令列表，或 human plane 给出明确 N/A 理由 |
| `max_autofix_loops` | 非负整数 |

## Plane B: Human-Readable Markdown

必须包含以下 section heading：

- `## Human Summary`
- `## Background`
- `## Scope`
- `## Files To Inspect`
- `## Files Allowed To Modify`
- `## Files Forbidden`
- `## Implementation Requirements`
- `## Acceptance Criteria`
- `## Validation Tests`
- `## Stop Conditions`
- `## Review Requirements`
- `## Rollback Plan`
- `## Required Codex Result Pack`

## Ingestion Modes

同一个 Task Pack 可以通过三种方式进入 workflow：

- `workflow_dispatch`: 粘贴到 `taskpack` 输入。
- `issues:labeled`: issue body 就是 Task Pack，标签为 `agent:run` 且已有
  `source:chatgpt-approved`。
- `repository_dispatch`: event type 为 `agent_loop_taskpack`，payload 中
  `taskpack` 字段就是 Task Pack。

三种入口都会归一化为：

```text
/tmp/agent_loop/taskpack.md
```

后续所有自动化只读取这个文件。

## T1 示例

```text
<!-- AGENT_LOOP_METADATA
{"agent_loop_version":"1.0","source":"chatgpt-approved","repository":"LinzeColin/CodexProject","risk_tier":"T1","auto_merge":true,"plan_required":false,"production_deploy":false,"project":"docs","roadmap_task_id":"DOC-T01","acceptance_id":"DOC-A01","allowed_paths":["docs/governance/agent_loop/**"],"forbidden_paths":["AGENTS.md","Alpha/**","EEI/**"],"validation_commands":["python3 scripts/agent_loop/validate_taskpack.py --taskpack taskpack.md"],"max_autofix_loops":1}
END_AGENT_LOOP_METADATA -->
```

## T2 示例

```text
<!-- AGENT_LOOP_METADATA
{"agent_loop_version":"1.0","source":"chatgpt-approved","repository":"LinzeColin/CodexProject","risk_tier":"T2","auto_merge":true,"plan_required":true,"production_deploy":false,"project":"governance","roadmap_task_id":"GOV-T02","acceptance_id":"GOV-A02","allowed_paths":["docs/governance/**","scripts/agent_loop/**"],"forbidden_paths":["AGENTS.md","Alpha/**","EEI/**","PFI/**"],"validation_commands":["python3 scripts/agent_loop/validate_plan.py --plan codex-plan.md --taskpack taskpack.md"],"max_autofix_loops":2}
END_AGENT_LOOP_METADATA -->
```

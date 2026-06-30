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

Human plane 可以是中文、英文或中英双语。Owner 不需要记住精确英文标题；
validator 会把等价的中文/英文/编号式 `##` headings 映射到同一组 canonical
sections。

必须覆盖以下 canonical sections：

| Canonical section | Accepted heading examples |
|---|---|
| `human_summary` | `## Human Summary`, `## 1. 人类摘要`, `## 摘要` |
| `background` | `## Background`, `## 2. 背景`, `## 上下文` |
| `scope` | `## Scope`, `## 3. 范围`, `## 任务范围` |
| `files_to_inspect` | `## Files To Inspect`, `## 4. 允许读取的文件`, `## 需要读取的文件` |
| `files_allowed_to_modify` | `## Files Allowed To Modify`, `## 5. 允许修改的文件`, `## 可修改文件` |
| `files_forbidden` | `## Files Forbidden`, `## 6. 禁止修改的文件`, `## 禁止文件` |
| `implementation_requirements` | `## Implementation Requirements`, `## 7. 实现要求`, `## Requirements` |
| `acceptance_criteria` | `## Acceptance Criteria`, `## 8. 验收标准`, `## 验收条件` |
| `validation_tests` | `## Validation Tests`, `## 9. 验证测试`, `## Validation Commands` |
| `stop_conditions` | `## Stop Conditions`, `## 10. 停止条件`, `## 阻断条件` |
| `review_requirements` | `## Review Requirements`, `## 11. 审查要求`, `## 复审要求` |
| `rollback_plan` | `## Rollback Plan`, `## 12. 回滚计划`, `## 回滚方案` |
| `required_codex_result_pack` | `## Required Codex Result Pack`, `## 13. Codex 最终结果包`, `## Required Final Response` |

Validator 只匹配 Markdown 二级标题：以 `##` 开头的 heading。正文里的随机文本
不会被当作 section。

## Ingestion Modes

同一个 Task Pack 可以通过三种方式进入 workflow：

- `workflow_dispatch`: 粘贴到 `taskpack` 输入。
- `issues` opened/edited/labeled: issue body 就是 Task Pack。可信作者创建或编辑
  包含 metadata 的 issue 时不需要手动加标签；workflow 会读取 live issue labels，
  自动加 `agent:run`、`source:chatgpt-approved`、`agent:running`，并让重复
  opened/labeled 触发安全跳过。
- `repository_dispatch`: event type 为 `agent_loop_taskpack`，payload 中
  `taskpack` 字段就是 Task Pack。

三种入口都会先写入：

```text
/tmp/agent_loop/taskpack.raw.md
```

然后 routing/autofill 层生成：

```text
/tmp/agent_loop/taskpack.md
```

后续所有自动化只读取这个文件。

## Project Routing

Workflow 和脚本不得猜测目标项目。以下字段必须来自 metadata：

- `project`
- `allowed_paths`
- `forbidden_paths`
- `risk_tier`
- `plan_required`
- `validation_commands`

如果 `project` 缺失、为空、占位、或任务实际跨多个项目但没有拆分，Task
Pack 应失败或标记 `BLOCKED`。默认路由参考
`docs/governance/agent_loop/PROJECT_ROUTING_MATRIX.md`。

Workflow 可以补全缺失的 routing metadata，但只在
`TASKPACK_ROUTING_POLICY.md` 允许且项目唯一时补全。多项目必须拆分；模糊项目
必须 blocked。

## C2/C3/D1 Entry Points

- C2: Issue body 作为已批准 Task Pack，标签触发自动运行。
- C3: Issue Form 或 prefilled issue URL 降低非代码 Owner 的操作成本。
- D1: `scripts/agent_loop/submit_taskpack.py` 用本机 `gh` 创建 issue、发送
  dispatch 或触发 workflow fallback。

所有入口都不能加入 Planner Agent，不能在 GitHub Actions 内重新生成 Task
Pack，不能从模糊 issue 推断需求。

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

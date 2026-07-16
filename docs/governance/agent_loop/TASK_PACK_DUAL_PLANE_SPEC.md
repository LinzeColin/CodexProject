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
  "roadmap_task_id": "TSK.CodexProject.AGENTLOOP.0001",
  "acceptance_id": "ACC.CodexProject.AGENTLOOP.0001",
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

## Validation and publication

Task Pack 可以用本地 validator 或只读 `workflow_dispatch` 校验。只读 workflow
只把输入写到 runner 临时目录并运行 validator；它不创建 Issue、branch、PR、
artifact 或 merge。

发布是独立的外部身份边界。授权用户先推送一个临时的 same-repository branch，
再显式运行 `scripts/agent_loop/submit_taskpack.py --confirm-publish`。脚本创建一个
绑定 Task ID、Acceptance ID、head SHA 和 base SHA 的 PR。GitHub Actions 不持有
publisher credential。

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

## Entry points

- C2 Issue trigger：已退役。
- C3 Issue Form / prefilled Issue：已退役。
- D1 external publisher：当前唯一写入口，只能创建一个 marker-bound PR。
- Read-only validation workflow：可选校验入口，不具备写权限。

任何入口都不能在 GitHub Actions 内重新生成 Task Pack，也不能从模糊文本推断
需求或项目范围。

## T1 示例

```text
<!-- AGENT_LOOP_METADATA
{"agent_loop_version":"1.0","source":"chatgpt-approved","repository":"LinzeColin/CodexProject","risk_tier":"T1","auto_merge":true,"plan_required":false,"production_deploy":false,"project":"docs","roadmap_task_id":"TSK.CodexProject.DOCS.0001","acceptance_id":"ACC.CodexProject.DOCS.0001","allowed_paths":["docs/governance/agent_loop/**"],"forbidden_paths":["AGENTS.md","Alpha/**","EEI/**"],"validation_commands":["python3 scripts/agent_loop/validate_taskpack.py --taskpack taskpack.md"],"max_autofix_loops":1}
END_AGENT_LOOP_METADATA -->
```

## T2 示例

```text
<!-- AGENT_LOOP_METADATA
{"agent_loop_version":"1.0","source":"chatgpt-approved","repository":"LinzeColin/CodexProject","risk_tier":"T2","auto_merge":true,"plan_required":true,"production_deploy":false,"project":"governance","roadmap_task_id":"TSK.CodexProject.GOVERNANCE.0002","acceptance_id":"ACC.CodexProject.GOVERNANCE.0002","allowed_paths":["docs/governance/**","scripts/agent_loop/**"],"forbidden_paths":["AGENTS.md","Alpha/**","EEI/**","PFI/**"],"validation_commands":["python3 scripts/agent_loop/validate_plan.py --plan codex-plan.md --taskpack taskpack.md"],"max_autofix_loops":2}
END_AGENT_LOOP_METADATA -->
```

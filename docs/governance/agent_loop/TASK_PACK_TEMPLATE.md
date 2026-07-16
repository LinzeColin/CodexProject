# Dual-Plane Task Pack Template

复制本模板到 ChatGPT 对话中，填完后由 Owner 明确授权。先用本地 validator
或只读 validation workflow 校验；需要发布时由外部认证用户通过
`submit_taskpack.py --confirm-publish` 创建一个 marker-bound PR。

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
  "roadmap_task_id": "TSK.Project.Program.0001",
  "acceptance_id": "ACC.Project.Program.0001",
  "allowed_paths": [
    "docs/governance/agent_loop/**"
  ],
  "forbidden_paths": [
    "AGENTS.md",
    "Alpha/**",
    "EEI/**",
    "FIFA/**",
    "KMFA/**",
    "MetaDatabase/**",
    "OpenAIDatabase/**",
    "KM_IDSystem/**",
    "PFI/**",
    "QBVS/**",
    "Serenity-Alipay/**",
    "arxiv-daily-push/**",
    "whkmSalary/**"
  ],
  "validation_commands": [
    "python3 scripts/agent_loop/validate_taskpack.py --taskpack taskpack.md"
  ],
  "max_autofix_loops": 1
}
END_AGENT_LOOP_METADATA -->

# Task Pack: TITLE

## Human Summary

| Field | Value |
|---|---|
| Project | PROJECT |
| Risk Tier | T1 |
| Auto Merge | Yes |
| Production Deploy | No |
| Roadmap Task | TASK-ID |
| Acceptance | ACCEPTANCE-ID |

## Background

Describe why this task exists.

## Scope

Describe exactly what is in scope and out of scope.

## Files To Inspect

- `AGENTS.md`
- `docs/governance/STANDARD.md`

## Files Allowed To Modify

- `docs/governance/agent_loop/**`

## Files Forbidden

- `AGENTS.md`
- business project directories unless explicitly scoped.

## Implementation Requirements

- Requirement 1.
- Requirement 2.

## Acceptance Criteria

- Criterion 1.
- Criterion 2.

## Validation Tests

- `python3 scripts/agent_loop/validate_taskpack.py --taskpack taskpack.md`

If no runnable validation is possible, write an explicit N/A reason.

## Stop Conditions

- Stop if forbidden paths are needed.
- Stop if validation cannot run and no N/A reason is acceptable.

## Review Requirements

- Check scope drift.
- Check tests and validation.
- Check security/privacy risk.

## Rollback Plan

Revert the PR. No data migration or production rollback is required.

## Required Codex Result Pack

Codex final result must include:

- Summary.
- Files changed.
- Validation commands and exact results.
- Review/autofix status.
- Known risks.
- Rollback plan.
```

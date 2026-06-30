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
  "roadmap_task_id": "AGENT-LOOP-C2C3D1-T01",
  "acceptance_id": "AGENT-LOOP-C2C3D1-A01",
  "allowed_paths": [
    ".github/workflows/agent-loop-run-approved-taskpack.yml",
    ".github/ISSUE_TEMPLATE/codex-task.yml",
    "docs/governance/agent_loop/**",
    "scripts/agent_loop/**"
  ],
  "forbidden_paths": [
    "AGENTS.md",
    "Alpha/**",
    "EEI/**",
    "FIFA/**",
    "KMFA/**",
    "MetaDatabase/**",
    "OpenAIDatabase/**",
    "OpMe_System/**",
    "PFI/**",
    "QBVS/**",
    "Serenity-Alipay/**",
    "arxiv-daily-push/**",
    "whkmSalary/**"
  ],
  "validation_commands": [
    "python3 -m py_compile scripts/agent_loop/*.py"
  ],
  "max_autofix_loops": 1
}
END_AGENT_LOOP_METADATA -->

# Task Pack: Minimal Agent Loop T1 Fixture

## Human Summary

| Field | Value |
|---|---|
| Project | agent-loop |
| Risk Tier | T1 |
| Production Deploy | false |

## Background

This fixture validates local Agent Loop submitter and parser behavior.

## Scope

Use this Task Pack for local dry-run tests only.

## Files To Inspect

- `docs/governance/agent_loop/TASK_PACK_DUAL_PLANE_SPEC.md`

## Files Allowed To Modify

- `docs/governance/agent_loop/**`
- `scripts/agent_loop/**`

## Files Forbidden

- `AGENTS.md`
- Business project directories.

## Implementation Requirements

- No Planner Agent.
- No production deploy.

## Acceptance Criteria

- The Task Pack validates locally.
- The submitter dry-run does not call GitHub.

## Validation Tests

- `python3 -m py_compile scripts/agent_loop/*.py`

## Stop Conditions

- Stop if business project files are required.

## Review Requirements

- Check scope and no production deployment.

## Rollback Plan

No repository change is needed for this fixture dry-run.

## Required Codex Result Pack

Report validation results and whether GitHub was called.

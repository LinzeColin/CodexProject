<!-- AGENT_LOOP_METADATA
{
  "agent_loop_version": "1.0",
  "source": "chatgpt-approved",
  "repository": "LinzeColin/CodexProject",
  "risk_tier": "T1",
  "auto_merge": true,
  "plan_required": false,
  "production_deploy": false,
  "roadmap_task_id": "AGENT-LOOP-INVALID-T01",
  "acceptance_id": "AGENT-LOOP-INVALID-A01",
  "allowed_paths": ["docs/governance/agent_loop/**"],
  "forbidden_paths": ["AGENTS.md"],
  "validation_commands": ["python3 -m py_compile scripts/agent_loop/*.py"],
  "max_autofix_loops": 1
}
END_AGENT_LOOP_METADATA -->

# Task Pack: Invalid Missing Project Fixture

## Human Summary

| Field | Value |
|---|---|
| Project | Missing |
| Risk Tier | T1 |
| Production Deploy | false |

## Background

This fixture intentionally omits the required `project` metadata key.

## Scope

Use this fixture only to prove validator failure behavior.

## Files To Inspect

- `scripts/agent_loop/validate_taskpack.py`

## Files Allowed To Modify

- `docs/governance/agent_loop/**`

## Files Forbidden

- `AGENTS.md`

## Implementation Requirements

- Validator must reject this Task Pack.

## Acceptance Criteria

- `validate_taskpack.py` reports `TASKPACK_VALIDATION=FAIL`.

## Validation Tests

- `python3 scripts/agent_loop/validate_taskpack.py --taskpack docs/governance/agent_loop/examples/invalid_missing_project_taskpack.md`

## Stop Conditions

- Stop if this fixture passes validation.

## Review Requirements

- Confirm the failure reason includes missing project metadata.

## Rollback Plan

Remove this negative fixture.

## Required Codex Result Pack

Report the validator failure output.

---
name: project-governance
description: Maintain CodexProject model, parameter, development, delivery, version, and traceability governance. Use when creating or updating governance registries, validator rules, project migration records, delivery tasks, or governance CI.
---

# Project Governance Skill

Use this skill for CodexProject governance work only. It is not a general
feature-development skill.

## Required Inputs

Before editing, read:

1. `AGENTS.md`
2. `docs/governance/STANDARD.md`
3. `governance/projects.yaml`
4. The selected project's existing README, AGENTS, HANDOFF, VERSION, CHANGELOG,
   model, development, and task files when migrating that project.

For root governance work, inspect only root governance files and the top-level
project directory list needed to keep `governance/projects.yaml` complete.

## Execution Boundary

Default to one project, one task ID, and one acceptance target per run.
Do not migrate multiple projects in one run unless the user explicitly approves
that scope. Root governance changes must not migrate project business documents
or business code.

## Fact Discipline

Use only:

- `EXTRACTED`
- `RECONSTRUCTED`
- `PROPOSED`
- `UNKNOWN`
- `NOT_APPLICABLE`

Do not invent formulas, parameters, historical versions, test results, or
iteration counts. Git commit count is not iteration count.

## Workflow

1. Report a compact run contract: goal, scope, files to inspect, files to
   modify, validation commands, risks, rollback, stop conditions.
2. Inspect only the selected project and root governance files.
3. Update model, formula, parameter, delivery, version, and traceability files
   together when behavior changes.
4. Append one `development_events.jsonl` event for meaningful project
   development work.
5. Update delivery task acceptance and evidence when a task is completed.
6. Run `python3 scripts/validate_project_governance.py --project <project_id>`.
7. For root governance changes, run
   `python3 scripts/validate_project_governance.py --all --semantic --drift-report`.
8. Regenerate human-readable status pages with
   `python3 scripts/generate_governance_dashboard.py --write` and verify
   `git diff --exit-code -- GOVERNANCE_DASHBOARD.md */docs/governance/STATUS.md`
   after a second generation pass.

## P20 Incident Runs

Hotfix and rollback runs are event-driven. Before changing files, verify that
`PROJECT_PATH`, `INCIDENT_ID`, `AFFECTED_VERSION`, and
`TARGET_ROLLBACK_VERSION` are all provided with evidence. If any required value
is missing, do not invent an incident; perform only readiness or template work
and report the missing input.

## Stop Conditions

Stop and report if:

- Evidence is insufficient to classify a model or parameter.
- P20 incident inputs are missing or the evidence does not identify an affected version.
- A required project fails validator after one focused repair pass.
- Fixing the failure would require changing unrelated business code.
- The requested scope would migrate more than one project without approval.

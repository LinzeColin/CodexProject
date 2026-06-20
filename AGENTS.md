# CodexProject Governance Rules

This repository is a multi-project source hub. Keep this file concise; detailed
rules live in `docs/governance/STANDARD.md`.

## Permanent Rules

- Every project must be registered in `governance/projects.yaml`.
- Every project must maintain model, development, delivery, version, and traceability files.
- One Codex run should handle one project, one task ID, and one acceptance target by default.
- Before implementation, report the files to read, files to modify, test commands, risks, and rollback path.
- When code, configuration, rules, formulas, thresholds, or model behavior changes, update model and parameter documentation in the same run.
- Every meaningful development run must append one development event. Do not overwrite history.
- Completed tasks must update delivery task status, Acceptance, and evidence.
- Do not infer iteration count from Git commit count.
- Do not invent formulas, parameters, historical versions, or test results.
- `UNKNOWN` must link to a concrete unresolved task. Do not use vague `TBD` placeholders.
- Hotfix or rollback work requires a concrete incident ID, affected version, target rollback version, and evidence. Do not invent incidents.
- Done means the governance validator passes for the affected scope.
- Do not scan directories unrelated to the current project and task.

## Model Definition

In this repository, a model includes mathematical models, statistical models,
machine-learning models, ranking or scoring models, backtest strategies, risk
models, salary or business calculation formulas, deterministic rule engines,
heuristic algorithms, and LLM routing or fallback strategies.

Technology stack names are not models. A project with no model still needs
`MODEL_SPEC.md`, with evidence-backed `NOT_APPLICABLE` status.

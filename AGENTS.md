# CodexProject Governance Rules

This repository is a multi-project source hub. Keep this file concise; detailed
rules live in `docs/governance/STANDARD.md`.

## Permanent Rules

- Every project must be registered in `governance/projects.yaml`.
- Every project must maintain model, development, delivery, version, and traceability files.
- Required project artifacts are `VERSION`, `CHANGELOG.md`, and all files under the standard `docs/governance/` contract listed in `docs/governance/STANDARD.md`.
- One Codex run should handle one project, one task ID, and one acceptance target by default.
- Use the `T0`-`T3` risk-tier routing in `docs/governance/STANDARD.md`. Default to `T0`/`T1` unless a concrete model, formula, parameter, schema, safety, release, legal, privacy, money, or production risk requires `T2`/`T3`.
- Non-trivial `T2`/`T3` software development, refactoring, model changes, releases, or multi-file fixes must explicitly invoke `$codex-dex`.
- Before implementation, report the files to read, files to modify, test commands, risks, and rollback path.
- Default to a bounded PLAN / READ-ONLY pass before implementation unless the user explicitly provides a narrow implementation contract.
- When code, configuration, rules, formulas, thresholds, or model behavior changes at `T2`/`T3`, update model and parameter documentation in the same run.
- Meaningful `T2`/`T3` development runs append one development event. Do not overwrite history. `T0`/`T1` runs may use a concise change note or PR body instead of a governance event.
- Completed `T2`/`T3` tasks must update delivery task status, Acceptance, and evidence. `T0`/`T1` changes do not need generated-view or attestation updates.
- Do not infer iteration count from Git commit count.
- Do not invent formulas, parameters, historical versions, or test results.
- `UNKNOWN` must link to a concrete unresolved task. Do not use vague `TBD` placeholders.
- Hotfix or rollback work requires a concrete incident ID, affected version, target rollback version, and evidence. Do not invent incidents.
- Done means the affected tests pass and the changed-scope governance validator passes when the change touches governed files. Full portfolio, generated-view drift, and attestation proof belong to scheduled/manual/release gates.
- Do not scan directories unrelated to the current project and task.
- Detailed schemas, templates, and execution rules live in `docs/governance/STANDARD.md`; do not duplicate the full standard in nested AGENTS files.

## Model Definition

In this repository, a model includes mathematical models, statistical models,
machine-learning models, ranking or scoring models, backtest strategies, risk
models, salary or business calculation formulas, deterministic rule engines,
heuristic algorithms, and LLM routing or fallback strategies.

Technology stack names are not models. A project with no model still needs
`MODEL_SPEC.md`, with evidence-backed `NOT_APPLICABLE` status.

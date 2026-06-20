# CodexProject Governance Standard

Governance spec version: `1.0.0`

This standard defines the minimum model, development, delivery, version, and
traceability controls for every project in CodexProject.

## Fact Levels

Every material statement about models, parameters, tasks, versions, and tests
must use one of these labels:

- `EXTRACTED`: directly extracted from code, configuration, tests, or a primary project document.
- `RECONSTRUCTED`: rebuilt from multiple evidence sources or Git history.
- `PROPOSED`: recommended by a current plan, not yet implemented.
- `UNKNOWN`: not confirmable from current evidence and linked to a task.
- `NOT_APPLICABLE`: confirmed not applicable, with evidence.

Do not convert `PROPOSED` or `UNKNOWN` values into current active facts.

## Model Scope

Models include, but are not limited to:

- Mathematical models.
- Statistical models.
- Machine-learning models.
- Ranking or scoring models.
- Backtest strategies.
- Risk models.
- Salary or business calculation formulas.
- Deterministic rule engines.
- Heuristic algorithms.
- LLM routing and fallback strategies.

Technology stacks, providers, libraries, frameworks, and database names are not
models unless the project defines behavior-changing routing, fallback, scoring,
or decision logic around them.

Projects with no model must still maintain `docs/governance/MODEL_SPEC.md` and
must explain `NOT_APPLICABLE` with evidence.

## Required Project Governance Files

Each registered project must eventually maintain:

- `docs/governance/MODEL_SPEC.md`
- `docs/governance/model_registry.yaml`
- `docs/governance/formula_registry.yaml`
- `docs/governance/parameter_registry.csv`
- `docs/governance/DEVELOPMENT_LEDGER.md`
- `docs/governance/development_events.jsonl`
- `docs/governance/DELIVERY_PLAN.md`
- `docs/governance/delivery_tasks.yaml`
- `docs/governance/VERSION_MATRIX.yaml`
- `docs/governance/TRACEABILITY_MATRIX.csv`
- `VERSION`
- `CHANGELOG.md`

Advisory projects warn while migrating. Required projects fail validation when
these files are missing or invalid.

## Registry Coverage

`governance/projects.yaml` is the authoritative project register. It must cover
every actual project directory in this repository, including nested project
directories such as `PFI/大数据模拟器`.

Root governance is separate from project governance:

- Root governance framework: `required`.
- During migration, projects may be `advisory` until their baseline is accepted.
- After G5 enforcement, every `existing` registered project must be `required`.
- Only explicitly `archived` or `excluded` projects may remain non-required, with owner, reason, archive date, and replacement or restore condition.

Do not make all projects required before their governance baseline has been
migrated and accepted.

## Run Contract

Before changing files, each implementation run should report:

1. Goal.
2. Minimum relevant scope.
3. Files and directories to inspect.
4. Files likely to change.
5. Validation commands.
6. Risks and rollback.
7. Stop conditions.

Default execution boundary: one project, one task ID, one acceptance target.

## Data Structures

### `governance/projects.yaml`

Required root fields:

- `governance_spec_version`
- `root_governance.ci_mode`
- `root_governance.required_files`
- `project_governance_files`
- `projects`

Required project fields:

- `project_id`
- `path`
- `ci_mode`
- `status`
- `model_behavior_globs`

`ci_mode` enum: `required`, `advisory`.

### `model_registry.yaml`

Required root fields:

- `governance_spec_version`
- `project_id`
- `models`

Required model fields:

- `model_id`
- `name`
- `kind`
- `purpose`
- `owner`
- `status`
- `fact_level`
- `model_version`
- `assumptions`
- `formula_ids`
- `parameter_ids`
- `inputs`
- `outputs`
- `code_refs`
- `test_refs`
- `evidence_refs`

Model status enum: `active`, `planned`, `deprecated`, `not_applicable`.
Assumptions use stable IDs such as `ASM-001`.

### `formula_registry.yaml`

Required root fields:

- `governance_spec_version`
- `project_id`
- `formulas`

Required formula fields:

- `formula_id`
- `model_id`
- `assumption_ids`
- `status`
- `expression`
- `variables`
- `constraints`
- `missing_policy`
- `output_range`
- `code_refs`
- `test_refs`
- `evidence_refs`

Formula status enum: `active`, `planned`, `deprecated`, `not_applicable`.
Variables must define name, data type, unit, and input domain or range.

### `parameter_registry.csv`

Required columns:

- `parameter_id`
- `model_id`
- `formula_id`
- `symbol`
- `name`
- `category`
- `data_type`
- `unit`
- `default_value`
- `initial_or_prior_value`
- `active_value`
- `weight`
- `weight_group`
- `weight_group_target`
- `weight_group_tolerance`
- `min_value`
- `max_value`
- `formula_or_transform`
- `source_or_rationale`
- `calibration_method`
- `sensitivity`
- `code_ref`
- `config_ref`
- `test_ref`
- `status`
- `fact_level`
- `unknown_task_ids`
- `parameter_version`
- `last_updated`

Parameter status enum: `active`, `planned`, `deprecated`, `not_applicable`.

### `development_events.jsonl`

Append-only. Each non-empty line must be valid JSON with:

- `event_id`
- `timestamp`
- `actor`
- `phase`
- `task_id`
- `change_type`
- `summary`
- `files_changed`
- `model_ids_changed`
- `parameter_ids_changed`
- `tests_run`
- `result`
- `evidence_refs`
- `git_commit`
- `fact_level`

### `delivery_tasks.yaml`

Required root fields:

- `governance_spec_version`
- `project_id`
- `tasks`

Required task fields:

- `task_id`
- `phase`
- `objective`
- `scope`
- `non_scope`
- `status`
- `dependencies`
- `required_files`
- `acceptance_ids`
- `test_commands`
- `test_results`
- `evidence_refs`
- `risk`
- `rollback`
- `target_version`
- `completed_version`

Task status enum: `proposed`, `planned`, `ready`, `in_progress`, `blocked`,
`completed`, `rejected`, `deprecated`.

### `VERSION_MATRIX.yaml`

Required fields:

- `product_version`
- `product_version_status`
- `governance_spec_version`
- `schema_version`
- `model_versions`
- `parameter_profile_versions`
- `data_snapshot_version`
- `current_iteration`
- `current_phase`
- `current_gate`

If a project has no trustworthy product version, use `0.0.0` and
`product_version_status: provisional`.

### `TRACEABILITY_MATRIX.csv`

Required columns:

- `requirement_id`
- `model_id`
- `assumption_id`
- `formula_id`
- `parameter_id`
- `task_id`
- `acceptance_id`
- `code_ref`
- `config_ref`
- `test_ref`
- `evidence_ref`
- `status`

### `INCIDENT_RESPONSE`

P20 hotfix or rollback work is event-driven. It must not be treated as complete
readiness work unless a real incident is supplied.

Required incident inputs:

- `PROJECT_PATH`
- `INCIDENT_ID`
- `AFFECTED_VERSION`
- `TARGET_ROLLBACK_VERSION`
- Incident time.
- Impact scope.
- Symptoms.
- Evidence references.

Incident records must distinguish:

- Symptoms.
- Evidence.
- Hypotheses.
- Confirmed root cause.

Do not guess root cause. If root cause is unknown, set
`root_cause_status: unknown`, preserve the evidence, and link a follow-up task.

P20 changes must update:

- Incident task.
- `development_events.jsonl`.
- `DEVELOPMENT_LEDGER.md`.
- `CHANGELOG.md`.
- Risk and rollback records.

The root template is `docs/governance/templates/INCIDENT_RESPONSE.template.md`.
The machine schema is `governance/schemas/incident_response.schema.json`.

## Cross-Reference Rules

The required closed loop is:

`requirement -> model -> assumption -> formula -> parameter -> code -> test -> task -> acceptance -> release gate -> evidence`

Rules:

- Every `formula.model_id` must exist in `model_registry.yaml`.
- Every `formula.assumption_ids` value must exist in the referenced model's assumptions or in root-level assumptions.
- Every `parameter.model_id` must exist in `model_registry.yaml`.
- Every `parameter.formula_id` must exist in `formula_registry.yaml` unless the parameter is explicitly `NOT_APPLICABLE`.
- Every `completed` task must have at least one Acceptance ID, actual test command, actual test result, evidence reference, and completion version or commit.
- Every `UNKNOWN` value must have an unresolved task reference.

## Version Governance

Each project tracks independent versions:

- `product_version`
- `governance_spec_version`
- `schema_version`
- `model_versions`
- `parameter_profile_versions`
- `data_snapshot_version`

`VERSION`, `VERSION_MATRIX.yaml`, `CHANGELOG.md`, and
`DEVELOPMENT_LEDGER.md` must agree on the active product version for required
projects.

Version changes must be linked to a development event and changelog entry.

## Parameter Rules

Active parameters must record:

- Default value.
- Prior or initial value when applicable.
- Current active value.
- Unit.
- Allowed range or explicit unbounded reason.
- Source or rationale.
- Calibration method or `NOT_APPLICABLE`.
- Code reference or explicit external-source rationale.
- Test reference.

Weights must declare `weight_group` and `weight_group_tolerance` when they must
sum to a target, normally `1.0`.

## Formula Rules

Active formulas must record:

- Mathematical expression or precise deterministic rule.
- Variables and units.
- Input domain.
- Constraints.
- Missing-value behavior.
- Output range or type.
- Code reference.
- Test reference.

## Validator Policy

The validator must support:

```bash
python scripts/validate_project_governance.py --all
python scripts/validate_project_governance.py --project EEI
python scripts/validate_project_governance.py --changed-only
```

It must fail required scopes and warn for advisory scopes.

## Prohibited Shortcuts

- Do not use Git commit count as iteration count.
- Do not invent formula details, weights, thresholds, versions, or tests.
- Do not treat a provider name as a business model.
- Do not mark tasks complete without acceptance and evidence.
- Do not scan unrelated business directories during a focused run.

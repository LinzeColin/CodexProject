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
- `docs/governance/STATUS.md`
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

## Codex Execution Layers

The repository governance framework is enforced in layers:

- Codex Personalization: short global routing instructions for the user profile.
- Global `~/.codex/AGENTS.md`: user-wide development constraints.
- Repository `AGENTS.md`: this repository's mandatory governance contract.
- Repository `.agents/skills/codex-dex/SKILL.md`: governed development workflow for implementation, model changes, releases, and multi-file fixes.
- Repository `.codex/hooks.json` and `.codex/hooks/governance_stop.py`: Stop Hook that runs changed-scope governance validation before a Codex turn is allowed to finish.
- `.github/workflows/project-governance.yml`: GitHub Actions validation for PRs, pushes to `main`, and manual all/project/changed-only runs.
- GitHub branch protection or rulesets: repository setting that must make Project Governance a required status check for `main`.

## Review-5 Diff Synchronization Contract

Structural validation is not enough. The repository also enforces a
diff-driven synchronization contract through
`scripts/validate_governance_sync.py`.

The sync validator classifies changed files as:

- `model_behavior_change`
- `parameter_or_config_change`
- `data_snapshot_change`
- `test_or_evidence_change`
- `product_capability_change`
- `governance_only_change`
- `trivial_change`

Behavior, parameter, data, test, evidence, or product changes must travel with
the governance records that make the change auditable. For example, model
behavior changes require same-run updates or explicit review of:

- `MODEL_SPEC.md`
- `model_registry.yaml`
- `formula_registry.yaml`
- `parameter_registry.csv`
- `DEVELOPMENT_LEDGER.md`
- `development_events.jsonl`
- `delivery_tasks.yaml`
- `TRACEABILITY_MATRIX.csv`
- `VERSION_MATRIX.yaml`
- `STATUS.md`
- `CHANGELOG.md` or an explicit no-version-change rationale in the run record

Project `development_events.jsonl` files are append-only. Existing lines must
not be modified or removed; follow-up evidence belongs in a new event or a
post-commit binding.

## Review-6 Entry Gate Contract

Every execution entry must use the same diff contract when a diff is available:

- Pull requests run `--changed-only --enforce-sync --semantic` against the PR base.
- Pushes to `main` run `--changed-only --enforce-sync --semantic --base-ref <github.event.before>` and then `--all --semantic --drift-report`.
- Manual `workflow_dispatch` with `scope=changed-only` accepts an optional `base_ref` and uses the same diff contract.
- The Codex Stop Hook reruns the validator even on recursive Stop passes. It may cap automatic repair loops, but it must not unconditionally allow a failed second Stop.

If branch protection or ruleset details cannot be inspected with authenticated
GitHub evidence, their required-check and no-bypass status must remain
`UNVERIFIED`.

## Run Manifest and Post-Commit Binding

Root governance runs may record machine-readable manifests under:

```text
governance/run_manifests/<RUN_ID>.json
```

Each manifest records at least:

- `run_id`
- `project_id`
- `task_id`
- `acceptance_id`
- `actor`
- `started_at`
- `finished_at`
- `base_commit`
- `content_tree_hash`
- `changed_files_actual`
- `change_classification`
- `required_governance_files`
- `updated_governance_files`
- `model_delta`
- `formula_delta`
- `parameter_delta`
- `version_delta`
- `tests_run`
- `observed_results`
- `evidence_refs`
- `rollback`
- `unresolved_risks`

Do not require a commit to contain its own final SHA. If final commit binding is
required, use GitHub Checks evidence or append a later binding event that maps
`run_id`, `content_tree_hash`, final commit SHA, and CI run.

Post-commit CI evidence is recorded as an attestation under:

```text
governance/ci_attestations/<RUN_ID>.json
```

Each attestation binds a pre-commit run manifest or workflow run to:

- final commit SHA
- workflow name
- workflow run ID and attempt
- job ID when available
- conclusion
- finished timestamp
- evidence hash

Run manifests may remain local/pre-submit facts. A manifest that still says
`PENDING_CI` after the allowed binding window must have a matching successful
CI attestation or the semantic validator reports a governance issue.

## Semantic Accuracy

`--semantic` checks enforce facts that can be machine-verified without inventing
domain knowledge:

- `code_ref`, `config_ref`, and `test_ref` paths must exist when they point to
  repository files.
- `VERSION_MATRIX.current_iteration` must match the latest extracted event.
- `DEVELOPMENT_LEDGER` confirmed iteration counts must match the actual
  confirmed iteration sections.
- Existing development events remain append-only under diff validation.

Facts that cannot be machine-verified must remain `UNKNOWN` or
`HUMAN_REVIEW_REQUIRED`; do not present them as `EXTRACTED`.

## Human-Readable Generated Status

`scripts/generate_governance_dashboard.py` generates:

- root `GOVERNANCE_DASHBOARD.md`
- each project `docs/governance/STATUS.md`

These pages are read-only views generated from registries, events, version
matrices, ledgers, and Git metadata. They must not become duplicate editable
fact sources. CI regenerates them and fails if committed status pages drift.

Personalization and user-level config are documented in
`docs/governance/CODEX_SETUP.md`. Repository files, validators, tests, and
GitHub Actions are the source of truth for auditable delivery.

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

For non-trivial software development, invoke `$codex-dex` before editing.

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

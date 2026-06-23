# Lean Project Governance Standard v2.0

Governance spec version: `2.0.0-lean-transition`

## Purpose

CodexProject governance must preserve accurate owner-useful project truth while
reducing agent context, CI latency, token cost, generated Git noise, and
duplicate synchronization. Root `AGENTS.md` is the permanent execution contract;
this standard defines the machine rules, field contracts, sync rules, and
acceptance gates behind it.

## Project Contract

Every active registered project must have these exact project-root human entry
files:

- `功能清单`
- `开发记录`
- `模型参数文件`
- `VERSION`
- `CHANGELOG.md`

The three Chinese files are complete human views, not aliases, compatibility
indexes, or links to `docs/governance/`.

The Lean v2 canonical fact target for each project is:

- `docs/governance/project.yaml`
- `docs/governance/roadmap.yaml`
- `docs/governance/events.jsonl`
- `VERSION`
- `CHANGELOG.md`

`governance/schemas/project.schema.json` defines the Lean v2 project fact
contract. It must be able to carry features, models, assumptions, formulas,
parameters, strategies, validation records, and evidence references with
explicit fact levels. `UNKNOWN` remains a first-class fact level and must not be
collapsed into verified truth.

During migration, existing v1 registries and status files remain governance
truth. Do not delete, archive, or rewrite them until the project has passed its
Lean v2 migration gate.

## Roadmap Contract

`开发记录` must directly render a complete owner-readable Roadmap.

Structure:

```text
Stage -> Phase -> Task
```

`governance/schemas/roadmap.schema.json` defines the Lean v2 Roadmap facts.
It constrains Stage, Phase, and Task IDs, task status, estimates, dependencies,
Acceptance IDs, test commands, evidence refs, risks, rollback, Stop Conditions,
and Stop Gates. The schema stores estimate and percentage fields; deterministic
recalculation and drift checks belong to the CLI/validator instead of manual
editing.

`governance/schemas/events.schema.json` defines one append-only
`events.jsonl` event line. Events record meaningful decisions,
implementations, validations, migrations, releases, incidents, owner
acceptance, evidence updates, or rollbacks. They are not a transcript of every
agent action. Event and evidence fact levels are limited to `VERIFIED`,
`RECONSTRUCTED`, `PROPOSED`, and `UNKNOWN`.

IDs:

- Stage: `S1`, `S2`, ...
- Phase: `S1PA`, `S1PB`, ...
- Task: `S1PAT01`, `S1PET01`, ...
- Task regex: `^S[1-9][0-9]*P[A-Z]T[0-9]{2}$`

Each Task records name, objective, status, estimated hours, dependencies,
Acceptance IDs, test commands, evidence, risks, rollback, and current result.

Each Stage and Phase records name, objective or person goal, Stop Conditions,
Stop Gate, pass criteria, evidence, failure action, approver, child count,
derived hours, and derived percentage.

Derived values are calculated, not hand-maintained:

```text
task_pct = task_hours / total_active_task_hours * 100
phase_hours = sum(child task hours)
stage_hours = sum(descendant task hours)
progress = completed task hours / total_active_task_hours * 100
```

Display percentages with two decimals. Validate totals with unrounded values
and a 0.1 percentage-point tolerance.

Task status enum:

```text
proposed, planned, ready, in_progress, blocked, completed, rejected, deprecated
```

Completed tasks require Acceptance, actual test commands, actual results,
evidence, and a completion version or commit.

## Human Views

`功能清单` first screen: version, current Stage/Phase/Task, capability count,
blockers, next Gate, and next unique task. Capabilities include value, scope,
non-scope, implementation refs, test refs, evidence, limitations, and current
status.

`docs/governance/templates/功能清单.template.md` is the template for that
human view. It starts with summary fields, then owner decisions, capability
overview, evidence, limitations, and feature detail. It must not degrade into a
link page.

`开发记录` first screen: version, current Stage/Phase/Task, total and completed
hours, progress, blockers, next Gate, and next unique task. It renders the full
Roadmap and recent meaningful events.

`docs/governance/templates/开发记录.template.md` is the template for that human
view. It starts with summary fields, then owner decisions, progress overview,
the full Roadmap, recent meaningful events, and risks or blockers. It must not
degrade into a link page.

`docs/governance/templates/Roadmap.template.md` is the owner-readable Roadmap
template. It directly renders Stage, Phase, Task, Stop Gate, Acceptance, and
Evidence sections, while derived calculations remain deterministic validator
work rather than manual governance computation.

`模型参数文件` records active models, assumptions, inputs, outputs, formulas or
pseudocode, variables, units, domains, missing-value behavior, fallback behavior,
parameters, defaults, priors, active values, ranges, weights, sources,
calibration, validation, limitations, stop conditions, and code/config/test
evidence refs.

`docs/governance/templates/模型参数文件.template.md` is the template for that
human view. It starts with summary fields, then evidence, limitations, models,
formulas, parameters, and validation. It must keep formulas and parameters in
the owner-readable file rather than replacing them with links.

Technology stack names are architecture facts, not model parameters. A project
with no model still documents evidence-backed `NOT_APPLICABLE`.

## Evidence And Fact Levels

Current machine fact levels remain:

```text
EXTRACTED, RECONSTRUCTED, PROPOSED, UNKNOWN, NOT_APPLICABLE
```

Owner-facing evidence states may additionally use:

```text
VERIFIED, PARTIALLY_VERIFIED, CONTRADICTED, STALE
```

Do not convert `PROPOSED`, `UNKNOWN`, `PARTIALLY_VERIFIED`, `CONTRADICTED`, or
`STALE` into current active facts. `UNKNOWN` must link to a resolving Roadmap
task. Critical model, formula, parameter, release, money, legal, privacy, and
production claims require evidence refs.

## Run Modes And Writes

| Mode | Baseline | Deep validation | Repository writes |
|---|---|---|---|
| `READ_ONLY` / `REVIEW` | all, compact | requested scope | prohibited |
| `PLAN` | all, compact | target project | prohibited |
| `IMPLEMENT` | all, compact | selected task scope | selected task scope only |
| `CI` | changed scope | changed projects/root | prohibited |
| `Hook` | changed-file hint | none | prohibited |
| `NIGHTLY` / `MANUAL` / `RELEASE` | all | all | prohibited unless an explicit release task says otherwise |

Only the selected target render task may use write mode to update the three
target-project human files. CI and Hook never use `--write`.

## Risk-Tier Routing

Default to T0/T1. Upgrade only when concrete risk requires it.

| Tier | Typical changes | Required PR gate | Full governance |
|---|---|---|---|
| `T0` | Documentation, copy, formatting, small text | Changed-scope Project Governance | Not required |
| `T1` | Local bug fix, isolated logic, non-critical config | Affected tests plus changed-scope Project Governance | Not required |
| `T2` | Model, formula, parameter, schema, migration, security rule, evidence contract | Affected full tests plus project governance records | Manual full gate when owner requires it |
| `T3` | Production release, money, payroll, legal, privacy, permissions, deletion, live delivery | Full tests, human approval evidence, release/manual all governance | Required before production or release acceptance |

Do not apply T2/T3 governance computation to ordinary T0/T1 work.

## Agent Workflow

1. Run compact baseline.
2. Select one project, one Roadmap Task ID, and one Acceptance ID.
3. Bound the read list.
4. State files to read, files to modify, tests, risks, rollback, and stop
   conditions.
5. Implement without scope expansion.
6. Update affected canonical facts.
7. Append one event only when product, model, parameter, test, Roadmap, or
   Acceptance outcome materially changes.
8. Render/check the target human files when the selected task requires it.
9. Run validation and focused tests.
10. Inspect the diff and report actual results plus the next unique task.

Pure rendering, dashboard refresh, review, or CI is not a product iteration and
must not create a development event or product version.

## Changed-Scope CI And Hook

Every pull request runs one required Project Governance job focused on
changed-scope validation against the PR base. Pushes to `main` run the same
contract against the previous main commit. Manual `scope=changed-only` accepts
an optional `base_ref`.

Scheduled and manual `scope=all` runs execute full information-quality,
all-project semantic/drift validation, generated-view determinism checks, and CI
attestation upload.

The Stop Hook is advisory only. It may detect changed governance files and
suggest commands. It must not run generators, validators, setup doctor,
semantic extraction, receipt writing, attestation, or recursive repair loops.

If branch protection or ruleset details cannot be inspected with authenticated
GitHub evidence, required-check and no-bypass status remain `UNVERIFIED`.

## Sync And Manifests

Meaningful code, config, model, parameter, data, test, evidence, product, or
governance changes must travel with the governance records that make the change
auditable.

Root governance changes require:

- a run manifest under `governance/run_manifests/`;
- an updated governance test when the contract changes;
- changed-scope Project Governance success.

Run manifests use schema v2 and record at least:

```text
schema_version, run_id, project_id, task_id, acceptance_ids, iteration_id,
generated_at, implementation_base_sha, content_tree_hash,
changed_files_declared, changed_files_actual, required_governance_files,
updated_governance_files, test_commands, test_results, evidence_refs,
binding_status, ci_attestation_subject, ci_run_reference
```

Do not require a manifest to contain its own final commit SHA. If final binding
is required, use a later CI attestation or append-only binding event.

## Machine Field Contracts

`governance/projects.yaml` requires:

```text
governance_spec_version, root_governance.ci_mode,
root_governance.required_files, project_governance_files, projects
```

Each project registry entry is deliberately small:

```text
project_id, path, ci_mode, migration.version
```

Project entries must not carry semantic coverage, extractor state, model
behavior globs, active-count claims, task targets, evidence summaries, or other
computed governance state. Those facts remain in project-level governance
files, run manifests, or later Lean v2 canonical facts, and are checked by
explicit validation modes instead of being recomputed from the registry during
every development action.

During Lean v2 migration, `ci_mode` stays `advisory` for unmigrated projects.
Only Stage 6 may switch a project to `required` after its Lean v2 migration
gate passes and owner/branch-protection evidence exists. The current v1 files
remain valid until replaced by project-level `project.yaml`, `roadmap.yaml`,
and `events.jsonl` through the approved Stage 4/5 migration tasks.

Current v1 required project governance files remain:

```text
MODEL_SPEC.md, model_registry.yaml, formula_registry.yaml,
parameter_registry.csv, DEVELOPMENT_LEDGER.md, development_events.jsonl,
DELIVERY_PLAN.md, delivery_tasks.yaml, VERSION_MATRIX.yaml,
TRACEABILITY_MATRIX.csv, STATUS.md, OWNER_STATUS.md, VERSION, CHANGELOG.md
```

Validator commands remain:

```bash
python scripts/validate_project_governance.py --all
python scripts/validate_project_governance.py --project <project_id>
python scripts/validate_project_governance.py --changed-only --enforce-sync --semantic
```

## Semantic Accuracy

Machine semantic checks verify repository facts without inventing domain
knowledge:

- referenced `code_ref`, `config_ref`, and `test_ref` paths exist;
- event files are append-only;
- current iteration and gate agree with the latest extracted event;
- active parameter values match extractors when semantic extraction is enabled;
- active formula implementation fingerprints match extractors when enabled;
- registry entries stay identity-only and do not store semantic coverage or
  extractor rollout state.

Facts that cannot be machine-verified remain `UNKNOWN`,
`HUMAN_REVIEW_REQUIRED`, `PARTIALLY_VERIFIED`, or another non-active evidence
state. They must not be presented as verified active facts.

## Token Budget And Scope

- Root `AGENTS.md` target: <= 4 KB.
- Ordinary initial governance context target: <= 12 KB and <= 5 files.
- Compact baseline output target: <= 2 KB.
- One task per run.
- No all-project LLM reading in ordinary work.
- Exclude dependencies, caches, generated outputs, artifacts, backups, binaries,
  and large data unless the selected task explicitly requires them.

## Migration And Cleanup

Governance v1 files remain read-only during project migration. After all
projects pass Lean v2, archive old framework files with checksums and remove
them only after reference scan, one release-cycle retention, and owner approval.

Do not enable `required` for an unmigrated project. Do not delete truth before
the replacement truth is accepted.

## Prohibited Shortcuts

- Do not use Git commit count as iteration count.
- Do not invent formulas, parameters, thresholds, versions, tests, owner
  decisions, or evidence.
- Do not treat provider or technology names as model parameters.
- Do not mark tasks complete without Acceptance, actual tests, and evidence.
- Do not scan unrelated business directories during a focused run.
- Do not use generated dashboards or status pages as editable source facts.

## Definition Of Done

The selected task is done only when Acceptance, actual tests, evidence,
canonical facts, human views, Roadmap status, scoped diff, rollback path, and
changed-scope validation are consistent. Read-only modes, CI, and Hook must
write nothing. No `UNKNOWN` may be presented as verified truth.

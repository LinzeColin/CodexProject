# Lean Project Governance Standard v2.0

Governance spec version: `2.0.0-lean-transition`

## 目的

CodexProject governance 的目标是保留准确、对 owner 有用的项目事实，同时降低
agent context、CI latency、token cost、generated Git noise、以及 duplicate
synchronization。根目录 `AGENTS.md` 是永久执行契约；本标准定义其背后的 machine
rules、field contracts、sync rules、acceptance gates。

## 项目契约

每个 active registered project 都必须在项目根目录拥有以下 exact human entry files：

- `功能清单.md`
- `开发记录.md`
- `模型参数文件.md`
- `VERSION`
- `CHANGELOG.md`

这三份中文文件是完整 human views，不是 aliases、compatibility indexes、或指向
`docs/governance/` 的 link pages。

中文优先、默认全局中文适用于整个仓库和每个 registered project。除非 owner 或更严格的
project-specific contract 明确要求其他语言，governance summaries、PR descriptions、
CI-facing summaries、owner-facing documents、project human-entry files 默认使用中文。
为保证准确性，technical identifiers、code symbols、file paths、API names、exact
quoted source text 可以保留原语言。

每个项目的 Lean v2 canonical fact target 是：

- `docs/governance/project.yaml`
- `docs/governance/roadmap.yaml`
- `docs/governance/events.jsonl`
- `VERSION`
- `CHANGELOG.md`

`governance/schemas/project.schema.json` 定义 Lean v2 project fact contract。它必须能承载
features、models、assumptions、formulas、parameters、strategies、validation records、
以及带显式 fact levels 的 evidence references。`UNKNOWN` 是一等 fact level，不能被折叠成 verified truth。

迁移期间，existing v1 registries 和 status files 仍是 governance truth。在项目通过 Lean v2
migration gate 前，不要 delete、archive、或 rewrite 它们。

## Roadmap Contract

`开发记录.md` must directly render a complete owner-readable Roadmap.

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

IDs use an immutable V2 registry contract:

- Canonical V2 Task: `TSK.<project>.<program>.<sequence>`.
- Canonical V2 Acceptance: `ACC.<project>.<program>.<sequence>` with the exact
  same suffix as its Task.
- Canonical V2 Event: `EVT.<project>.<program>.<sequence>` in an independent
  namespace; Pursuing Goal uses `PG.<project>.<goal>`.
- Stage (`S1`) and Phase (`S1PA`) remain mutable placement metadata and are not
  encoded in a new permanent Task ID.
- Existing positional IDs such as `S1PAT01` and their legacy Acceptance IDs stay
  readable; they are not mass-rewritten.
- A mixed V1/V2 reference requires an explicit project-scoped alias. New
  positional IDs fail after bootstrap.
- New IDs come only from `scripts/governance_id_allocator.py`; allocation needs
  base SHA, idempotency key, registry SHA compare-and-swap, and the Git-dir
  single-flight lock.
- `governance/id_registry.json` is the allocation ledger. JSON Schema provides
  shape validation; `scripts/governance_id_audit.py` enforces property-level
  uniqueness, exactly-one resolution, dependency acyclicity, immutability, and
  positional-ID cutoff because `uniqueItems` cannot prove those properties.
- The operational and legacy alias contract is
  `docs/governance/ID_GOVERNANCE_V2.md`.

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

`功能清单.md` first screen: version, current Stage/Phase/Task, capability count,
blockers, next Gate, and next unique task. Capabilities include value, scope,
non-scope, implementation refs, test refs, evidence, limitations, and current
status.

`docs/governance/templates/功能清单.template.md` is the template for that
human view. It starts with summary fields, then owner decisions, capability
overview, evidence, limitations, and feature detail. It must not degrade into a
link page.

`开发记录.md` first screen: version, current Stage/Phase/Task, total and completed
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

`模型参数文件.md` records active models, assumptions, inputs, outputs, formulas or
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

## Canonical, Evidence, And Artifact Retention

`governance/artifact_policy.json` is the machine-readable root contract for
canonical resources, derived views, compact receipts, retained legacy evidence,
and transient CI/local artifacts. Its schema is
`governance/schemas/artifact_policy.schema.json`; its read-only validator and
deterministic renderer are exposed through `scripts/lean_governance.py` as
`artifact-audit`, `artifact-render`, and `artifact-check-render`.

The boundary is fail-closed:

- Each editable canonical fact domain has one path and one named writer.
  Duplicate domains or a resource classified as both canonical and derived fail.
- Derived human views name their canonical sources and set
  `editable_fact_source=false`. Root and project human entries remain directly
  readable and cannot degrade into link-only pages.
- New Task evidence is an append-only `governance/run_manifests/TSK-*.json`
  compact receipt. It stores commands, outcomes, hashes, commit/CI pointers, and
  essential owner decisions; it cannot embed raw stdout/stderr, transcripts, or
  full logs and cannot exceed the policy byte limit.
- Full Actions output, generated reports, and large/raw evidence use runner temp
  or ignored local artifact directories. They are short-lived artifacts, not Git
  governance truth. New tracked full-log filenames fail the changed-scope audit.
- Historical non-`TSK-` run manifests, tracked CI attestations, review bundles,
  and stage-gate files are read-only compatibility collections with an owner,
  retention reason, count, bytes, and aggregate SHA-256. A normal Task cannot
  add, edit, or delete them. An owner-authorized migration must update the policy
  and prove reference safety before changing their disposition.
- Task Pack schemas/specifications remain owned source contracts. A Task Pack or
  legacy reader may consume preserved evidence, but it cannot dual-write a second
  editable governance source.

The Project Governance workflow runs the artifact audit before other governance
checks. Scheduled/full runs verify the current locked collections; PR/push runs
also compare the changed paths with the base commit. The renderer writes only to
stdout, and `artifact-check-render` proves two identical renders plus zero
repository write delta.

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
target-project human files. CI and Hook must not write root generated views
back into tracked source; manual or scheduled root view generation writes to a
temporary artifact directory through `--root-artifact-dir`.

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

## Automation C And Zero-Open

At rest, root governance requires open PR / open Issue / non-main branch =
`0 / 0 / 0`. Agent runtime never uses an Issue as a lock, queue, audit log,
failure state, or completion record.

One external authenticated publisher may create one same-repository, non-draft
temporary PR. `Project Governance` is the read-only required CI role and runs on
every PR without `paths` filters. The trusted default-branch Settlement/Janitor
uses live APIs only: it does not checkout or execute PR code and does not read
PR artifacts or caches. Success requires authorized actor, base `main`, exact
tested head/base, successful required check, and mergeability before squash
merge and exact-ref deletion. All terminal failures close the PR and delete only
the exact unchanged transaction ref; unknown refs are never deleted.

The Settlement-installation PR is the one bootstrap manual/native auto-merge
exception. A local-only implementation may report
`REMOTE_ACTIVATION_DEFERRED`, but it must not claim required-check enforcement,
production acceptance, or final `0/0/0` until live evidence exists.

## Changed-Scope CI And Hook

Every pull request runs one required Project Governance job focused on
`lean_governance.py ci --changed-only` against the PR base. Pushes to `main`
run the same contract against the previous main commit. Manual
`scope=changed-only` accepts an optional `base_ref`.

Scheduled and manual `scope=all` runs execute full information-quality,
all-project semantic/drift validation, generated-view determinism checks, and CI
attestation upload.

The Stop Hook is advisory only. It may suggest commands, but it must not run
subprocesses, inspect git state, detect changed files, run generators,
validators, setup doctor, semantic extraction, receipt writing, attestation, or
recursive repair loops.

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

`projects` contains active projects only. A retired project remains discoverable
without participating in active validation, dashboards, information quality, semantic
checks, or root changed-scope fanout by moving to `retired_projects` with this
fail-closed contract:

```text
project_id, path, status=retired, retired_at, retirement_reason,
preserve_history=true, reactivation_requires_owner_authorization=true, evidence_refs
```

Active and retired IDs and paths must be disjoint. Retired entries must not carry
`ci_mode` or `migration`. Their tracked history stays in place; changing a retired
path fails with `RETIRED_PROJECT_CHANGE` until an explicit Owner-authorized
reactivation task first restores it to `projects`.

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

Lean validator commands remain:

```bash
python scripts/lean_governance.py validate --all
python scripts/lean_governance.py validate --project <project_id>
python scripts/lean_governance.py ci --changed-only --base-ref <base_ref>
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

## Workflow Security And Supply Chain

`governance/workflow_policy.json` is the canonical root-workflow inventory. It
binds every active workflow to one owner, unique role, trigger set, exact
permissions, job topology, trust boundary, failure behavior, and local
dependencies. `docs/governance/WORKFLOW_ROLE_MATRIX.md` is its deterministic
human-readable view; nested project `.github/workflows` directories are invalid.

All third-party Actions must use a policy-allowlisted 40-character commit SHA.
Workflow permissions default to explicit read-only scope, every job has a finite
timeout, and every workflow has concurrency behavior. Untrusted dispatch, branch,
PR title, and PR body values may enter a shell only through environment variables.
Prompt-bearing jobs must use a read-only sandbox and disable checkout credential
persistence. The sole Settlement role runs trusted default-branch code against
live APIs only and must never check out PR code or consume PR artifacts/caches.

Run the fail-closed checks with:

```bash
python3 scripts/workflow_security_audit.py audit
python3 scripts/workflow_security_audit.py check-render
```

The repository acceptance counters are zero unowned workflows, zero duplicate
roles, exactly one Transaction CI role, exactly one Settlement role, zero nested
workflows, zero unpinned or unapproved Actions, zero permission drift, and zero
untrusted-context or high-privilege-boundary violations.

## Repository Hygiene And Large Objects

`governance/repository_hygiene_policy.json` is the canonical large-object,
archive, runtime-noise, and backup-producer contract. Regular new tracked blobs
must not exceed 1 MiB. A retained large/archive object must match exactly one
baseline-OID-only rule with owner, purpose, consumer, retention, recovery, and
confidentiality metadata. New or modified archives, Git bundles, WAL/SHM,
caches, build outputs, and whole-repository backup producers fail closed.

Run `python3 -B scripts/repository_hygiene_audit.py --root .`; after staging,
pass `--tree-ish "$(git write-tree)"` to bind the check to the exact candidate
tree. See `docs/governance/REPOSITORY_HYGIENE.md` for the function list,
parameters, LFS/Release decision, rollback, and deferred history-rewrite gates.

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

# IDS v0.1 STAGE-009 Phase 1 Scope Boundary

## Identity

- Stage: `STAGE-009`
- Phase: `Phase 1`
- Task ID: `IDS-V0_1-STAGE009-P1`
- Acceptance ID: `ACC-STAGE-009`
- Stage title: `存储预算基线`
- Recorded at UTC: `2026-07-02T08:58:29Z`

## Goal

Confirm the storage-budget baseline before implementing any budget reducer,
waterline checker, worker guard, output quota, report cap, or UI budget slice.

This phase records evidence and engineering contracts only. It does not start
Docker services, install dependencies, write to `IDS_DATA_ROOT`, enumerate
external-drive contents, create `00-99` directories, generate reports,
generate embeddings, create indexes, create runtime data, or enter Phase 2.

Marker: `STAGE009_PHASE1_STORAGE_BUDGET_BOUNDARY_NO_IMPLEMENTATION_NO_PHASE2`.

## Read-Only Local Baseline

Read-only commands run for this phase:

| Check | Result |
|---|---|
| `sw_vers` | `ProductVersion: 15.1`, `BuildVersion: 24B83` |
| `uname -m` | `arm64` |
| `sysctl -n machdep.cpu.brand_string` | `Apple M2 Max` |
| `docker --version` | `Docker version 29.6.1, build 8900f1d` |
| `docker compose version` | `Docker Compose version v5.1.4` |
| `df -h /` | root filesystem `926Gi` size, `15Gi` used, `630Gi` available |
| `printenv IDS_DATA_ROOT` | no value configured in this shell |
| `check_environment_baseline.py --ids-data-root '' --internal-total-gib 1000 --internal-free-gib 300` | `IDS_DATA_ROOT state=NOT_CONFIGURED`, internal storage `state=OK`, `free_gib=300.0`, `min_free_gib=100`, `warn_free_gib=200`, `max_used_percent=85`, `does_not_start_services=true`, `does_not_create_ids_data_root=true` |
| `check_removable_drive_state.py --ids-data-root '' --storage-total-gib 1000 --storage-free-gib 300` | `state=NOT_CONFIGURED`, `safe_mode=true`, `resume_allowed=false`, `auto_resume=false`, `customer_visible=false`, `storage_state=OK` |

These checks prove only that the current shell can see local platform facts and
existing STAGE-006/STAGE-008 storage/root behavior. They do not prove Docker
Desktop is running, do not start containers, and do not inspect any external
drive.

## Storage Responsibility Split

| Area | Owner | Allowed In Phase 1 | Forbidden In Phase 1 |
|---|---|---|---|
| Internal disk hot data | IDS local runtime and development loop | Code, governance docs, small fixtures, small config, local environment facts, synthetic storage-budget evidence, budget contracts | Unbounded OCR output, embeddings, indexes, report batches, raw-material copies, dependency installs, runtime databases, generated data |
| External cold data | `IDS_DATA_ROOT` on 5TB external drive | Contract-only references and future budget categories | Creating, listing recursively, moving, deleting, scanning content, mutating external-drive contents, or guessing the root path |
| GitHub metadata | `LinzeColin/CodexProject` / `KM_IDSystem/` | Code, schemas, manifest templates, governance evidence, small fixtures | Real raw materials, local runtime data, secrets, large generated outputs |

## Budget Boundary

Future implementation must treat storage budget as a deterministic preflight
and runtime guard, not as a best-effort warning. Internal disk pressure must
block unbounded derived output before OCR, Embedding, indexing, cleanup, or
batch report work starts.

Phase 2 may implement only read-only budget checks:

- normalize configured storage roles without creating directories;
- consume STAGE-006 internal storage state and STAGE-008 removable-drive state;
- classify current storage budget state;
- emit allowed actions and required operator action;
- block unbounded derived output when free space or used-percent waterlines are
  unsafe;
- refuse recursive external-drive content scans in the budget preflight.

The budget guard must not open raw files, calculate file hashes, generate
manifests, import documents, run OCR, run Embedding, build indexes, clean
temporary files, write audit/report outputs, or modify external-drive content.
Those belong to later stages.

## Future Budget State Contract

Phase 1 defines the state names that later phases may implement:

| State | Meaning | Required behavior |
|---|---|---|
| `BUDGET_OK` | Internal storage has enough free space and is below high-waterline. | Allow later bounded preflight only; do not start data-moving work automatically. |
| `BUDGET_WARN` | Internal storage is above hard minimum but below warning free-space threshold. | Keep operations visible; require operator awareness before large derived jobs. |
| `BUDGET_BLOCKED_LOW_FREE` | Free space is below hard minimum. | Enter safe mode and block derived outputs and batch jobs. |
| `BUDGET_BLOCKED_HIGH_WATERLINE` | Used-percent exceeds configured maximum. | Enter safe mode and block derived outputs and batch jobs. |
| `BUDGET_UNKNOWN` | Storage state cannot be classified from available checks. | Fail closed; do not start data-moving work. |
| `EXTERNAL_ROOT_NOT_READY` | `IDS_DATA_ROOT` is missing, offline, reconnected-needs-validation, path-changed, permission-denied, or structurally invalid. | Keep cold-data workflows disabled until STAGE-007/008 checks pass. |
| `UNBOUNDED_OUTPUT_RISK` | A planned job has no declared output budget or cap. | Stop the job before creating local output. |

STAGE-006 and STAGE-008 state names remain source evidence. STAGE-009 maps
them into a storage-budget state set for local-disk protection and derived
output control.

## Default Threshold Contract

Phase 1 keeps the existing conservative defaults until Phase 2 proves a better
configuration:

| Parameter | Default | Meaning |
|---|---:|---|
| `internal_min_free_gib` | `100` | Hard minimum free space before derived output is blocked. |
| `internal_warn_free_gib` | `200` | Warning threshold before large jobs require explicit review. |
| `internal_max_used_percent` | `85` | High-waterline used-percent cap. |
| `external_cold_root_nominal_tb` | `5` | Owner-provided nominal removable-drive size for raw/cold data. |
| `internal_budget_label_gb` | `800` | Owner-facing planning label from the STAGE-009 pursuing goal; current APFS root measurement may differ. |

The local `df -h /` evidence reports `926Gi` root filesystem size in this
shell. The owner-facing `800GB` label remains a conservative planning boundary,
not a measured filesystem claim.

## Safe-Mode Rules

Safe mode means the IDS operations entrance may still show status, small
metadata, and recovery instructions, but must not run data-moving work or
unbounded derived-output work.

Safe mode must pause or block:

- bulk source import;
- recursive directory scanning;
- raw-material cleanup;
- OCR jobs;
- Embedding jobs;
- index rebuilds over external cold data;
- batch report generation;
- any job without declared output budget or cleanup policy.

Safe mode may still allow:

- read-only configuration checks;
- top-level-only structure validation;
- storage-budget preview;
- small fixture tests;
- governance and configuration validation;
- operator-facing Chinese guidance;
- rollback or pause-state evidence capture.

## Allowed Phase 1 Outputs

Phase 1 may create or update only:

- this Phase 1 boundary document;
- `STAGE009_ENTRY_CONTRACT.md`;
- batch-lock, roadmap, and event-log governance records;
- rendered Chinese owner-entry files.

## Forbidden Phase 1 Actions

Phase 1 must not:

- start Docker Desktop, Docker Compose, backend, frontend, or workers;
- install Python, npm, Docker, or system dependencies;
- create `.venv/`, `frontend/node_modules/`, `frontend/dist/`, `data/`,
  `reports/`, `outputs/`, generated indexes, OCR outputs, or embeddings;
- create, list recursively, copy, move, delete, or mutate external
  `IDS_DATA_ROOT` contents;
- create missing `00-99` directories;
- automatically resume import, OCR, Embedding, indexing, cleanup, or report
  jobs after storage pressure clears;
- copy real raw materials into Git;
- add secrets, API keys, database passwords, or cloud credentials;
- alter backend/frontend runtime behavior;
- push to GitHub before the STAGE-001..010 batch is complete.

## Evidence And Validation Plan

Phase 1 validation is evidence-based:

- confirm P0 STAGE-009 taskpack SHA-256;
- confirm stage execution index maps STAGE-009 to `D02-S004` and
  `ACC-STAGE-009`;
- confirm read-only local environment facts;
- confirm STAGE-006 and STAGE-008 evidence provide the source storage/root
  states used by the STAGE-009 budget contract;
- run `check-render --project KM_IDSystem`;
- run a marker/JSONL/scope check after governance updates;
- run `git diff --check`;
- run full semantic validate only as a known sparse-worktree diagnostic and do
  not expand unrelated projects.

Phase 2 may implement a small read-only storage-budget slice only after this
boundary is committed.

## Final Validation Results

Fresh Phase 1 validation run in this worktree:

| Check | Result |
|---|---|
| P0 STAGE-009 taskpack SHA check | `490671d6372dd185fa829ce4a7ea05d25b6ae311feb92a986571cbdb2a567099` |
| stage execution index check | STAGE-009 maps to `D02-S004`, `ACC-STAGE-009`, and `stages/STAGE-009_存储预算基线.md` |
| STAGE-006 environment/storage smoke | `IDS_DATA_ROOT state=NOT_CONFIGURED`, internal storage `state=OK`, `free_gib=300.0`, `min_free_gib=100`, `warn_free_gib=200`, `max_used_percent=85`, `does_not_start_services=true`, `does_not_create_ids_data_root=true` |
| STAGE-008 removable-drive smoke | `state=NOT_CONFIGURED`, `safe_mode=true`, `resume_allowed=false`, `auto_resume=false`, `customer_visible=false`, `storage_state=OK`, `does_not_create_ids_data_root=true` |
| `check-render --project KM_IDSystem` | `drift_count=0`, `reference_issue_count=0` |
| STAGE-009 Phase 1 marker, scope, and JSONL check | marker, event ID, batch status, next gate, completed hours, and P0 hash found |
| `git diff --check` | passed |
| semantic governance validate | diagnostic-only failure: 28 known sparse-worktree/root errors for omitted root governance schema/test/hook/workflow files and unrelated registered projects |

## Review Notes

No STAGE-009 Phase 1 blocker was found. The only carried limitation is the
known sparse-worktree semantic governance diagnostic. Do not expand unrelated
projects to satisfy it.

## Rollback

Rollback Phase 1 by reverting the local `IDS-V0_1-STAGE009-P1` commit. Because
Phase 1 is governance/contract only, rollback does not require data cleanup,
schema rollback, Docker cleanup, service restart, dependency restoration,
report cleanup, runtime file restore, external-drive cleanup, or GitHub PR
cleanup.

## Decision

STAGE-009 Phase 1 is allowed to complete when this boundary, the entry
contract, the batch lock, the roadmap, and the event log all point to
`IDS-V0_1-STAGE009-P1`; upload remains blocked until the STAGE-001..010 batch
is complete, reviewed, and repaired.

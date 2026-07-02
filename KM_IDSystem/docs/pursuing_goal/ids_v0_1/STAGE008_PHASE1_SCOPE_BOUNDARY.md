# IDS v0.1 STAGE-008 Phase 1 Scope Boundary

## Identity

- Stage: `STAGE-008`
- Phase: `Phase 1`
- Task ID: `IDS-V0_1-STAGE008-P1`
- Acceptance ID: `ACC-STAGE-008`
- Stage title: `可拔插移动硬盘状态机`
- Recorded at UTC: `2026-07-02T08:22:01Z`

## Goal

Confirm the removable external-drive state-machine boundary before implementing
any state reducer, event handler, polling loop, worker resume logic, or UI
status slice.

This phase records evidence and engineering contracts only. It does not start
Docker services, install dependencies, write to `IDS_DATA_ROOT`, enumerate
external-drive contents, create `00-99` directories, create runtime data, or
enter Phase 2.

Marker: `STAGE008_PHASE1_STATE_MACHINE_BOUNDARY_NO_IMPLEMENTATION_NO_PHASE2`.

## Read-Only Local Baseline

Read-only commands run for this phase:

| Check | Result |
|---|---|
| `sw_vers` | `ProductVersion: 15.1`, `BuildVersion: 24B83` |
| `uname -m` | `arm64` |
| `sysctl -n machdep.cpu.brand_string` | `Apple M2 Max` |
| `docker --version` | `Docker version 29.6.1, build 8900f1d` |
| `docker compose version` | `Docker Compose version v5.1.4` |
| `df -h /` | root filesystem `926Gi` size, `15Gi` used, `758Gi` available |
| `printenv IDS_DATA_ROOT` | no value configured in this shell |
| `detect_ids_data_root.py --ids-data-root ''` | `state=NOT_CONFIGURED`, `safe_mode=true`, `customer_visible=false`, `does_not_create_ids_data_root=true`, `does_not_scan_recursively=true` |

These checks prove only that the current shell can see local platform facts and
the existing STAGE-007 detector behavior. They do not prove Docker Desktop is
running, do not start containers, and do not inspect any external drive.

## Storage Responsibility Split

| Area | Owner | Allowed In Phase 1 | Forbidden In Phase 1 |
|---|---|---|---|
| Internal disk hot data | IDS local runtime and development loop | Code, governance docs, small fixtures, small config, local environment facts, state-machine contracts | Unbounded derived files, raw-material copies, report/output generation, dependency installs |
| External cold data | `IDS_DATA_ROOT` on 5TB external drive | Contract-only references and future top-level validation rules | Creating, listing recursively, moving, deleting, scanning content, or mutating external-drive contents |
| GitHub metadata | `LinzeColin/CodexProject` / `KM_IDSystem/` | Code, schemas, manifest templates, governance evidence, small fixtures | Real raw materials, local runtime data, secrets, large generated outputs |

## State-Machine Boundary

Future implementation must treat removable-drive state as a deterministic
preflight state machine, not as ad hoc retries. Missing configuration, absent
mounts, path changes, permission failures, and storage pressure remain safe
mode until an explicit revalidation step passes.

Phase 2 may implement only read-only state-machine checks:

- normalize configured and expected paths without creating them;
- consume STAGE-006 environment/path/storage state and STAGE-007 root-structure
  state;
- classify current removable-drive state;
- emit allowed transitions and required operator action;
- block automatic resume after reconnect until path identity, permissions, and
  top-level structure are revalidated;
- refuse recursive content scans in the state-machine preflight.

The state machine must not open raw files, calculate file hashes, generate
manifests, import documents, run OCR, run Embedding, build indexes, clean
temporary files, write audit/report outputs, or modify external-drive content.
Those belong to later stages.

## Future State Contract

Phase 1 defines the state names that later phases may implement:

| State | Meaning | Required behavior |
|---|---|---|
| `NOT_CONFIGURED` | No explicit `IDS_DATA_ROOT` value exists. | Keep data workflows disabled; show setup guidance in IDS operations entrance. |
| `OFFLINE` | Expected removable drive/root is absent or unmounted. | Pause data-moving work and wait for reconnect or corrected path. |
| `ONLINE_VALIDATED` | Drive/root is present, readable, expected, and structurally valid. | Allow later bounded preflight checks; do not start import automatically. |
| `RECONNECTED_NEEDS_REVALIDATION` | Drive/root reappeared after a non-online state. | Stay in safe mode until path identity, permissions, and structure are revalidated. |
| `PATH_CHANGED` | Configured path differs from expected path. | Require operator confirmation; never resume automatically. |
| `PERMISSION_DENIED` | Root exists but cannot be read or searched safely. | Enter safe mode and request operator correction. |
| `STRUCTURE_INVALID` | STAGE-007 root detector reports missing, duplicate, malformed, or not-directory structure. | Enter safe mode; require operator repair or migration decision outside this state machine. |
| `STORAGE_BLOCKED` | Internal disk budget is below minimum or above high-waterline. | Block derived outputs and batch jobs until storage guard passes. |
| `UNKNOWN` | State cannot be classified from available checks. | Fail closed; do not start data-moving work. |

STAGE-006 and STAGE-007 state names remain source evidence. STAGE-008 maps
them into a smaller lifecycle state set for removable-drive pause/resume
behavior.

## Transition Contract

| Event | From | To | Resume allowed? |
|---|---|---|---|
| configuration missing | any | `NOT_CONFIGURED` | no |
| drive/root absent | any | `OFFLINE` | no |
| drive/root reappears after offline/absent/not configured/unknown | `OFFLINE`, `NOT_CONFIGURED`, `UNKNOWN` | `RECONNECTED_NEEDS_REVALIDATION` | no |
| path differs from expected path | any | `PATH_CHANGED` | no |
| permission check fails | any | `PERMISSION_DENIED` | no |
| root structure is missing, duplicate, malformed, or not a directory | any | `STRUCTURE_INVALID` | no |
| internal storage is blocked or unknown | any | `STORAGE_BLOCKED` | no |
| path, permission, structure, and storage checks all pass after explicit validation | safe-mode state | `ONLINE_VALIDATED` | only bounded later preflight; no automatic import |

The key invariant is that reconnect is not enough to resume work. Reconnect
only moves the system into a revalidation state.

## Safe-Mode Rules

Safe mode means the IDS operations entrance may still show status, small
metadata, and recovery instructions, but must not run data-moving work.

Safe mode must pause or block:

- bulk source import;
- recursive directory scanning;
- raw-material cleanup;
- OCR jobs;
- Embedding jobs;
- index rebuilds over external cold data;
- batch report generation that would create unbounded local output.

Safe mode may still allow:

- read-only configuration checks;
- top-level-only structure validation;
- state-machine transition preview;
- small fixture tests;
- governance and configuration validation;
- operator-facing Chinese guidance;
- rollback or pause-state evidence capture.

## Allowed Phase 1 Outputs

Phase 1 may create or update only:

- this Phase 1 boundary document;
- `STAGE008_ENTRY_CONTRACT.md`;
- batch-lock, roadmap, and event-log governance records;
- rendered Chinese owner-entry files.

## Forbidden Phase 1 Actions

Phase 1 must not:

- start Docker Desktop, Docker Compose, backend, frontend, or workers;
- install Python, npm, Docker, or system dependencies;
- create `.venv/`, `frontend/node_modules/`, `frontend/dist/`, `data/`,
  `reports/`, or `outputs/`;
- create, list recursively, copy, move, delete, or mutate external
  `IDS_DATA_ROOT` contents;
- create missing `00-99` directories;
- automatically resume import, OCR, Embedding, indexing, cleanup, or report
  jobs after reconnect;
- copy real raw materials into Git;
- add secrets, API keys, database passwords, or cloud credentials;
- alter backend/frontend runtime behavior;
- push to GitHub before the STAGE-001..010 batch is complete.

## Evidence And Validation Plan

Phase 1 validation is evidence-based:

- confirm P0 STAGE-008 taskpack SHA-256;
- confirm read-only local environment facts;
- confirm stage execution index maps STAGE-008 to `D02-S003` and
  `ACC-STAGE-008`;
- confirm STAGE-006 and STAGE-007 evidence provide the source states used by
  the STAGE-008 state-machine contract;
- run `check-render --project KM_IDSystem`;
- run a marker/JSONL/scope check after governance updates;
- run `git diff --check`;
- run full semantic validate only as a known sparse-worktree diagnostic and do
  not expand unrelated projects.

Phase 2 may implement a small read-only state-machine slice only after this
boundary is committed.

## Final Validation Results

Fresh Phase 1 validation run in this worktree:

| Check | Result |
|---|---|
| P0 STAGE-008 taskpack SHA check | `5cd56ca188c4e13215d08b0281a412c877e3e02209b2c00e4f3ff1c943f2d357` |
| stage execution index check | STAGE-008 maps to `D02-S003`, `ACC-STAGE-008`, and `stages/STAGE-008_可拔插移动硬盘状态机.md` |
| STAGE-007 detector regression unittest | `Ran 7 tests` / `OK` |
| STAGE-006 environment baseline regression unittest | `Ran 7 tests` / `OK` |
| STAGE-007 CLI smoke | `state=NOT_CONFIGURED`, `safe_mode=true`, `customer_visible=false`, `does_not_create_ids_data_root=true`, `does_not_scan_recursively=true` |
| `check-render --project KM_IDSystem` | `drift_count=0` |
| STAGE-008 Phase 1 marker, scope, and JSONL check | `stage008_phase1_marker_jsonl_scope_ok=True` |
| `git diff --check` | passed |
| semantic governance validate | diagnostic-only failure: 28 known sparse-worktree/root errors for omitted root governance schema/test/hook/workflow files and unrelated registered projects |

The failed `shasum` attempt in this run was traced to the local Perl
`C.UTF-8` locale problem. The accepted SHA evidence above uses Python standard
library `zipfile` and `hashlib` against the same P0 taskpack entry.

## Rollback

Rollback Phase 1 by reverting the local `IDS-V0_1-STAGE008-P1` commit. Because
Phase 1 is governance/contract only, rollback does not require data cleanup,
schema rollback, Docker cleanup, service restart, dependency restoration,
report cleanup, runtime file restore, external-drive cleanup, or GitHub PR
cleanup.

## Decision

STAGE-008 Phase 1 is allowed to complete when this boundary, the entry
contract, the batch lock, the roadmap, and the event log all point to
`IDS-V0_1-STAGE008-P1`; upload remains blocked until the STAGE-001..010 batch
is complete, reviewed, and repaired.

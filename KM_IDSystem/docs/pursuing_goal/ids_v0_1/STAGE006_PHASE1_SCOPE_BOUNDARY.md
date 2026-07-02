# IDS v0.1 STAGE-006 Phase 1 Scope Boundary

## Identity

- Stage: `STAGE-006`
- Phase: `Phase 1`
- Task ID: `IDS-V0_1-STAGE006-P1`
- Acceptance ID: `ACC-STAGE-006`
- Stage title: `macOS M2 Max Docker 基线`
- Recorded at UTC: `2026-07-02T07:12:45Z`

## Goal

Confirm the local environment and storage-root boundary for IDS v0.1 before
implementing any path detector, storage budget interface, or safe-mode runtime
logic.

This phase records evidence and engineering contracts only. It does not start
Docker services, install dependencies, write to `IDS_DATA_ROOT`, inspect
external-drive contents, create runtime data, or enter Phase 2.

Marker: `STAGE006_PHASE1_NO_DOCKER_START_NO_PHASE2`.

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

These checks prove that Docker CLI and Compose are visible in the local shell.
They do not prove Docker Desktop is currently running, do not start containers,
and do not validate service health.

## Storage Responsibility Split

| Area | Owner | Allowed In Phase 1 | Forbidden In Phase 1 |
|---|---|---|---|
| Internal disk hot data | IDS local runtime and development loop | Code, governance docs, small fixtures, small config, local environment facts | Unbounded derived files, raw-material copies, report/output generation, dependency installs |
| External cold data | `IDS_DATA_ROOT` on 5TB external drive | Contract-only references and future state definitions | Creating, moving, deleting, scanning, or mutating external-drive contents |
| GitHub metadata | `LinzeColin/CodexProject` / `KM_IDSystem/` | Code, schemas, manifest templates, governance evidence, small fixtures | Real raw materials, local runtime data, secrets, large generated outputs |

## Boundaries For macOS, Docker, And Paths

Phase 1 records these boundaries for later implementation:

- macOS baseline must remain local and operator-readable; it is not a customer
  workflow surface.
- Docker/Compose baseline is an IDS operations concern and should be exposed
  through diagnostics or health checks, not through report/customer copy.
- `IDS_DATA_ROOT` must be configurable and absent-safe. If missing, the system
  must fail closed into safe mode instead of creating a guessed large-data
  directory inside the repo.
- Internal disk usage must have a high-waterline budget before large imports,
  OCR, Embedding, or derived-report batches are allowed.
- External drive identity must be represented by path plus later fingerprint or
  manifest evidence; path string alone is not enough for future raw-material
  safety.

## Removable External Drive State Contract

Phase 1 defines the state names that later phases may implement:

| State | Meaning | Required operator behavior |
|---|---|---|
| `NOT_CONFIGURED` | No `IDS_DATA_ROOT` is configured. | Keep bulk data workflows disabled; show setup guidance in IDS operations entrance. |
| `ONLINE` | Configured path is present and readable. | Allow bounded checks; later stages may allow imports after preflight. |
| `OFFLINE` | Configured path is absent. | Pause bulk import, OCR, Embedding, and index rebuild work. |
| `RECONNECTED` | Previously absent path is present again. | Require revalidation before resuming paused jobs. |
| `PERMISSION_DENIED` | Path exists but cannot be read safely. | Enter safe mode and request operator correction. |
| `PATH_CHANGED` | Expected path changed or points to a different mount. | Do not resume automatically; require operator confirmation and later identity checks. |
| `UNKNOWN` | State cannot be classified from available checks. | Fail closed; do not start data-moving work. |

## Safe-Mode Rules

Safe mode means the IDS operations entrance may still show status, small
metadata, and recovery instructions, but must not run data-moving work.

Safe mode must pause or block:

- bulk source import;
- OCR jobs;
- Embedding jobs;
- index rebuilds over external cold data;
- batch report generation that would create unbounded local output;
- cleanup jobs that could delete or move raw materials.

Safe mode may still allow:

- read-only status checks;
- small fixture tests;
- governance and configuration validation;
- operator-facing Chinese guidance;
- rollback or pause-state evidence capture.

## Allowed Phase 1 Outputs

Phase 1 may create or update only:

- this Phase 1 boundary document;
- `STAGE006_ENTRY_CONTRACT.md`;
- batch-lock, roadmap, and event-log governance records;
- rendered Chinese owner-entry files.

## Forbidden Phase 1 Actions

Phase 1 must not:

- start Docker Desktop, Docker Compose, backend, frontend, or workers;
- install Python, npm, Docker, or system dependencies;
- create `.venv/`, `frontend/node_modules/`, `frontend/dist/`, `data/`,
  `reports/`, or `outputs/`;
- write to, enumerate, copy, move, or delete external `IDS_DATA_ROOT` contents;
- copy real raw materials into Git;
- add secrets, API keys, database passwords, or cloud credentials;
- alter backend/frontend runtime behavior;
- push to GitHub before the STAGE-001..010 batch is complete.

## Evidence And Validation Plan

Phase 1 validation is evidence-based:

- confirm P0 STAGE-006 taskpack SHA-256;
- confirm read-only local environment facts;
- confirm stage execution index maps STAGE-006 to `D02-S001` and
  `ACC-STAGE-006`;
- run `check-render --project KM_IDSystem`;
- run a marker/JSONL/scope check after governance updates;
- run `git diff --check`;
- run full semantic validate only as a known sparse-worktree diagnostic and do
  not expand unrelated projects.

Phase 2 may implement a small detector or contract slice only after this
boundary is committed.

## Rollback

Rollback Phase 1 by reverting the local `IDS-V0_1-STAGE006-P1` commit. Because
Phase 1 is governance/contract only, rollback does not require data cleanup,
schema rollback, Docker cleanup, service restart, dependency restoration,
report cleanup, runtime file restore, external-drive cleanup, or GitHub PR
cleanup.

## Decision

STAGE-006 Phase 1 is allowed to complete when this boundary, the entry
contract, the batch lock, the roadmap, and the event log all point to
`IDS-V0_1-STAGE006-P1`; upload remains blocked until the STAGE-001..010 batch
is complete, reviewed, and repaired.

# IDS v0.1 STAGE-007 Phase 1 Scope Boundary

## Identity

- Stage: `STAGE-007`
- Phase: `Phase 1`
- Task ID: `IDS-V0_1-STAGE007-P1`
- Acceptance ID: `ACC-STAGE-007`
- Stage title: `IDS_DATA_ROOT 检测`
- Recorded at UTC: `2026-07-02T07:45:36Z`

## Goal

Confirm the `IDS_DATA_ROOT` detector boundary before implementing any real path
detector or directory-structure validator.

This phase records evidence and engineering contracts only. It does not start
Docker services, install dependencies, write to `IDS_DATA_ROOT`, enumerate
external-drive contents, create `00-99` directories, create runtime data, or
enter Phase 2.

Marker: `STAGE007_PHASE1_NO_ROOT_SCAN_NO_DIRECTORY_CREATE_NO_PHASE2`.

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

These checks prove only that the current shell can see local platform and
Docker CLI facts. They do not prove Docker Desktop is running, do not start
containers, and do not inspect any external drive.

## Storage Responsibility Split

| Area | Owner | Allowed In Phase 1 | Forbidden In Phase 1 |
|---|---|---|---|
| Internal disk hot data | IDS local runtime and development loop | Code, governance docs, small fixtures, small config, local environment facts | Unbounded derived files, raw-material copies, report/output generation, dependency installs |
| External cold data | `IDS_DATA_ROOT` on 5TB external drive | Contract-only references and future top-level validation rules | Creating, listing recursively, moving, deleting, scanning content, or mutating external-drive contents |
| GitHub metadata | `LinzeColin/CodexProject` / `KM_IDSystem/` | Code, schemas, manifest templates, governance evidence, small fixtures | Real raw materials, local runtime data, secrets, large generated outputs |

## IDS_DATA_ROOT Detection Boundary

Future implementation must treat `IDS_DATA_ROOT` as explicit configuration, not
as a guessed local directory. Missing configuration remains safe mode.

Phase 2 may implement only read-only checks:

- normalize the configured path without creating it;
- confirm the root path exists and is a directory;
- confirm the root is readable/searchable;
- inspect immediate top-level directory names only;
- classify missing, duplicate, malformed, or permission-denied top-level
  structure states;
- refuse recursive content scans in the detector.

The detector must not open raw files, calculate file hashes, generate
manifests, import documents, run OCR, run Embedding, build indexes, clean
temporary files, or write audit/report outputs. Those belong to later stages.

## `00-99` Top-Level Directory Contract

For STAGE-007, a complete `IDS_DATA_ROOT` structure means the root has exactly
one immediate directory slot for every numeric prefix from `00` through `99`.

A slot is valid when the immediate child directory name is either exactly
`NN` or starts with `NN_`, where `NN` is a two-digit number. Examples:

- `00_ORIGINAL_RAW_DATA`
- `01_INBOX`
- `02_STAGING`
- `99_ARCHIVE`

The exact labels after `NN_` may be refined by later path-contract stages, but
the numeric slot contract is fixed in this stage:

- all slots `00` through `99` must be present;
- each numeric slot may appear only once;
- non-directory files do not satisfy a slot;
- duplicate directories such as `00` and `00_ORIGINAL_RAW_DATA` are invalid;
- `00_ORIGINAL_RAW_DATA` is a reserved raw-material slot and remains read-only;
- missing, duplicate, malformed, or permission-denied structures enter safe
  mode rather than auto-repair.

Phase 1 does not require a real drive to contain this structure. It defines the
contract for the Phase 2 validator.

## Future Detection States

Phase 1 defines the state names that later phases may implement:

| State | Meaning | Required operator behavior |
|---|---|---|
| `NOT_CONFIGURED` | No `IDS_DATA_ROOT` is configured. | Keep bulk data workflows disabled; show setup guidance in IDS operations entrance. |
| `ROOT_ABSENT` | Configured root path is absent. | Pause data-moving work and ask operator to reconnect or correct the path. |
| `ROOT_NOT_DIRECTORY` | Configured path exists but is not a directory. | Fail closed; require configuration correction. |
| `ROOT_PERMISSION_DENIED` | Root exists but cannot be read or searched safely. | Enter safe mode and request operator correction. |
| `STRUCTURE_COMPLETE` | All numeric top-level slots `00` through `99` are present exactly once. | Allow later bounded preflight checks; do not start import automatically. |
| `MISSING_NUMERIC_SLOTS` | One or more `00-99` slots are missing. | Enter safe mode; show missing slot list in operations entrance. |
| `DUPLICATE_NUMERIC_SLOT` | A numeric slot appears more than once. | Enter safe mode; require operator cleanup or explicit migration decision. |
| `MALFORMED_TOP_LEVEL_ENTRY` | A top-level entry cannot be mapped to a valid numeric slot. | Enter safe mode; require operator review. |
| `PATH_CHANGED` | Configured path differs from the expected path. | Do not resume automatically; require operator confirmation and later identity checks. |
| `UNKNOWN` | State cannot be classified from available checks. | Fail closed; do not start data-moving work. |

STAGE-006 states remain valid for external-drive availability. STAGE-007 adds
root-structure states.

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
- small fixture tests;
- governance and configuration validation;
- operator-facing Chinese guidance;
- rollback or pause-state evidence capture.

## Allowed Phase 1 Outputs

Phase 1 may create or update only:

- this Phase 1 boundary document;
- `STAGE007_ENTRY_CONTRACT.md`;
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
- copy real raw materials into Git;
- add secrets, API keys, database passwords, or cloud credentials;
- alter backend/frontend runtime behavior;
- push to GitHub before the STAGE-001..010 batch is complete.

## Evidence And Validation Plan

Phase 1 validation is evidence-based:

- confirm P0 STAGE-007 taskpack SHA-256;
- confirm read-only local environment facts;
- confirm stage execution index maps STAGE-007 to `D02-S002` and
  `ACC-STAGE-007`;
- run `check-render --project KM_IDSystem`;
- run a marker/JSONL/scope check after governance updates;
- run `git diff --check`;
- run full semantic validate only as a known sparse-worktree diagnostic and do
  not expand unrelated projects.

Phase 2 may implement a small read-only detector or contract slice only after
this boundary is committed.

## Rollback

Rollback Phase 1 by reverting the local `IDS-V0_1-STAGE007-P1` commit. Because
Phase 1 is governance/contract only, rollback does not require data cleanup,
schema rollback, Docker cleanup, service restart, dependency restoration,
report cleanup, runtime file restore, external-drive cleanup, or GitHub PR
cleanup.

## Decision

STAGE-007 Phase 1 is allowed to complete when this boundary, the entry
contract, the batch lock, the roadmap, and the event log all point to
`IDS-V0_1-STAGE007-P1`; upload remains blocked until the STAGE-001..010 batch
is complete, reviewed, and repaired.

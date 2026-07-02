# IDS v0.1 STAGE-011 Phase 1 Scope Boundary

## Identity

- Stage: `STAGE-011`
- Phase: `Phase 1`
- Task ID: `IDS-V0_1-STAGE011-P1`
- Acceptance ID: `ACC-STAGE-011`
- Stage title: `安全模式基线`
- Recorded at UTC: `2026-07-02T11:03:09Z`

## Goal

Confirm the safe-mode baseline before implementing any safe-mode reducer,
state enum, worker pause/resume hook, indexing failure handler, external API
budget guard, UI status slice, or runtime configuration.

This phase records evidence and engineering contracts only. It does not start
Docker services, install dependencies, write to `IDS_DATA_ROOT`, enumerate
external-drive contents, read or scan `/Users/linzezhang/Downloads/IDS_MetaData`,
generate reports, generate OCR output, create embeddings, create indexes,
write manifests, create runtime data, call external APIs, or enter Phase 2.

Marker: `STAGE011_PHASE1_SAFE_MODE_BOUNDARY_NO_IMPLEMENTATION_NO_PHASE2`.

## P0 Source Evidence

Read-only source check:

| Check | Result |
|---|---|
| P0 taskpack zip | `/Users/linzezhang/Downloads/RAG IDS/v0.1/IDS_Taskpack_v0_1_only_中文修订版.zip` |
| P0 taskpack zip SHA | `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3` |
| Stage file inside zip | `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-011_安全模式基线.md` |
| Stage file SHA-256 | `b4e568ee400a1bcfaa36d51123800fa1dd2d77cb5c24363a01765318b2300473` |
| Stage execution index | STAGE-011 maps to `D02-S006`, `ACC-STAGE-011`, and `stages/STAGE-011_安全模式基线.md` |

The stage source was read directly from the user-provided v0.1 taskpack zip
without extracting or copying it into the worktree. The first `shasum` attempt
was blocked by this shell's unsupported `C.UTF-8` locale; the final stage-file
SHA was computed with Python standard library `zipfile` and `hashlib`.

## Read-Only Local Baseline

Read-only commands run for this phase:

| Check | Result |
|---|---|
| `sw_vers` | `ProductVersion: 15.1`, `BuildVersion: 24B83` |
| `uname -m` | `arm64` |
| `sysctl -n machdep.cpu.brand_string` | `Apple M2 Max` |
| `docker --version` | `Docker version 29.6.1, build 8900f1d` |
| `docker compose version` | `Docker Compose version v5.1.4` |
| `df -h /` | root filesystem `926Gi` size, `15Gi` used, `579Gi` available |
| `printenv IDS_DATA_ROOT` | no value configured in this shell |
| `test -d /Users/linzezhang/Downloads/IDS_MetaData` | `IDS_METADATA_ROOT_EXISTS`; content not listed, read, hashed, opened, copied, modified, or deleted |
| `check_environment_baseline.py --ids-data-root '' --internal-total-gib 1000 --internal-free-gib 300` | `IDS_DATA_ROOT state=NOT_CONFIGURED`, internal storage `state=OK`, `free_gib=300.0`, `min_free_gib=100`, `warn_free_gib=200`, `max_used_percent=85`, `safe_mode=true`, `does_not_start_services=true`, `does_not_create_ids_data_root=true` |
| `detect_ids_data_root.py --ids-data-root ''` | `state=NOT_CONFIGURED`, `safe_mode=true`, `customer_visible=false`, `does_not_start_services=true`, `does_not_create_ids_data_root=true`, `does_not_scan_recursively=true` |
| `check_removable_drive_state.py --ids-data-root '' --storage-total-gib 1000 --storage-free-gib 300` | `state=NOT_CONFIGURED`, `safe_mode=true`, `resume_allowed=false`, `auto_resume=false`, `customer_visible=false`, `storage_state=OK`, `does_not_scan_external_drive_contents=true` |
| `check_storage_budget.py --internal-total-gib 1000 --internal-free-gib 300 --planned-output-gib 20 --job-kind bounded_preflight --no-require-external-root` | `state=BUDGET_OK`, `safe_mode=false`, `bounded_preflight_only=true`, `does_not_generate_outputs=true`, `does_not_write_runtime_data=true` |
| `check_local_path_contract.py` read-only preflight | `state=PATH_CONTRACT_OK`, `source_uri.path=/Users/linzezhang/Downloads/IDS_MetaData`, `does_not_open_source_files=true`, `does_not_hash_source_files=true`, `does_not_scan_recursively=true`, `does_not_write_manifests=true`, `does_not_generate_outputs=true`, `does_not_copy_backups=true` |

These checks prove only that the current shell can see local platform facts and
existing STAGE-006/007/008/009/010 safe-mode source evidence. They do not
prove Docker Desktop is running, do not start containers, do not inspect any
external drive, and do not read database content.

## Safe-Mode Responsibility Split

| Area | Owner | Allowed In Phase 1 | Forbidden In Phase 1 |
|---|---|---|---|
| Internal hot data | IDS local runtime and development loop | Code, governance docs, small config, read-only environment facts, safe-mode contracts | Runtime databases, generated reports, OCR output, embeddings, indexes, caches, dependency installs, unbounded derived files |
| External cold data | `IDS_DATA_ROOT` on removable storage | Contract-only references and future readiness states | Creating, repairing, recursively listing, scanning, moving, deleting, cleaning, or mutating external-drive contents |
| Raw metadata database | `/Users/linzezhang/Downloads/IDS_MetaData` | Path existence reference and read-only boundary record | Opening, dumping, listing, hashing, copying, modifying, deleting, moving, renaming, or committing raw database content |
| GitHub metadata | `LinzeColin/CodexProject` / `KM_IDSystem/` | Code, schemas, manifest templates, governance evidence, small tests/fixtures | Raw materials, raw database dumps, secrets, local runtime data, large generated outputs, fake business data |
| External API budget | Future API provider and quota state | Define safe-mode trigger and future budget-guard states | Calling external APIs, spending quota, committing keys, or fabricating API responses |
| IDS operations entrance | Machine-side operator view | Future status, pause reason, recovery instruction, and revalidation evidence | Exposing machine internals in customer operator flow or promising automatic recovery |

## Safe-Mode Trigger Boundary

Future implementation must treat safe mode as a fail-closed operating state,
not as a warning banner. Safe mode must pause data-moving, expensive, or
unbounded work before side effects occur.

Phase 2 may implement only read-only safe-mode checks:

- consume STAGE-006 local environment state;
- consume STAGE-007 `IDS_DATA_ROOT` state;
- consume STAGE-008 removable-drive lifecycle state;
- consume STAGE-009 storage-budget state;
- consume STAGE-010 local path contract state;
- accept future external API budget and indexing failure inputs without making
  provider calls;
- classify safe-mode state, paused workflows, operator actions, and revalidation
  requirements;
- refuse automatic resume when a removable-drive or storage block clears
  without explicit revalidation.

The safe-mode baseline must not open raw files, calculate raw file hashes,
generate manifests, import documents, run OCR, run Embedding, build indexes,
clean temporary files, write audit/report outputs, call external APIs, or
modify external-drive or raw metadata content. Those belong to later stages
only when explicitly authorized.

## Future Safe-Mode State Contract

Phase 1 defines the state names that later phases may implement:

| State | Meaning | Required behavior |
|---|---|---|
| `SAFE_MODE_CLEAR` | All required local path, root, storage, indexing, and API budget inputs are safe for bounded preflight. | Allow bounded preflight only; do not start data-moving work automatically. |
| `SAFE_MODE_ROOT_NOT_CONFIGURED` | `IDS_DATA_ROOT` is absent or not configured. | Pause cold-data workflows; require operator configuration. |
| `SAFE_MODE_DRIVE_OFFLINE` | Removable drive is absent or offline. | Pause import, OCR, Embedding, indexing, backup, manifest, and report jobs. |
| `SAFE_MODE_REVALIDATION_REQUIRED` | Removable drive was reconnected, path changed, or previous state is stale. | Require explicit revalidation before resume. |
| `SAFE_MODE_PERMISSION_DENIED` | Required path exists but cannot be accessed. | Fail closed and require operator permission repair. |
| `SAFE_MODE_STORAGE_BLOCKED` | Internal storage is below free-space or used-percent waterline, or planned output is unbounded. | Block derived output, OCR, Embedding, indexing, and batch report work. |
| `SAFE_MODE_PATH_BLOCKED` | Source URI, processed, backup, manifest, or report export path contract is unsafe. | Block file-moving and output work before side effects. |
| `SAFE_MODE_INDEX_FAILED` | Index build or rebuild failed or is stale/partial. | Pause dependent search/retrieval/report workflows until repair evidence exists. |
| `SAFE_MODE_API_BUDGET_EXCEEDED` | External API quota, budget, rate, or provider safety state is exhausted or unknown. | Pause external API calls and fall back to offline or no-op behavior. |
| `SAFE_MODE_UNKNOWN` | State cannot be classified from available evidence. | Fail closed; do not start data-moving, indexing, report, or API work. |

STAGE-006 through STAGE-010 state names remain source evidence. STAGE-011 maps
them into a safe-mode state set for local operation protection.

## Pause And Resume Rules

Safe mode must pause or block:

- bulk source import;
- recursive directory scanning;
- raw-material cleanup;
- raw metadata database reads, dumps, or mutation;
- OCR jobs;
- Embedding jobs;
- index builds and rebuilds;
- backup copying;
- manifest generation;
- report export and batch report generation;
- external API calls when budget, quota, provider, or key state is unsafe;
- any job without declared path, output budget, cleanup policy, or revalidation
  record.

Safe mode may still allow:

- read-only configuration checks;
- top-level-only structure validation;
- storage-budget preview;
- local path contract preview;
- safe-mode status preview;
- small structural tests that do not become IDS business data;
- governance and configuration validation;
- operator-facing Chinese guidance;
- rollback or pause-state evidence capture.

Resume is never automatic after removable-drive, path, storage, indexing, or
API-budget recovery. Resume requires a fresh preflight and explicit
operator-visible revalidation evidence.

## Allowed Phase 1 Outputs

Phase 1 may create or update only:

- this Phase 1 boundary document;
- `STAGE011_ENTRY_CONTRACT.md`;
- `BATCH011_020_UPLOAD_LOCK.yaml`;
- roadmap and event-log governance records;
- rendered Chinese owner-entry files.

## Forbidden Phase 1 Actions

Phase 1 must not:

- start Docker Desktop, Docker Compose, backend, frontend, workers, OCR,
  Embedding, indexing, report, backup, or API jobs;
- install Python, npm, Docker, or system dependencies;
- create `.venv/`, `frontend/node_modules/`, `frontend/dist/`, `data/`,
  `reports/`, `outputs/`, processed outputs, backup payloads, manifests,
  generated indexes, OCR outputs, embeddings, or runtime databases;
- create, list recursively, copy, move, delete, or mutate external
  `IDS_DATA_ROOT` contents;
- open, list, hash, dump, copy, move, delete, rename, normalize, or mutate
  `/Users/linzezhang/Downloads/IDS_MetaData`;
- create missing `00-99` directories;
- call external APIs or consume quota;
- automatically resume import, OCR, Embedding, indexing, cleanup, backup,
  manifest, report, or API work after a block clears;
- copy real raw materials into Git;
- create fake IDS business data, fake database rows, fake source documents, or
  fabricated evidence;
- add secrets, API keys, database passwords, or cloud credentials;
- alter backend/frontend runtime behavior;
- push to GitHub before STAGE-011..020 are complete, reviewed, and repaired.

## Evidence And Validation Plan

Phase 1 validation is evidence-based:

- confirm P0 STAGE-011 taskpack SHA-256;
- confirm stage execution index maps STAGE-011 to `D02-S006` and
  `ACC-STAGE-011`;
- confirm read-only local environment facts;
- confirm STAGE-006 through STAGE-010 evidence provide the source
  environment/root/drive/storage/path states used by the safe-mode contract;
- confirm `/Users/linzezhang/Downloads/IDS_MetaData` is recorded only as a
  read-only real data source boundary;
- run `check-render --project KM_IDSystem`;
- run a marker/JSONL/scope check after governance updates;
- run `git diff --check`;
- run full semantic validate only as a known sparse-worktree diagnostic and do
  not expand unrelated projects.

Phase 2 may implement a small read-only safe-mode baseline slice only after
this boundary is committed.

## Rollback

Rollback Phase 1 by reverting the local `IDS-V0_1-STAGE011-P1` commit. Because
Phase 1 is governance/contract only, rollback does not require data cleanup,
schema rollback, Docker cleanup, service restart, dependency restoration,
report cleanup, runtime file restore, external-drive cleanup, raw metadata
cleanup, API quota cleanup, or GitHub PR cleanup.

## Decision

STAGE-011 Phase 1 is allowed to complete when this boundary, the entry
contract, the `BATCH011_020_UPLOAD_LOCK.yaml`, the roadmap, and the event log
all point to `IDS-V0_1-STAGE011-P1`; upload remains blocked until the
STAGE-011..020 batch is complete, reviewed, and repaired.

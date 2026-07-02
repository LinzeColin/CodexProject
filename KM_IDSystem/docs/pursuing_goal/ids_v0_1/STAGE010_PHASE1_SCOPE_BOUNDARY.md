# IDS v0.1 STAGE-010 Phase 1 Scope Boundary

## Identity

- Stage: `STAGE-010`
- Phase: `Phase 1`
- Task ID: `IDS-V0_1-STAGE010-P1`
- Acceptance ID: `ACC-STAGE-010`
- Stage title: `本地路径合同`
- Recorded at UTC: `2026-07-02T09:38:35Z`

## Goal

Confirm the local path contract before implementing any path detector, path
normalizer, path state enum, manifest writer, processed-output location,
backup location, report export location, or UI path slice.

This phase records evidence and engineering contracts only. It does not start
Docker services, install dependencies, write to `IDS_DATA_ROOT`, enumerate
external-drive contents, create processed/backup/manifest/report directories,
generate reports, generate embeddings, create indexes, create runtime data, or
enter Phase 2.

Marker: `STAGE010_PHASE1_LOCAL_PATH_BOUNDARY_NO_IMPLEMENTATION_NO_PHASE2`.

## P0 Source Evidence

Read-only source check:

| Check | Result |
|---|---|
| P0 taskpack zip | `/Users/linzezhang/Downloads/RAG IDS/v0.1/IDS_Taskpack_v0_1_only_中文修订版.zip` |
| P0 taskpack zip SHA | `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3` |
| Stage file inside zip | `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-010_本地路径合同.md` |
| Stage file SHA-256 | `b459c6cac1b79be5a2904308236be2e41356adadfce9bf6a6f5febd27e3fa0a6` |
| Stage execution index | STAGE-010 maps to `D02-S005`, `ACC-STAGE-010`, and `stages/STAGE-010_本地路径合同.md` |

The stage source was read directly from the user-provided v0.1 taskpack zip
without extracting or copying it into the worktree.

## Read-Only Local Baseline

Read-only commands run for this phase:

| Check | Result |
|---|---|
| `sw_vers` | `ProductVersion: 15.1`, `BuildVersion: 24B83` |
| `uname -m` | `arm64` |
| `sysctl -n machdep.cpu.brand_string` | `Apple M2 Max` |
| `df -h /` | root filesystem `926Gi` size, `15Gi` used, `577Gi` available |
| `printenv IDS_DATA_ROOT` | no value configured in this shell |
| `check_environment_baseline.py --ids-data-root '' --internal-total-gib 1000 --internal-free-gib 300` | `IDS_DATA_ROOT state=NOT_CONFIGURED`, internal storage `state=OK`, `free_gib=300.0`, `min_free_gib=100`, `warn_free_gib=200`, `max_used_percent=85`, `does_not_start_services=true`, `does_not_create_ids_data_root=true` |
| `detect_ids_data_root.py --ids-data-root ''` | `state=NOT_CONFIGURED`, `safe_mode=true`, `customer_visible=false`, `does_not_start_services=true`, `does_not_create_ids_data_root=true`, `does_not_scan_recursively=true` |
| `check_removable_drive_state.py --ids-data-root '' --storage-total-gib 1000 --storage-free-gib 300` | `state=NOT_CONFIGURED`, `safe_mode=true`, `resume_allowed=false`, `auto_resume=false`, `customer_visible=false`, `storage_state=OK`, `does_not_scan_external_drive_contents=true` |
| `check_storage_budget.py --internal-total-gib 1000 --internal-free-gib 300 --planned-output-gib 20 --job-kind bounded_preflight --no-require-external-root` | `state=BUDGET_OK`, `safe_mode=false`, `bounded_preflight_only=true`, `customer_visible=false`, `does_not_generate_outputs=true`, `does_not_write_runtime_data=true` |

These checks prove only that the current shell can see local platform facts and
existing STAGE-006/007/008/009 environment, root, drive-state, and storage
budget contracts. They do not start containers, create directories, inspect raw
files, or verify a real external drive.

## Local Path Responsibility Split

| Path role | Owner | Allowed in Phase 1 | Forbidden in Phase 1 |
|---|---|---|---|
| `file:// source_uri` | Explicit local reference to source material | Define syntax, normalization, read-only policy, and later validation states | Opening raw files, hashing raw files, copying, moving, deleting, cleaning, or recursively scanning source material |
| processed path | Later bounded derived processing | Define contract and future guard requirements | Creating processed directories, writing transformed files, OCR output, embeddings, indexes, or caches |
| backup path | Later explicit backup workflow | Define contract and safe-mode dependency on external/root/storage checks | Creating backup payloads, copying raw material, cloud sync, or unbounded duplicate storage |
| manifest path | Small metadata and evidence descriptors | Define contract for small structured manifest metadata and separation from raw payloads | Writing manifest files, generating evidence ledgers, scanning raw data, or committing secrets |
| report export path | Later report delivery/export workflow | Define contract and budget guard dependency | Generating reports, ZIPs, PDFs, exports, or report batches |
| internal hot data | IDS local runtime and development loop | Code, governance docs, small fixtures, small config, path-contract evidence | Unbounded processed output, runtime databases, generated reports, dependency installs |
| external cold data | `IDS_DATA_ROOT` on 5TB external drive | Contract-only references and future role definitions | Creating, repairing, listing recursively, moving, deleting, scanning content, mutating external-drive contents |
| GitHub metadata | `LinzeColin/CodexProject` / `KM_IDSystem/` | Code, schemas, manifest templates, governance evidence, small fixtures | Real raw materials, local runtime data, secrets, large generated outputs |

## Path Contract Boundary

Future implementation must treat local path handling as deterministic
preflight validation, not as a side-effecting file operation.

Phase 2 may implement only read-only path contract checks:

- normalize `file:// source_uri` without opening or hashing raw files;
- classify source URI syntax and path availability from explicit input only;
- consume STAGE-007 `IDS_DATA_ROOT`, STAGE-008 removable-drive, and STAGE-009
  storage-budget states;
- classify processed, backup, manifest, and report export path states;
- emit allowed actions and required operator action;
- block unbounded processed, backup, manifest, or report output when path or
  budget prerequisites are unsafe;
- refuse recursive external-drive content scans in the path preflight.

The path contract must not open raw files, calculate file hashes, generate
manifests, import documents, run OCR, run Embedding, build indexes, clean
temporary files, write audit/report outputs, or modify external-drive content.
Those belong to later stages.

## Future Path State Contract

Phase 1 defines the state names that later phases may implement:

| State | Meaning | Required behavior |
|---|---|---|
| `PATH_CONTRACT_OK` | Source URI and local path roles are syntactically valid and all required storage/root prerequisites are clear. | Allow later bounded preflight only; do not start data-moving work automatically. |
| `SOURCE_URI_INVALID` | Source URI is missing, malformed, not absolute, not `file://`, or cannot be normalized. | Fail closed; require operator correction. |
| `SOURCE_PATH_NOT_READY` | Source path is absent, inaccessible, outside allowed local roots, or depends on an unvalidated removable drive. | Enter safe mode for data-moving work. |
| `PROCESSED_PATH_UNBOUNDED` | Processed path is missing a declared root, budget, cleanup policy, or safe-mode guard. | Block derived processing before output is created. |
| `BACKUP_PATH_UNSAFE` | Backup path would duplicate raw data into an unsafe, unbounded, or unvalidated location. | Block backup work before copying. |
| `MANIFEST_PATH_UNSAFE` | Manifest path would write secrets, raw payload, or unbounded evidence outside approved metadata locations. | Block manifest writes. |
| `REPORT_EXPORT_PATH_UNSAFE` | Report export path has no declared budget/cap or would write into an unsafe runtime/raw-data location. | Block report export before file generation. |
| `PATH_CONTRACT_UNKNOWN` | Path state cannot be classified from available checks. | Fail closed; do not start data-moving or report work. |

STAGE-007, STAGE-008, and STAGE-009 state names remain source evidence.
STAGE-010 maps them into path-contract states for local path protection,
manifest separation, backup safety, and report export control.

## Safe-Mode Rules

Safe mode means the IDS operations entrance may still show status, small
metadata, and recovery instructions, but must not run data-moving work,
unbounded derived-output work, backup work, manifest writes, or report export
work.

Safe mode must pause or block:

- bulk source import;
- recursive directory scanning;
- raw-material cleanup;
- OCR jobs;
- Embedding jobs;
- index rebuilds over external cold data;
- backup copying;
- manifest generation;
- report export and batch report generation;
- any job without declared path, output budget, or cleanup policy.

Safe mode may still allow:

- read-only configuration checks;
- top-level-only structure validation;
- storage-budget preview;
- local path contract preview;
- small fixture tests;
- governance and configuration validation;
- operator-facing Chinese guidance;
- rollback or pause-state evidence capture.

## Allowed Phase 1 Outputs

Phase 1 may create or update only:

- this Phase 1 boundary document;
- `STAGE010_ENTRY_CONTRACT.md`;
- batch-lock, roadmap, and event-log governance records;
- rendered Chinese owner-entry files.

## Forbidden Phase 1 Actions

Phase 1 must not:

- start Docker Desktop, Docker Compose, backend, frontend, or workers;
- install Python, npm, Docker, or system dependencies;
- create `.venv/`, `frontend/node_modules/`, `frontend/dist/`, `data/`,
  `reports/`, `outputs/`, processed outputs, backup payloads, manifests,
  generated indexes, OCR outputs, or embeddings;
- create, list recursively, copy, move, delete, or mutate external
  `IDS_DATA_ROOT` contents;
- create missing `00-99` directories;
- write or export reports, manifests, evidence ledgers, backups, or runtime
  files;
- automatically resume import, OCR, Embedding, indexing, cleanup, backup,
  manifest, or report jobs after a path/storage block clears;
- copy real raw materials into Git;
- add secrets, API keys, database passwords, or cloud credentials;
- alter backend/frontend runtime behavior;
- push to GitHub before the STAGE-001..010 batch is complete, reviewed, and
  repaired.

## Evidence And Validation Plan

Phase 1 validation is evidence-based:

- confirm P0 STAGE-010 taskpack SHA-256;
- confirm stage execution index maps STAGE-010 to `D02-S005` and
  `ACC-STAGE-010`;
- confirm read-only local environment facts;
- confirm STAGE-007, STAGE-008, and STAGE-009 evidence provide the source
  root/drive/storage states used by the STAGE-010 path contract;
- run `check-render --project KM_IDSystem`;
- run a marker/JSONL/scope check after governance updates;
- run `git diff --check`;
- run full semantic validate only as a known sparse-worktree diagnostic and do
  not expand unrelated projects.

Phase 2 may implement a small read-only local path contract slice only after
this boundary is committed.

## Rollback

Rollback Phase 1 by reverting the local `IDS-V0_1-STAGE010-P1` commit. Because
Phase 1 is governance/contract only, rollback does not require data cleanup,
schema rollback, Docker cleanup, service restart, dependency restoration,
report cleanup, runtime file restore, external-drive cleanup, or GitHub PR
cleanup.

## Decision

STAGE-010 Phase 1 is allowed to complete when this boundary, the entry
contract, the batch lock, the roadmap, and the event log all point to
`IDS-V0_1-STAGE010-P1`; upload remains blocked until the STAGE-001..010 batch
is complete, reviewed, and repaired.

# IDS v0.1 STAGE-018 Phase 1 Scope Boundary

## Identity

- Stage: `STAGE-018`
- Phase: `Phase 1`
- Task ID: `IDS-V0_1-STAGE018-P1`
- Acceptance ID: `ACC-STAGE-018`
- Stage title: `导入预检扫描器`
- Recorded at UTC: `2026-07-02T19:49:34Z`

## Goal

Define the import preflight scanner boundary before any directory scanner,
body parser, OCR, Embedding, index builder, actual import, database write,
manifest write, report write, or runtime output is implemented.

Marker: `STAGE018_PHASE1_IMPORT_PREFLIGHT_SCANNER_BOUNDARY_NO_IMPLEMENTATION_NO_PHASE2`.

## P0 Evidence

| Item | Value |
|---|---|
| P0 taskpack zip SHA-256 | `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3` |
| P0 stage file | `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-018_导入预检扫描器.md` |
| P0 stage file SHA-256 | `30ff34c2ac598a1b8a69d719af2781dbe4fa4b2314957ba2715c434f9a499ba8` |
| Stage index mapping | `STAGE-018,D04-S001,导入预检扫描器,v0.1,D04,ACC-STAGE-018` |

## Inherited Boundary From STAGE-012 Through STAGE-017

| Upstream stage | Inherited rule |
|---|---|
| `STAGE-012` | Original materials and raw metadata roots remain read-only. |
| `STAGE-013` | Source identity must be metadata-only and bounded by explicit source input. |
| `STAGE-014` | Manifest decisions are metadata-only until a later stage authorizes persistence. |
| `STAGE-015` | Duplicate/conflict classification preserves provenance and never deletes originals. |
| `STAGE-016` | Import idempotency prevents duplicate document/chunk/job/index/import side effects. |
| `STAGE-017` | Repeated scan, resume, and offline-drive recovery fail closed and keep all write deltas at zero unless a later gate authorizes writes. |

## Input Contract

Phase 1 defines these future inputs. It does not scan, enumerate, persist, or
backfill them.

| Field | Required meaning |
|---|---|
| `precheck_request_id` | future bounded request identity for an owner-approved preflight |
| `requested_root_uri` | future explicit local directory or file-set root chosen by a human owner |
| `source_scope` | `single_file`, `directory`, `selected_files`, `archive_candidate`, or `removable_drive` |
| `source_read_policy` | metadata-only; no body parsing, OCR, Embedding, indexing, import, or mutation |
| `owner_requested_at` | future timestamp when a human owner starts preflight |
| `drive_state` | online, offline, missing, blocked, or reconnected state for removable sources |
| `precheck_mode` | dry-run estimate only; no production import side effect |
| `confirmation_required` | always true before batch processing |

No Phase 1 artifact authorizes recursive discovery, raw metadata root
inspection, document body parsing, OCR, Embedding, indexing, import, report
generation, or persistence writes.

## Output Summary Contract

Phase 1 reserves these future output fields for Phase 2 implementation and
Phase 3 validation. They are not emitted as runtime records in this phase.

| Field | Required meaning |
|---|---|
| `file_count_estimate` | count of candidate files from approved metadata-only preflight |
| `total_size_bytes_estimate` | aggregate byte size estimate for candidate files |
| `format_counts` | extension or safe type-class counts without parsing body text |
| `archive_candidate_count` | count of files likely requiring archive handling |
| `scanned_document_candidate_count` | count of files likely requiring OCR based on safe metadata or type hints |
| `estimated_ocr_units` | rough future OCR workload estimate |
| `estimated_embedding_units` | rough future Embedding workload estimate |
| `risk_items` | explicit risks such as archive, large size, offline drive, unreadable path, or insufficient space |
| `cost_items` | estimated local compute, storage, OCR, Embedding, and operator review cost classes |
| `priority_hint` | future suggestion such as `low_risk_first`, `small_batch_first`, `manual_review_first`, or `blocked` |
| `confirmation_status` | owner decision status before any batch work |

## Risk Items

Phase 1 defines these risk categories for later implementation:

| Risk | Required behavior |
|---|---|
| `PREFLIGHT_SOURCE_NOT_CONFIGURED` | no approved input root or file set exists |
| `PREFLIGHT_SOURCE_BLOCKED` | source is unsafe, absent, unreadable, non-local, or raw metadata root |
| `PREFLIGHT_DRIVE_OFFLINE` | removable source is unavailable and must not be inferred |
| `PREFLIGHT_ARCHIVE_PRESENT` | archive handling may require a later security gate |
| `PREFLIGHT_SCANNED_DOCUMENT_PRESENT` | OCR work may be required; do not start OCR in preflight |
| `PREFLIGHT_LARGE_BATCH` | candidate count or byte size may need splitting |
| `PREFLIGHT_INSUFFICIENT_SPACE` | available workspace or target storage may not support later processing |
| `PREFLIGHT_UNSUPPORTED_FORMAT` | unsupported or unknown format requires skip or manual review |
| `PREFLIGHT_WRITE_BLOCKED` | proposed persistence/report/index/import write is outside the current gate |

## Cost Items

Cost estimates must be explicit uncertainty bands, not promises:

| Cost item | Meaning |
|---|---|
| `local_scan_time_class` | expected metadata-only preflight duration class |
| `storage_pressure_class` | estimated pressure from future derived artifacts |
| `ocr_workload_class` | expected OCR effort if later authorized |
| `embedding_workload_class` | expected Embedding effort if later authorized |
| `operator_review_class` | expected human review effort for risky files |
| `batch_split_hint` | future split guidance for high-risk or large imports |

## Confirmation States

| State | Meaning |
|---|---|
| `PREFLIGHT_NOT_CONFIGURED` | no approved source exists |
| `PREFLIGHT_READY` | metadata-only preflight estimate can be produced in a later phase |
| `PREFLIGHT_REVIEW_REQUIRED` | risk or cost requires owner review before import |
| `PREFLIGHT_OWNER_APPROVED` | future owner confirmation allows the next gated batch action |
| `PREFLIGHT_OWNER_CANCELLED` | owner cancels; no batch action may run |
| `PREFLIGHT_SPLIT_REQUIRED` | import must be split before any processing |
| `PREFLIGHT_SKIP_HIGH_RISK` | high-risk candidates must be skipped or separately reviewed |
| `PREFLIGHT_BLOCKED` | source, risk, policy, or storage condition blocks batch processing |

## Human Product Entrance Contract

The future preflight result shown in the human product entrance must:

- show counts, total size, format mix, archive count, scanned-document count,
  OCR/Embedding workload estimates, risk items, cost items, and confirmation
  state;
- use restrained enterprise wording and avoid production-ready claims;
- explain uncertainty in estimates;
- require an explicit owner action before any batch processing;
- provide cancel, split batch, skip high-risk, and review-later choices;
- never present fake business data or fabricated corpus examples.

## Phase 1 Allowed Outputs

- This scope-boundary document.
- The STAGE-018 entry contract.
- Stage005 governance-regression validator and unit-test updates that only
  accept the Phase 1 state.
- Roadmap, batch-lock, event-log, and rendered owner-file updates reflecting
  `IDS-V0_1-STAGE018-P1`.

## Phase 1 Forbidden Outputs

- No preflight scanner implementation, directory crawler, body parser, archive
  extractor, OCR, Embedding, index builder, importer, report writer, database
  adapter, or UI runtime implementation.
- No document, chunk, job, index, import, duplicate, evidence, audit, manifest,
  report, runtime database, cache, output, or backup writes.
- No service start, dependency install, external API call, GitHub push, PR,
  merge, app reinstall, or Phase 2 work.
- No read, list, hash, open, copy, move, delete, modify, dump, scan, or commit
  of `/Users/linzezhang/Downloads/IDS_MetaData` content.

## Validation Results

Final validation completed in this Phase 1 run:

- Stage005 RED failed as expected with `Ran 36 tests ... FAILED
  (failures=3)` because `IDS-V0_1-STAGE018-P1` was not yet accepted by the
  governance state machine and `STAGE018_*` evidence paths were not allowed.
- Stage005 intermediate RED failed as expected with `Ran 36 tests ... FAILED
  (failures=1)` because `STAGE018_ENTRY_CONTRACT.md` and
  `STAGE018_PHASE1_SCOPE_BOUNDARY.md` were missing as required evidence.
- Stage005 GREEN passed 36 tests.
- Stage005 validator returned `valid=true` with no issues, no missing required
  files, no event JSON errors, no forbidden changed paths, and no unexpected
  changed paths.
- Full IDS v0.1 pursuing-goal unittest discover passed 118 tests.
- `py_compile` passed for the Stage005 validator.
- events JSONL parsing returned `events_jsonl_ok`.
- bundled Python `render --project KM_IDSystem --write` updated the three
  Chinese owner files; bundled `check-render --project KM_IDSystem` returned
  `drift_count=0` and `reference_issue_count=0`.
- `git diff --check` passed.
- exact old underscored task-id variant scan returned no hits.
- Legacy path/name scan found only historical migration-policy, stale-path,
  do-not-revive, or scanner-rule references; this Phase 1 document does not
  add new legacy path literals.
- semantic validate remains diagnostic-only with 29 known sparse root-governance
  or registered-project missing paths and no new `KM_IDSystem` semantic error.
- Phase 1 did not read, list, hash, open, copy, move, delete, modify, dump,
  scan, or commit `/Users/linzezhang/Downloads/IDS_MetaData` content.
- No service start, dependency install, preflight scanner, directory crawler,
  body parser, OCR, Embedding, index builder, importer, report writer,
  database adapter, runtime output, external API call, GitHub upload, PR,
  merge, app reinstall, or Phase 2 work was performed.

## Owner Feedback Draft

STAGE-018 Phase 1 只定义“导入预检扫描器”应该看什么、输出什么、哪些风险和成本
必须提示、以及什么时候需要 owner 确认。当前不会扫描真实原始目录，不会打开正文，
不会解析文件内容，不会启动 OCR、Embedding、索引或批量导入，也不会写入 database、
manifest、document、chunk、job、report 或审计记录。

业务上可以把它理解为：未来导入前，系统先给出“文件数量、体积、格式、压缩包、
扫描件、预计处理工作量、风险、成本和优先级”的预估，再由 owner 决定继续、取消、
拆批或跳过高风险文件。

## Rollback

Revert the STAGE-018 Phase 1 documents, Stage005 validator/test updates,
batch-lock, roadmap/event, and rendered owner-file changes only. Do not touch
`00_ORIGINAL_RAW_DATA`, `/Users/linzezhang/Downloads/IDS_MetaData`, existing
manifests, evidence ledgers, audit logs, indexes, delivered reports, runtime
data, app entries, GitHub state, or Phase 2.

# IDS v0.1 STAGE-019 Phase 1 Scope Boundary

## Identity

- Stage: `STAGE-019`
- Phase: `Phase 1`
- Task ID: `IDS-V0_1-STAGE019-P1`
- Acceptance ID: `ACC-STAGE-019`
- Stage title: `导入风险估算器`
- Entrance: `人类产品入口 + IDS 系统运营入口`
- Recorded at UTC: `2026-07-02T20:38:56Z`

## Goal

Define the import risk estimator boundary before any directory scanner, body
parser, archive extractor, OCR, Embedding, index builder, actual import,
database write, manifest write, report write, runtime output, or risk-estimator
implementation is added.

Marker: `STAGE019_PHASE1_IMPORT_RISK_ESTIMATOR_BOUNDARY_NO_IMPLEMENTATION_NO_PHASE2`.

## P0 Evidence

| Item | Value |
|---|---|
| P0 taskpack zip SHA-256 | `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3` |
| P0 stage file | `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-019_导入风险估算器.md` |
| P0 stage file SHA-256 | `3b5d8fe9c7b542ea1264f2a8a53b4709fa9dcc73fe8eefed4ce1fe4849a39087` |
| Stage index mapping | `STAGE-019,D04-S002,导入风险估算器,v0.1,D04,ACC-STAGE-019` |

## Inherited Boundary From STAGE-012 Through STAGE-018

| Upstream stage | Inherited rule |
|---|---|
| `STAGE-012` | Original materials and raw metadata roots remain read-only. |
| `STAGE-013` | Source identity must be metadata-only and bounded by explicit source input. |
| `STAGE-014` | Manifest decisions are metadata-only until a later stage authorizes persistence. |
| `STAGE-015` | Duplicate/conflict classification preserves provenance and never deletes originals. |
| `STAGE-016` | Import idempotency prevents duplicate document/chunk/job/index/import side effects. |
| `STAGE-017` | Repeated scan, resume, and offline-drive recovery fail closed unless a later gate authorizes writes. |
| `STAGE-018` | Preflight scanner may estimate candidate shape but cannot authorize import, parsing, OCR, Embedding, index, report, manifest, database, evidence, or audit writes. |

## Input Contract

Phase 1 defines these future inputs. It does not scan, enumerate, persist,
backfill, or derive them from raw metadata content.

| Field | Required meaning |
|---|---|
| `risk_estimation_request_id` | future bounded request identity for an owner-approved risk estimate |
| `preflight_report_ref` | future reference to a metadata-only preflight report, not a production import artifact |
| `requested_root_uri` | future explicit local directory or file-set root chosen by a human owner |
| `candidate_file_metadata` | future safe metadata rows with path identity, size, extension, modified time, and source scope only |
| `storage_budget_snapshot` | future scalar free-space and expected derived-artifact budget, not a full disk audit |
| `source_scope` | `single_file`, `directory`, `selected_files`, `archive_candidate`, or `removable_drive` |
| `source_read_policy` | metadata-only; no body parsing, OCR, Embedding, indexing, import, report, or mutation |
| `owner_requested_at` | future timestamp when a human owner requests risk estimation |
| `risk_estimation_mode` | dry-run estimate only; no production import side effect |
| `confirmation_required` | always true before batch processing |

No Phase 1 artifact authorizes recursive discovery, raw metadata root
inspection, document body parsing, OCR, Embedding, indexing, import, report
generation, or persistence writes.

## Output Summary Contract

Phase 1 reserves these future output fields for Phase 2 implementation and
Phase 3 validation. They are not emitted as runtime records in this phase.

| Field | Required meaning |
|---|---|
| `high_risk_file_count` | count of candidates requiring owner review before processing |
| `oversized_file_count` | count of candidates exceeding future configured size limits |
| `suspicious_archive_count` | count of archive candidates needing later security or extraction policy |
| `unknown_format_count` | count of unsupported or unknown extensions/type hints |
| `insufficient_space_risk` | whether supplied storage budget may be insufficient |
| `risk_score_band` | future `low`, `medium`, `high`, or `blocked` risk band |
| `risk_items` | explicit risks such as high-risk file, oversized file, suspicious archive, unknown format, insufficient space, or blocked source |
| `cost_items` | estimated local compute, storage, OCR, Embedding, archive-review, and operator-review cost classes |
| `priority_hint` | future suggestion such as `low_risk_first`, `split_large_files`, `archive_review_first`, `skip_unknown_format`, or `blocked` |
| `confirmation_status` | owner decision status before any batch work |
| `uncertainty_items` | known estimation limits that must be shown to owner |

## Risk Items

Phase 1 defines these risk categories for later implementation:

| Risk | Required behavior |
|---|---|
| `RISK_SOURCE_NOT_CONFIGURED` | no approved input root or metadata report exists |
| `RISK_SOURCE_BLOCKED` | source is unsafe, absent, unreadable, non-local, or raw metadata root |
| `RISK_DRIVE_OFFLINE` | removable source is unavailable and must not be inferred |
| `RISK_HIGH_RISK_FILE_PRESENT` | candidate requires owner review before any processing |
| `RISK_OVERSIZED_FILE_PRESENT` | candidate size may require split, skip, or special handling |
| `RISK_SUSPICIOUS_ARCHIVE_PRESENT` | archive handling may require a later security gate |
| `RISK_UNKNOWN_FORMAT_PRESENT` | unsupported or unknown format requires skip or manual review |
| `RISK_INSUFFICIENT_SPACE` | available workspace or target storage may not support later processing |
| `RISK_WRITE_BLOCKED` | proposed persistence/report/index/import write is outside the current gate |

## Cost Items

Cost estimates must be explicit uncertainty bands, not promises:

| Cost item | Meaning |
|---|---|
| `local_metadata_review_class` | expected metadata-only risk-estimation duration class |
| `storage_pressure_class` | estimated pressure from future derived artifacts |
| `archive_review_class` | expected owner/security review effort for archive candidates |
| `ocr_workload_class` | expected OCR effort if later authorized |
| `embedding_workload_class` | expected Embedding effort if later authorized |
| `operator_review_class` | expected human review effort for risky files |
| `batch_split_hint` | future split guidance for high-risk or large imports |

## Confirmation States

| State | Meaning |
|---|---|
| `RISK_NOT_CONFIGURED` | no approved source or preflight reference exists |
| `RISK_READY` | metadata-only risk estimate can be produced in a later phase |
| `RISK_OWNER_REVIEW_REQUIRED` | risk or cost requires owner review before import |
| `RISK_OWNER_APPROVED` | future owner confirmation allows the next gated batch action |
| `RISK_OWNER_CANCELLED` | owner cancels; no batch action may run |
| `RISK_SPLIT_REQUIRED` | import must be split before any processing |
| `RISK_SKIP_HIGH_RISK` | high-risk candidates must be skipped or separately reviewed |
| `RISK_BLOCKED` | source, risk, policy, or storage condition blocks batch processing |

owner 确认后才进入批量处理. Until that confirmation exists, STAGE-019 may only
produce a dry-run risk estimate contract and owner-facing review choices.

## Human Product Entrance Contract

The future risk-estimator result shown in the human product entrance must:

- show high-risk file count, oversized file count, suspicious archive count,
  unknown format count, insufficient-space risk, risk score band, risk items,
  cost_items, priority hint, and confirmation state;
- use restrained enterprise wording and avoid production-ready claims;
- explain uncertainty in estimates;
- require an explicit owner action before any batch processing;
- provide cancel, split batch, skip high-risk, and review-later choices;
- never present fake business data, fake database rows, fabricated source
  documents, or fabricated corpus examples.

## Phase 1 Allowed Outputs

- This scope-boundary document.
- The STAGE-019 entry contract.
- Stage005 governance-regression validator and unit-test updates that only
  accept the Phase 1 state.
- A STAGE-019 focused test file covering the Phase 1 contract.
- Roadmap, batch-lock, event-log, and rendered owner-file updates reflecting
  `IDS-V0_1-STAGE019-P1`.

## Phase 1 Forbidden Outputs

- No risk estimator implementation, preflight scanner change, directory
  crawler, body parser, archive extractor, OCR, Embedding, index builder,
  importer, report writer, database adapter, or UI runtime implementation.
- No document, chunk, job, index, import, duplicate, evidence, audit, manifest,
  report, runtime database, cache, output, backup, or estimator-output writes.
- No service start, dependency install, external API call, GitHub push, PR,
  merge, app reinstall, or Phase 2 work.
- 不解析正文；不修改原始文件；不启动 OCR；不启动 Embedding；不建立索引；不启动实际导入。
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
  `/Users/linzezhang/Downloads/IDS_MetaData` 内容。
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档或伪造证据。

## Validation Results

Final validation completed in this Phase 1 run:

- Stage019 focused RED failed as expected with 3 failures because
  `STAGE019_ENTRY_CONTRACT.md` and `STAGE019_PHASE1_SCOPE_BOUNDARY.md` did not
  yet exist.
- Stage005 RED failed as expected with 40 tests and 5 failures because
  STAGE-019 changed paths and the `IDS-V0_1-STAGE019-P1` governance state were
  not yet accepted.
- Stage019 intermediate GREEN was delayed by a missing entrance field in the
  Phase 1 scope file; the field was added and the focused command then passed
  3 tests.
- Stage005 GREEN passed 40 tests.
- Stage005 validator returned `valid=true` with `issues=[]`,
  `missing_required_files=[]`, `missing_event_ids=[]`,
  `event_json_errors=[]`, `forbidden_changed_paths=[]`, and
  `unexpected_changed_paths=[]`.
- Full IDS v0.1 pursuing-goal unittest discover passed 135 tests.
- `py_compile` passed for the Stage005 validator and Stage019 focused test.
- events JSONL parsing returned `events_jsonl_ok`.
- bundled Python `render --project KM_IDSystem --write` updated the three
  Chinese owner files; bundled `check-render --project KM_IDSystem` returned
  `drift_count=0` and `reference_issue_count=0`.
- `git diff --check` passed.
- exact old underscored task-id variant scan returned no hits.
- legacy pre-rename path scan found only the existing roadmap stale-path policy
  line; this Phase 1 run did not add new active legacy project paths.
- semantic validate remains diagnostic-only with 29 known sparse
  root-governance or registered-project missing paths and no new
  `KM_IDSystem` semantic error.
- Phase 1 did not read, list, hash, open, copy, move, delete, modify, dump,
  scan, or commit `/Users/linzezhang/Downloads/IDS_MetaData` content.
- No risk estimator implementation, preflight scanner change, UI runtime
  change, screenshot, PDF, JSON output file, production report, runtime output,
  recursive scan, body parser, OCR, Embedding, index builder, importer, report
  writer, manifest/database/evidence/audit/runtime writer, document/chunk/job
  creation, service start, dependency install, external API call, GitHub
  upload, PR, merge, app reinstall, or Phase 2 work was performed.

## Owner Feedback Draft

STAGE-019 Phase 1 只定义“导入风险估算器”应该看哪些元信息、输出哪些风险和成本、
哪些状态需要 owner 再确认、以及为什么确认前不能批量处理。当前不会扫描真实原始目录，
不会打开正文，不会解析文件内容，不会启动 OCR、Embedding、索引或批量导入，也不会写入
database、manifest、document、chunk、job、report、evidence 或 audit。

业务上可以把它理解为：未来在导入前，系统先把高风险文件、超大文件、可疑压缩包、未知格式
和空间不足风险整理出来，再由 owner 决定继续、取消、拆批或跳过高风险文件。

## Rollback

Revert the STAGE-019 Phase 1 documents, Stage005 validator/test updates,
STAGE-019 focused tests, batch-lock, roadmap/event, and rendered owner-file
changes only. Do not touch `00_ORIGINAL_RAW_DATA`,
`/Users/linzezhang/Downloads/IDS_MetaData`, existing manifests, evidence
ledgers, audit logs, indexes, delivered reports, runtime data, app entries,
GitHub state, or Phase 2.

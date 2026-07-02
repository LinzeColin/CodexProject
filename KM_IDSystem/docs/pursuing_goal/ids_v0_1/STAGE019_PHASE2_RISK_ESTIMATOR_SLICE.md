# IDS v0.1 STAGE-019 Phase 2 Risk Estimator Slice

## Identity

- Stage: `STAGE-019`
- Phase: `Phase 2`
- Task ID: `IDS-V0_1-STAGE019-P2`
- Acceptance ID: `ACC-STAGE-019`
- Stage title: `导入风险估算器`
- Recorded at UTC: `2026-07-02T20:49:12Z`
- Marker: `STAGE019_PHASE2_RISK_ESTIMATOR_METADATA_ONLY_NO_PHASE3`

## Goal

Implement the smallest runnable import risk estimator slice using bounded
filesystem metadata only. The slice classifies proposed import candidates for
high-risk files, oversized files, suspicious archives, unknown formats, and
insufficient-space risk before any owner-approved batch processing.

## Delivered Slice

The Phase 2 helper is:

- `KM_IDSystem/scripts/check_import_risk_estimator.py`
- schema: `ids.stage019.import_risk_estimator.v1`
- task: `IDS-V0_1-STAGE019-P2`
- customer entrance: `human_product_entrance_payload`

The helper reuses the STAGE-018 metadata-only preflight helper as a safe input
source. It does not add a second scanner with broader access and does not
create runtime output files.

## Output Contract

The helper returns:

| Field | Meaning |
|---|---|
| `file_count_estimate` | candidate count from explicit `file://` metadata-only input |
| `format_counts` | extension-level counts without body parsing |
| `total_size_bytes_estimate` | aggregate candidate size estimate |
| `suspicious_archive_count` | archive candidates requiring later review |
| `scanned_document_candidate_count` | scanned/PDF/image candidates used only for OCR estimate |
| `estimated_ocr_units` | OCR workload estimate only; no OCR starts |
| `estimated_embedding_units` | Embedding workload estimate only; no Embedding starts |
| `oversized_file_count` | candidates above the configured dry-run size threshold |
| `unknown_format_count` | unsupported or unknown extension candidates |
| `insufficient_space_risk` | target-space risk based on supplied scalar free-space estimate |
| `risk_score_band` | `low`, `medium`, `high`, or `blocked` |
| `risk_items` | owner-visible risk categories |
| `cost_items` | metadata review, storage, archive, OCR, Embedding, operator-review and split classes |
| `priority_hint` | `blocked`, `archive_review_first`, `split_large_files`, `skip_unknown_format`, `manual_review_first`, or `low_risk_first` |
| `human_product_entrance_payload` | restrained Chinese owner-facing summary and owner action list |

## Human Product Entrance

`human_product_entrance_payload` includes:

- title: `导入风险估算器`;
- summary cards for file count, high-risk files, oversized files, suspicious
  archives, unknown formats, insufficient-space risk, and risk band;
- owner actions: cancel without side effects, split batch, skip high-risk, and
  review later;
- a confirmation-required message stating that parsing, OCR, Embedding, index,
  and import do not start before owner confirmation.

## Boundary

This slice:

- 不解析正文；
- 不修改原始文件；
- 不启动 OCR；
- 不启动 Embedding；
- 不建立索引；
- 不启动实际导入；
- 不写 manifest、database、document、chunk、job、evidence、audit、report、
  runtime output、cache、backup 或 estimator output file；
- 不安装依赖、不启动服务、不调用外部 API；
- 不进入 Phase 3，`NO_PHASE3`。

不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
`/Users/linzezhang/Downloads/IDS_MetaData` 内容。

## Real Data Policy

Focused tests use tracked governance documents as real local repository source
evidence and temporary process-owned structural files only for extension, size,
archive, scan, and unknown-format classification. Those structural files are
test harness state, not IDS business data, not raw database content, and not
production corpus evidence.

## Validation Results

Final validation completed in this Phase 2 run:

- Stage019 Phase2 RED failed as expected with 7 tests, 4 failures: the focused
  tests required `check_import_risk_estimator.py` and
  `STAGE019_PHASE2_RISK_ESTIMATOR_SLICE.md`, which did not yet exist.
- Stage005 Phase2 RED failed as expected with 41 tests, 2 failures because the
  Stage005 validator did not yet accept the Phase2 script path or
  `IDS-V0_1-STAGE019-P2` governance state.
- Stage019 focused GREEN passed 7 tests after adding the metadata-only risk
  estimator helper, CLI contract, and this evidence file.
- Stage005 intermediate RED failed as expected with 41 tests and 1 failure
  because the required Phase2 event was not yet recorded.
- Stage005 GREEN passed 41 tests after synchronizing batch lock, roadmap, and
  event log.
- Stage005 validator returned `valid=true` with `issues=[]`,
  `missing_required_files=[]`, `missing_event_ids=[]`,
  `event_json_errors=[]`, `forbidden_changed_paths=[]`, and
  `unexpected_changed_paths=[]`.
- Full IDS v0.1 pursuing-goal unittest discover passed 140 tests.
- `py_compile` passed for `check_import_risk_estimator.py`, the Stage005
  validator, and the Stage019 focused test.
- events JSONL parsing returned `events_jsonl_ok`.
- bundled Python `render --project KM_IDSystem --write` updated the three
  Chinese owner files; bundled `check-render --project KM_IDSystem` returned
  `drift_count=0` and `reference_issue_count=0`.
- `git diff --check` passed.
- exact old underscored task-id variant scan returned no hits.
- newly changed diff did not introduce legacy pre-rename project path spellings.
- semantic validate remains diagnostic-only with 29 known sparse
  root-governance or registered-project missing paths and no new
  `KM_IDSystem` semantic error.
- Phase 2 did not read, list, hash, open, copy, move, delete, modify, dump,
  scan, or commit `/Users/linzezhang/Downloads/IDS_MetaData` content.
- No UI runtime change, screenshot, PDF, JSON output file, production report,
  runtime output, recursive scan beyond the Stage018 safe preflight helper,
  body parser, OCR, Embedding, index builder, importer, report writer,
  manifest/database/evidence/audit/runtime writer, document/chunk/job creation,
  service start, dependency install, external API call, GitHub upload, PR,
  merge, app reinstall, or Phase 3 work was performed.

## Rollback

Revert `check_import_risk_estimator.py`, this evidence file, Stage019 focused
tests, Stage005 validator/test updates, batch-lock, roadmap/event, and rendered
owner-file changes only. Do not touch `00_ORIGINAL_RAW_DATA`,
`/Users/linzezhang/Downloads/IDS_MetaData`, runtime data, reports, outputs,
persisted manifests, evidence ledgers, audit logs, indexes, delivered reports,
app entries, GitHub state, or Phase 3.

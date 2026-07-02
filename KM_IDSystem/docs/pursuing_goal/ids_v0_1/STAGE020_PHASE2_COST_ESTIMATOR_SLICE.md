# IDS v0.1 STAGE-020 Phase 2 Cost Estimator Slice

## Task Identity
- Stage: `STAGE-020 · 导入成本估算器`
- Task: `IDS-V0_1-STAGE020-P2`
- Acceptance: `ACC-STAGE-020`
- Entrance: `人类产品入口 + IDS 系统运营入口`
- Implementation: `KM_IDSystem/scripts/check_import_cost_estimator.py`

## Implemented Slice
Phase 2 implements a metadata-only import cost estimator. It reuses the approved Stage 018 import preflight helper and Stage 019 import risk estimator helper, then adds the Stage 020 owner-facing cost fields:

- `file_count_estimate`
- `format_counts`
- `archive_candidate_count`
- `scanned_document_candidate_count`
- `unknown_format_count`
- `oversized_file_count`
- `embedding_token_estimate`
- `external_api_cost_estimate`
- `ocr_page_estimate`
- `index_size_estimate`
- `local_space_pressure`
- `cost_score_band`
- `risk_items`
- `cost_items`
- `priority_hint`
- `human_product_entrance_payload`

The helper exposes a CLI that prints JSON to stdout. It does not persist the result, does not write reports, does not create runtime files, and does not update any database.

## Estimation Method
All estimates are proxy estimates from metadata only:

- Embedding token estimate uses file-size metadata for embedding candidates and records `method: metadata_file_size_proxy_no_body_parse`.
- OCR page estimate uses scanned-document candidate count plus file-size metadata and records `method: metadata_scanned_candidate_count_and_size_proxy`.
- External API cost estimate multiplies metadata workload estimates by configured unit prices and records `method: configured_unit_price_times_metadata_workload_estimate`.
- Index size estimate multiplies embedding-token proxy by a configured `index_bytes_per_token`.
- Local space pressure compares estimated source bytes plus estimated index bytes with optional `available_space_bytes`.

The default values are conservative local configuration constants inside `check_import_cost_estimator.py`; they are not production provider prices and do not imply a real external API call.

## Human Product Entrance
`human_product_entrance_payload` is customer-visible and designed for `人类产品入口 + IDS 系统运营入口`. It exposes summary cards for file count, estimated Embedding token, estimated OCR pages, estimated external API cost, estimated index size, local-space pressure, and cost level. Supported owner actions are:

- `review_cost_before_import`
- `approve_cost_and_continue`
- `cancel_without_side_effects`

Owner confirmation remains mandatory before any batch processing.

## Raw Data Boundary
- The helper accepts explicit local `file://` source URIs only through the Stage 018 preflight helper.
- `/Users/linzezhang/Downloads/IDS_MetaData` is blocked before directory listing by the existing raw metadata boundary.
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- The helper must not read, list, hash, open, copy, move, delete, modify, dump, scan, or commit `/Users/linzezhang/Downloads/IDS_MetaData` content.
- Focused tests use tracked governance documents plus process-owned temporary structural files for extension/size classification only. They are not IDS corpus, database rows, business evidence, or committed user data.

## No Processing Or Persistence
- 不解析正文.
- 不启动 OCR.
- 不启动 Embedding.
- 不建立索引.
- 不启动实际导入.
- 不调用外部 API.
- 不写 manifest、database、evidence ledger、audit log、runtime data、reports、outputs、document/chunk/job/index/import row.
- 不生成 screenshot、PDF、JSON 输出文件或 production cost report.
- 不安装依赖、不启动服务、不执行 GitHub upload、PR、merge 或 app reinstall.
- `NO_PHASE3`: this run must not validate save/cancel/split/skip scenarios or enter Phase 3.

## Validation Plan
Final validation must include:

- RED/GREEN focused test for `KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage020_import_cost_estimator`.
- RED/GREEN Stage005 governance-regression state test for `IDS-V0_1-STAGE020-P2`.
- Stage005 validator report.
- Full IDS v0.1 pursuing-goal unittest discover.
- `py_compile` for the new helper and touched tests.
- events JSONL parse.
- owner render/check-render.
- `git diff --check`.
- exact old task-id spelling scan and legacy pre-rename path diff scan.
- semantic validate as sparse-worktree diagnostic only.

## Validation Results
Final validation completed in this Phase 2 run:

- Stage020 Phase2 RED failed as expected with 7 tests and 4 failures because
  `check_import_cost_estimator.py` and
  `STAGE020_PHASE2_COST_ESTIMATOR_SLICE.md` did not yet exist.
- Stage005 Phase2 RED failed as expected with 2 failures because
  `IDS-V0_1-STAGE020-P2` governance state and
  `check_import_cost_estimator.py` changed path were not yet accepted.
- Stage020 focused GREEN passed 7 tests after adding the metadata-only cost
  estimator helper, CLI contract, and this evidence file.
- Stage005 GREEN passed 45 tests.
- Stage005 validator returned `valid=true` with `issues=[]`,
  `missing_required_files=[]`, `missing_event_ids=[]`,
  `event_json_errors=[]`, `forbidden_changed_paths=[]`, and
  `unexpected_changed_paths=[]`.
- Full IDS v0.1 pursuing-goal unittest discover passed 157 tests.
- `py_compile` passed for `check_import_cost_estimator.py`, the Stage020
  focused test, the Stage005 validator, and the Stage005 regression test.
- events JSONL parsing returned `events_jsonl_ok count=91`.
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
- No Phase 3 scenario validation, save/cancel/split/skip workflow validation,
  UI runtime change, screenshot, PDF, JSON output file, production cost report,
  runtime output, body parser, OCR, Embedding, index builder, importer, report
  writer, manifest/database/evidence/audit/runtime writer,
  document/chunk/job creation, service start, dependency install, external API
  call, GitHub upload, PR, merge, or app reinstall was performed.

## Rollback
Revert `check_import_cost_estimator.py`, this evidence file, STAGE-020 focused tests, Stage005 validator/test updates, batch-lock, roadmap/event, and rendered owner-file changes only. Do not touch `/Users/linzezhang/Downloads/IDS_MetaData`, runtime data, reports, outputs, persisted manifests, evidence ledgers, audit logs, indexes, delivered reports, app entries, GitHub state, or Phase 3.

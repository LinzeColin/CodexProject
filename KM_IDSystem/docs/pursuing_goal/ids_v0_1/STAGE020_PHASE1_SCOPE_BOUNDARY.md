# IDS v0.1 STAGE-020 Phase 1 Scope Boundary

## Scope
- Stage: `STAGE-020 · 导入成本估算器`
- Task: `IDS-V0_1-STAGE020-P1`
- Acceptance: `ACC-STAGE-020`
- Entrance: `人类产品入口 + IDS 系统运营入口`
- Phase: `Phase 1 · 范围、输入输出与边界确认`

This phase defines the import cost estimator contract only. It prepares the field vocabulary, owner confirmation states, and no-processing boundary for estimating embedding token, external API, OCR, index, and local-space pressure before future batch processing.

## Inputs
Phase 1 defines these future metadata-only inputs:
- `cost_estimation_request_id`: stable request id for one owner-visible cost review.
- `input_directory_uri`: explicit owner-supplied local `file://` directory identity for import precheck; Phase 1 records the contract only and does not enumerate the directory.
- `input_directory_metadata`: approved directory-level metadata summary from preflight boundaries, not raw file body content.
- `candidate_file_metadata`: explicit metadata from approved preflight/risk-estimator boundaries, such as extension, byte size, high-level type flag, and already-approved counts.
- `storage_budget_snapshot`: owner-visible local disk budget and free-space pressure snapshot.
- `model_cost_policy_snapshot`: configured model/provider cost assumptions for future embedding and external API estimates.
- `ocr_policy_snapshot`: configured OCR page and scanned-document policy assumptions.
- `index_policy_snapshot`: configured index-size multiplier and retention assumptions.
- `owner_confirmation_context`: product entrance, operator, requested action, and pending confirmation state.

The input contract is metadata-only. It must not read raw database content from `/Users/linzezhang/Downloads/IDS_MetaData`; it must not recursively scan source roots; it must not parse body text.

## Outputs
Phase 1 defines these owner-facing output fields for future Phase 2:
- `output_summary`: compact owner-visible cost summary for the chosen input directory.
- `embedding_token_estimate`: estimated token workload range for embedding.
- `external_api_cost_estimate`: estimated external API cost range under configured provider assumptions.
- `ocr_page_estimate`: estimated OCR page workload range.
- `index_size_estimate`: estimated index storage footprint range.
- `local_space_pressure`: local machine storage pressure classification.
- `cost_score_band`: `LOW`, `MEDIUM`, `HIGH`, or `BLOCKED`.
- `cost_items`: structured list of token, API, OCR, index, and storage cost items.
- `risk_items`: structured list of cost blockers, uncertainty reasons, and missing metadata.
- `priority_hint`: owner-facing hint for import priority or split recommendation.
- `confirmation_status`: owner-visible confirmation state.
- `human_product_entrance_payload`: compact summary for `人类产品入口 + IDS 系统运营入口`.

## Confirmation States
- `COST_DRAFT`: cost summary is incomplete and cannot be approved.
- `COST_READY`: cost summary is complete enough for owner review.
- `COST_OWNER_REVIEW_REQUIRED`: owner must review cost, uncertainty, local-space pressure, and recommended action.
- `COST_OWNER_APPROVED`: owner explicitly approves moving to the next batch-processing gate.
- `COST_OWNER_REJECTED`: owner rejects the cost or pauses the import.
- `COST_BLOCKED`: missing metadata, local-space pressure, or policy conflict blocks the next phase.

Owner confirmation is mandatory: owner 确认后才进入批量处理.

## Raw Data And Processing Boundary
- 只读取元信息.
- 不解析正文.
- 不修改原始文件.
- 不启动 OCR.
- 不启动 Embedding.
- 不建立索引.
- 不启动实际导入.
- 不调用外部 API.
- 不写 manifest、database、evidence ledger、audit log、runtime data、reports、outputs、document/chunk/job/index/import row.
- 不生成 screenshot、PDF、JSON 输出文件或 production cost report.
- 不安装依赖、不启动服务、不执行 GitHub upload、PR、merge 或 app reinstall.
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档或伪造证据.
- `NO_PHASE2`: this run must not implement or exercise the cost estimator logic.

## Rollback
Revert only `IDS-V0_1-STAGE020-P1` entry/scope evidence, focused tests, batch-lock, roadmap/event, Stage005 governance-regression updates, and rendered owner files. Do not touch `/Users/linzezhang/Downloads/IDS_MetaData`, runtime data, reports, outputs, persisted manifests, evidence ledgers, audit logs, indexes, delivered reports, app entries, GitHub state, or Phase 2 artifacts.

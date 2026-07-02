# IDS v0.1 STAGE-021 Phase 1 Scope Boundary

## Scope
- Stage: `STAGE-021 · 预检确认 UI`
- Task: `IDS-V0_1-STAGE021-P1`
- Acceptance: `ACC-STAGE-021`
- Entrance: `人类产品入口 + IDS 系统运营入口`
- Phase: `Phase 1 · 范围、输入输出与边界确认`
- Recorded at UTC: `2026-07-02T22:43:25Z`

This phase defines the preflight confirmation UI contract only. It prepares the field vocabulary, confirmation states, owner decision boundaries, and no-processing rules for a later UI slice that can show preflight results and let the owner decide whether to continue, pause, split, or exclude items.

## P0 Source Evidence

| Check | Result |
|---|---|
| P0 taskpack zip | `/Users/linzezhang/Downloads/RAG IDS/v0.1/IDS_Taskpack_v0_1_only_中文修订版.zip` |
| P0 taskpack zip SHA | `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3` |
| Stage file inside zip | `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-021_预检确认UI.md` |
| Stage file SHA-256 | `2428711c7a935317de9bed7d50bbd02b7954ec7cdc5e1bfb832149a0c30103e8` |
| Stage execution index | STAGE-021 maps to `D04-S004`, `ACC-STAGE-021`, and `stages/STAGE-021_预检确认UI.md` |

The stage source was read directly from the user-provided v0.1 taskpack zip without extracting or copying the taskpack into the worktree.

## Inputs
Phase 1 defines these future metadata-only inputs:
- `preflight_confirmation_request_id`: stable request id for one owner-visible confirmation review.
- `input_directory_uri`: explicit owner-supplied local `file://` directory identity for preflight confirmation; Phase 1 records the contract only and does not enumerate the directory.
- `preflight_summary_snapshot`: approved metadata summary from STAGE-018 import preflight, such as file count, format count, size range, archive candidate count, scanned candidate count, and source readiness state.
- `risk_summary_snapshot`: approved metadata-only risk summary from STAGE-019, including high-risk counts, blocked reasons, unknown format counts, oversized counts, and risk score band.
- `cost_summary_snapshot`: approved metadata-only cost summary from STAGE-020, including OCR, Embedding, external API, index size, local-space pressure, and cost score band.
- `owner_confirmation_context`: product entrance, IDS operations entrance, operator identity label, requested action, pending confirmation state, and audit note.
- `excluded_item_metadata`: optional metadata-only list of items the owner chooses to exclude; it must not contain raw file contents or database rows.
- `batch_split_plan_metadata`: optional metadata-only split plan for future phased imports.

The input contract is metadata-only. It must not read raw database content from `/Users/linzezhang/Downloads/IDS_MetaData`; it must not recursively scan source roots; it must not parse body text.

## Outputs
Phase 1 defines these owner-facing output fields for future Phase 2:
- `output_summary`: compact owner-visible preflight confirmation summary for the chosen input directory.
- `risk_items`: structured list of owner-review risks, blockers, high-risk file classes, unknown formats, and local readiness gaps.
- `cost_items`: structured list of OCR, Embedding, external API, index, local-space, and operator-review cost items.
- `priority_hint`: owner-facing recommendation such as continue, pause, split batch, or exclude high-risk items.
- `confirmation_status`: owner-visible confirmation state.
- `owner_decision_options`: allowed owner actions: continue, pause, split, exclude, cancel, or review later.
- `excluded_items_summary`: metadata-only summary of excluded files or classes.
- `batch_split_summary`: metadata-only summary of future batch partitions.
- `human_product_entrance_payload`: restrained Chinese summary for `人类产品入口 + IDS 系统运营入口`.
- `ids_operations_entrance_payload`: machine-side status and audit hints for IDS operators.

## Confirmation States
- `PREFLIGHT_DRAFT`: preflight confirmation summary is incomplete and cannot be approved.
- `PREFLIGHT_READY`: preflight summary is complete enough for owner review.
- `PREFLIGHT_OWNER_REVIEW_REQUIRED`: owner must review risk, cost, priority, and readiness before any batch processing.
- `PREFLIGHT_OWNER_APPROVED_CONTINUE`: owner explicitly approves continuing to the next batch-processing gate.
- `PREFLIGHT_OWNER_PAUSED`: owner pauses the import without side effects.
- `PREFLIGHT_OWNER_SPLIT_BATCH`: owner chooses a metadata-only batch split plan before processing.
- `PREFLIGHT_OWNER_EXCLUDED_ITEMS`: owner excludes selected metadata-only candidates before processing.
- `PREFLIGHT_OWNER_CANCELLED`: owner cancels without processing.
- `PREFLIGHT_BLOCKED`: missing metadata, local-space pressure, risk block, cost block, or policy conflict blocks continuation.

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
- 不生成 runtime 输出、screenshot、PDF、JSON 输出文件或 production preflight report.
- 不安装依赖、不启动服务、不执行 GitHub upload、PR、merge 或 app reinstall.
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档或伪造证据.
- `NO_PHASE2`: this run must not implement or exercise the preflight confirmation UI.

## Rollback
Revert only `IDS-V0_1-STAGE021-P1` entry/scope evidence, focused tests, `BATCH021_030_UPLOAD_LOCK.yaml`, roadmap/event, Stage005 governance-regression updates, and rendered owner files. Do not touch `/Users/linzezhang/Downloads/IDS_MetaData`, runtime data, reports, outputs, persisted manifests, evidence ledgers, audit logs, indexes, delivered reports, app entries, GitHub state, or Phase 2 artifacts.

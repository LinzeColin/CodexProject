# IDS v0.1 STAGE-022 Phase 1 Scope Boundary

## Scope
- Stage: `STAGE-022 · 数据优先级队列`
- Task: `IDS-V0_1-STAGE022-P1`
- Acceptance: `ACC-STAGE-022`
- Entrance: `人类产品入口 + IDS 系统运营入口`
- Phase: `Phase 1 · 范围、输入输出与边界确认`
- Recorded at UTC: `2026-07-02T23:25:38Z`

This phase defines the data priority queue contract only. It prepares the field vocabulary, P0/P1/P2/P3 priority classes, confirmation states, owner decision boundary, and no-processing rules for a later implementation slice that can prioritize high-value engineering materials before batch processing.

## P0 Source Evidence

| Check | Result |
|---|---|
| P0 taskpack zip | `/Users/linzezhang/Downloads/RAG IDS/v0.1/IDS_Taskpack_v0_1_only_中文修订版.zip` |
| P0 taskpack zip SHA | `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3` |
| Stage file inside zip | `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-022_数据优先级队列.md` |
| Stage file SHA-256 | `4a1c62ec99fec7e267737bdd3306a2b568f06bf682b33b32ec66615bb2760c0b` |
| Stage execution index | STAGE-022 maps to `D04-S005`, `ACC-STAGE-022`, and `stages/STAGE-022_数据优先级队列.md` |

The stage source was read directly from the user-provided v0.1 taskpack zip without extracting or copying the taskpack into the worktree.

## Inputs
Phase 1 defines these future metadata-only inputs:
- `priority_queue_request_id`: stable request id for one owner-visible priority review.
- `input_directory_uri`: explicit owner-supplied local `file://` directory identity for priority review; Phase 1 records the contract only and does not enumerate the directory.
- `source_preflight_snapshot_ref`: immutable reference to an already approved metadata-only STAGE-018/021 preflight snapshot.
- `preflight_summary_snapshot`: approved metadata summary such as file count, format count, size range, archive candidate count, scanned candidate count, and readiness state.
- `risk_summary_snapshot`: approved metadata-only risk summary from STAGE-019, including high-risk counts, blocked reasons, unknown format counts, oversized counts, and risk score band.
- `cost_summary_snapshot`: approved metadata-only cost summary from STAGE-020, including OCR, Embedding, external API, index size, local-space pressure, and cost score band.
- `priority_signal_snapshot`: metadata-only signals used to classify priority, such as engineering-doc likelihood, accepted format family, owner-critical label, risk band, cost band, duplicate/conflict state, and local readiness.
- `owner_confirmation_context`: product entrance, IDS operations entrance, operator identity label, requested action, pending confirmation state, and audit note.

The input contract is metadata-only. It must not read raw database content from `/Users/linzezhang/Downloads/IDS_MetaData`; it must not recursively scan source roots; it must not parse body text.

## Outputs
Phase 1 defines these owner-facing output fields for future Phase 2:
- `priority_queue_summary`: compact owner-visible summary of the queue decision for the chosen input directory.
- `priority_buckets`: P0/P1/P2/P3 bucket summary with counts, risk/cost highlights, blocked items, and owner-review items.
- `priority_class`: one of the priority classes below.
- `priority_reason_codes`: metadata-only reason codes explaining why an item or group is P0, P1, P2, or P3.
- `defer_reason`: why an item is held for owner review or later processing.
- `owner_review_items`: metadata-only list of risks, cost spikes, unknown formats, oversized candidates, or local readiness gaps requiring owner decision.
- `confirmation_status`: owner-visible priority queue confirmation state.
- `human_product_entrance_payload`: restrained Chinese priority summary for `人类产品入口 + IDS 系统运营入口`.
- `ids_operations_entrance_payload`: machine-side status and audit hints for IDS operators.

## Priority Classes
- `P0_CRITICAL_ENGINEERING_DATA`: critical engineering packages, accepted drawings, specifications, diagnostic reports, work orders, repair plans, owner-marked urgent materials, and high-confidence data needed first. P0 still requires owner review before batch processing when risk or cost is high.
- `P1_HIGH_VALUE_ENGINEERING_DATA`: high-value engineering documents, equipment documentation, structured sheets, maintenance reports, and high-confidence reference materials that should run before general context.
- `P2_SUPPORTING_ENGINEERING_DATA`: supporting context, meeting notes, photos, secondary references, and lower-confidence but useful engineering-adjacent material.
- `P3_LOW_VALUE_OR_DEFERRED_DATA`: low-confidence, unknown-format, duplicate, noisy, oversized, high-risk, high-cost, offline, or deferred material that should wait for owner action or a later batch.

## Confirmation States
- `PRIORITY_QUEUE_DRAFT`: priority queue summary is incomplete and cannot be approved.
- `PRIORITY_QUEUE_READY`: metadata is sufficient for owner review.
- `PRIORITY_QUEUE_OWNER_REVIEW_REQUIRED`: owner must review risk, cost, priority, and readiness before batch processing.
- `PRIORITY_QUEUE_WAITING_OWNER_CONFIRMATION`: queue is ready but no owner confirmation has been recorded.
- `PRIORITY_QUEUE_OWNER_APPROVED`: owner explicitly approves the queue for the next batch-processing gate.
- `PRIORITY_QUEUE_PAUSED`: owner pauses the queue without side effects.
- `PRIORITY_QUEUE_BLOCKED`: missing metadata, raw-data boundary conflict, local-space pressure, high-risk item, cost block, or policy conflict blocks continuation.

Owner confirmation is mandatory: owner 确认后才进入批量处理.

## Risk, Cost, And Confirmation Rules
- High-risk archives, unknown formats, suspicious extensions, oversized candidates, scanned materials, insufficient space, and high OCR/Embedding/API/index estimates can downgrade an item to P3 or require `PRIORITY_QUEUE_OWNER_REVIEW_REQUIRED`.
- Priority is advisory until owner confirmation; it must not trigger parsing, OCR, Embedding, indexing, import, report generation, manifest writes, database writes, or queue execution.
- Future Phase 2 may compute priority suggestions only from approved metadata snapshots; this Phase 1 does not implement those computations.

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
- `NO_PHASE2`: this run must not implement or exercise the data priority queue.

## Rollback
Revert only `IDS-V0_1-STAGE022-P1` entry/scope evidence, focused tests, `BATCH021_030_UPLOAD_LOCK.yaml`, roadmap/event, Stage005 governance-regression updates, and rendered owner files. Do not touch `/Users/linzezhang/Downloads/IDS_MetaData`, runtime data, reports, outputs, persisted manifests, evidence ledgers, audit logs, indexes, delivered reports, app entries, GitHub state, or Phase 2 artifacts.

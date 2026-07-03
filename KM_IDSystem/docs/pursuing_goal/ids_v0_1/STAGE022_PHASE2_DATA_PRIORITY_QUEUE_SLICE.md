# IDS v0.1 STAGE-022 Phase 2 Data Priority Queue Slice

## Scope
- Stage: `STAGE-022 · 数据优先级队列`
- Task: `IDS-V0_1-STAGE022-P2`
- Acceptance: `ACC-STAGE-022`
- Entrance: `人类产品入口 + IDS 系统运营入口`
- Phase: `Phase 2 · 实现、接入与最小可运行切片`
- Recorded at UTC: `2026-07-02T23:40:12Z`

This phase implements a metadata-only data priority queue helper:
`KM_IDSystem/scripts/check_data_priority_queue.py`.

The helper composes existing STAGE-020 metadata-only cost estimates and assigns
P0/P1/P2/P3 priority buckets before any batch processing is allowed.

## Implemented Contract
- `evaluate_data_priority_queue(...)` returns schema `ids.stage022.data_priority_queue.v1`.
- It accepts explicit local `file://` source roots only through the inherited STAGE-018/019/020 metadata chain.
- It reports file count, format count, size estimate, archive candidates, scanned candidates, estimated OCR pages, estimated Embedding tokens, estimated external API cost, estimated index size, local-space pressure, risk items, cost items, and priority suggestions.
- It emits `priority_buckets` in order `P0`, `P1`, `P2`, `P3`.
- It emits `priority_queue_summary`, `human_product_entrance_payload`, `ids_operations_entrance_payload`, and `ui_component_contract`.
- The owner-facing component contract is `DataPriorityQueuePanel`.

## Priority Classes
- `P0_CRITICAL_ENGINEERING_DATA`: critical engineering documents with accepted metadata hints such as repair plan, drawing, specification, diagnostic report, work order, accepted engineering package, or owner-critical name hint.
- `P1_HIGH_VALUE_ENGINEERING_DATA`: high-value engineering documents and structured references in accepted engineering formats.
- `P2_SUPPORTING_ENGINEERING_DATA`: supporting context such as meeting notes, scanned pages, photos, reference notes, and engineering-adjacent materials.
- `P3_LOW_VALUE_OR_DEFERRED_DATA`: archive, unknown-format, oversized, low-confidence, or owner-review-required material.

## Owner-Facing Output
The `human_product_entrance_payload` includes:
- title: `数据优先级队列`
- summary cards for file count, P0/P1/P2/P3 counts, archive candidates, scanned candidates, OCR estimate, Embedding estimate, index estimate, and confirmation status.
- owner actions: `review_priority_queue`, `approve_priority_queue`, `pause_without_side_effects`, `split_batch`, `defer_p3_items`, and `cancel_without_side_effects`.
- priority hints such as `process_p0_first_with_owner_review`.

Owner confirmation remains mandatory: owner 确认后才进入批量处理.

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
- `NO_PHASE3`: this run must not execute scenario validation or owner decision persistence.

## Validation Evidence
- `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage022_data_priority_queue -q`
- `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage005_governance_regression.Stage005GovernanceRegressionTests.test_phase_state_allows_stage022_phase2_data_priority_queue_slice -q`
- `python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
- `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q`
- `check-render --project KM_IDSystem`

## Rollback
Revert `KM_IDSystem/scripts/check_data_priority_queue.py`,
`STAGE022_PHASE2_DATA_PRIORITY_QUEUE_SLICE.md`, focused tests, Stage005
validator/test updates, `BATCH021_030_UPLOAD_LOCK.yaml`, roadmap/event changes,
and rendered owner files. Do not touch `/Users/linzezhang/Downloads/IDS_MetaData`,
runtime data, reports, outputs, persisted manifests, evidence ledgers, audit
logs, indexes, app entries, GitHub state, or Phase 3 artifacts.

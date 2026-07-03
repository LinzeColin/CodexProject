# IDS v0.1 STAGE-022 Entry Contract

## Taskpack Identity
- Stage: `STAGE-022 · 数据优先级队列`
- Task: `IDS-V0_1-STAGE022-P1`
- Acceptance: `ACC-STAGE-022`
- Version: `v0.1`
- Domain: `D04 · 导入预检与数据优先级`
- Entrance: `人类产品入口 + IDS 系统运营入口`
- Pursuing goal: `建立 P0/P1/P2/P3 资料处理优先级，先处理高价值工程资料。`
- Phase scope: `Phase 1 · 范围、输入输出与边界确认`
- P0 taskpack file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-022_数据优先级队列.md`
- P0 stage file SHA-256:
  `4a1c62ec99fec7e267737bdd3306a2b568f06bf682b33b32ec66615bb2760c0b`

## Preconditions
- `STAGE-021` is locally complete, but `BATCH021_030_UPLOAD_LOCK.yaml` remains locked until `STAGE-021..030` all complete, are reviewed, and any review findings are repaired.
- `/Users/linzezhang/Downloads/IDS_MetaData` remains a path-only read-only real-data source boundary. This phase must not read, list, hash, open, copy, move, delete, modify, dump, scan, normalize, or commit raw database content.
- All IDS runtime corpus, database-backed content, analytics inputs, reports, indexes, manifests, and committed examples must use real user-approved data; fake IDS business data and fabricated evidence are forbidden.

## Phase 1 Contract
`IDS-V0_1-STAGE022-P1` defines the data priority queue boundary for later implementation. It records the metadata-only input directory identity, inherited preflight output summary, risk items, cost items, priority signal vocabulary, confirmation states, and no-processing rules required before the system can prioritize high-value engineering materials as P0/P1/P2/P3.

Phase 1 is a contract-only phase:
- It defines metadata-only priority queue inputs and owner-visible outputs for the human product entrance and IDS operations entrance.
- It binds preflight, risk, and cost snapshots from prior stages without re-reading raw source content.
- It defines P0/P1/P2/P3 processing priority vocabulary so future phases can route high-value engineering materials first.
- It confirms owner confirmation is mandatory: owner 确认后才进入批量处理.
- It preserves the raw data boundary: 只读取元信息, 不解析正文, 不修改原始文件.

## Explicit Non-Goals
- `NO_PHASE2`: do not implement the priority algorithm, UI component, backend endpoint, queue runner, persistence, scenario validation, screenshot, or runnable batch-processing workflow.
- Do not start OCR, Embedding, index building, import, report generation, external API calls, service start, dependency install, GitHub upload, PR, merge, or app reinstall.
- Do not create runtime data, reports, outputs, manifests, evidence ledgers, audit logs, document/chunk/job/index/import rows, screenshots, PDFs, JSON output files, or production preflight reports.
- Do not use fake IDS business data, fake database rows, fake source documents, or fabricated evidence.

## Acceptance Evidence
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_ENTRY_CONTRACT.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_PHASE1_SCOPE_BOUNDARY.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage022_data_priority_queue.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH021_030_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md`

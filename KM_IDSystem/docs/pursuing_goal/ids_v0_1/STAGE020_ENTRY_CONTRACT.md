# IDS v0.1 STAGE-020 Entry Contract

## Taskpack Identity
- Stage: `STAGE-020 · 导入成本估算器`
- Task: `IDS-V0_1-STAGE020-P1`
- Acceptance: `ACC-STAGE-020`
- Version: `v0.1`
- Domain: `D04 · 导入预检与数据优先级`
- Entrance: `人类产品入口 + IDS 系统运营入口`
- Pursuing goal: `估算 embedding token、外部 API 成本、OCR 页数、索引体积和本机空间压力。`
- Phase scope: `Phase 1 · 范围、输入输出与边界确认`

## Preconditions
- `STAGE-019` is locally complete and still blocks GitHub upload until the `STAGE-011..020` batch is complete, reviewed, repaired, and app entries are reinstalled.
- `BATCH011_020_UPLOAD_LOCK.yaml` remains `push_allowed: false`.
- `/Users/linzezhang/Downloads/IDS_MetaData` is recorded only as a local read-only real-data root. This phase must not read, list, hash, open, copy, move, delete, modify, dump, or scan its raw database content.

## Phase 1 Contract
`IDS-V0_1-STAGE020-P1` defines the import cost estimator boundary for future Phase 2 implementation. It records the minimum input and output contract needed to estimate embedding token volume, external API cost, OCR page count, index size, and local storage pressure before any batch import can proceed.

Phase 1 is a contract-only phase:
- It defines accepted metadata inputs, owner-facing output summary fields, cost items, risk items, and confirmation states.
- It confirms the estimator may only consume metadata approved by the import preflight/risk-estimator boundary.
- It confirms owner confirmation is mandatory: owner 确认后才进入批量处理.
- It preserves the raw data boundary: 只读取元信息, 不解析正文, 不修改原始文件.

## Explicit Non-Goals
- `NO_PHASE2`: do not implement the cost estimator helper, CLI, UI route, backend route, database adapter, or persistence.
- Do not start OCR, Embedding, index building, import, report generation, external API calls, service start, dependency install, GitHub upload, PR, merge, or app reinstall.
- Do not create runtime data, reports, outputs, manifests, evidence ledgers, audit logs, document/chunk/job/index/import rows, screenshots, PDFs, or JSON output files.
- Do not use fake IDS business data, fake database rows, fake source documents, or fabricated evidence.

## Acceptance Evidence
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE020_ENTRY_CONTRACT.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE020_PHASE1_SCOPE_BOUNDARY.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage020_import_cost_estimator.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md`

# IDS v0.1 STAGE-023 Entry Contract

## Taskpack Identity
- Stage: `STAGE-023 · 预检场景测试`
- Task: `IDS-V0_1-STAGE023-P1`
- Acceptance: `ACC-STAGE-023`
- Version: `v0.1`
- Domain: `D04 · 导入预检与数据优先级`
- Entrance: `人类产品入口 + IDS 系统运营入口`
- Pursuing goal: `验证大目录、空目录、坏文件、压缩包、空间不足、移动硬盘断开等场景。`
- Phase scope: `Phase 1 · 范围、输入输出与边界确认`
- P0 taskpack file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-023_预检场景测试.md`
- P0 stage file SHA-256:
  `dce8e78bea790c56b16b9b4035b82160056f51ea0b7ddf020a19ddc465cadc2d`

## Preconditions
- `STAGE-021` and `STAGE-022` are locally complete, but `BATCH021_030_UPLOAD_LOCK.yaml` remains locked until `STAGE-021..030` all complete, are reviewed, and any review findings are repaired.
- `/Users/linzezhang/Downloads/IDS_MetaData` remains a path-only read-only real-data source boundary. This phase must not read, list, hash, open, copy, move, delete, modify, dump, scan, normalize, or commit raw database content.
- All IDS runtime corpus, database-backed content, analytics inputs, reports, indexes, manifests, and committed examples must use real user-approved data; fake IDS business data and fabricated evidence are forbidden.

## Phase 1 Contract
`IDS-V0_1-STAGE023-P1` defines the preflight scenario-test boundary for later implementation. It records the scenario suite vocabulary, metadata-only input directory identity, required scenarios, output summary, risk items, cost items, confirmation states, owner confirmation gate, and no-processing rules needed before the system can validate large directory, empty directory, bad file, archive, insufficient space, and offline removable-drive conditions.

Phase 1 is a contract-only phase:
- It defines metadata-only scenario-test inputs and owner-visible outputs for the human product entrance and IDS operations entrance.
- It binds preflight, risk, and cost snapshots from prior stages without re-reading raw source content.
- It defines required scenario IDs: `empty_directory`, `small_directory`, `large_directory`, `offline_drive`, `bad_file`, `archive_present`, and `insufficient_space`.
- It confirms owner confirmation is mandatory: owner 确认后才进入批量处理.
- It preserves the raw data boundary: 只读取元信息, 不解析正文, 不修改原始文件.

## Explicit Non-Goals
- `NO_PHASE2`: do not implement the scenario runner, UI component, backend endpoint, queue runner, persistence, scenario fixture builder, screenshot, or runnable batch-processing workflow.
- Do not start parsing, OCR, Embedding, index building, import, report generation, external API calls, service start, dependency install, GitHub upload, PR, merge, or app reinstall.
- Do not create runtime data, reports, outputs, manifests, evidence ledgers, audit logs, document/chunk/job/index/import rows, screenshots, PDFs, JSON output files, or production preflight reports.
- Do not use fake IDS business data, fake database rows, fake source documents, or fabricated evidence.

## Acceptance Evidence
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_ENTRY_CONTRACT.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_PHASE1_SCOPE_BOUNDARY.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage023_preflight_scenario_tests.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH021_030_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md`

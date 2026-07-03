# IDS v0.1 STAGE-023 Phase 1 Scope Boundary

## Scope
- Stage: `STAGE-023 · 预检场景测试`
- Task: `IDS-V0_1-STAGE023-P1`
- Acceptance: `ACC-STAGE-023`
- Entrance: `人类产品入口 + IDS 系统运营入口`
- Phase: `Phase 1 · 范围、输入输出与边界确认`
- Recorded at UTC: `2026-07-03T00:57:12Z`

This phase defines the preflight scenario-test contract only. It prepares the field vocabulary, required scenario IDs, scenario result summary, confirmation states, owner decision boundary, and no-processing rules for a later implementation slice that can validate preflight behavior before any batch-processing work starts.

## P0 Source Evidence

| Check | Result |
|---|---|
| P0 taskpack zip | `/Users/linzezhang/Downloads/RAG IDS/v0.1/IDS_Taskpack_v0_1_only_中文修订版.zip` |
| P0 taskpack zip SHA | `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3` |
| Stage file inside zip | `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-023_预检场景测试.md` |
| Stage file SHA-256 | `dce8e78bea790c56b16b9b4035b82160056f51ea0b7ddf020a19ddc465cadc2d` |
| Stage execution index | STAGE-023 maps to `D04-S006`, `ACC-STAGE-023`, and `stages/STAGE-023_预检场景测试.md` |

The stage source was read directly from the user-provided v0.1 taskpack zip without extracting or copying the taskpack into the worktree.

## Inputs
Phase 1 defines these future metadata-only inputs:
- `preflight_scenario_suite_id`: stable id for one owner-visible preflight scenario-test suite.
- `scenario_id`: one of the required scenario identifiers below.
- `scenario_input_directory_uri`: explicit owner-supplied local `file://` directory identity for scenario validation; Phase 1 records the contract only and does not enumerate the directory.
- `scenario_source_preflight_snapshot_ref`: immutable reference to an already approved metadata-only STAGE-018/021 preflight snapshot.
- `preflight_summary_snapshot`: approved metadata summary such as file count, format count, size range, archive candidate count, scanned candidate count, and readiness state.
- `risk_summary_snapshot`: approved metadata-only risk summary from STAGE-019, including high-risk counts, blocked reasons, unknown format counts, oversized counts, bad-file indicators, offline-source indicators, and risk score band.
- `cost_summary_snapshot`: approved metadata-only cost summary from STAGE-020, including OCR, Embedding, external API, index size, local-space pressure, and cost score band.
- `owner_confirmation_context`: product entrance, IDS operations entrance, operator identity label, requested action, pending confirmation state, and audit note.

The input contract is metadata-only. It must not read raw database content from `/Users/linzezhang/Downloads/IDS_MetaData`; it must not recursively scan source roots; it must not parse body text.

## Required Scenarios
- `empty_directory`: empty input directory readiness and owner explanation.
- `small_directory`: small valid directory baseline.
- `large_directory`: large directory summary without body parsing or batch processing.
- `offline_drive`: removable or external-drive path unavailable or disconnected.
- `bad_file`: unreadable, corrupt, zero-byte, permission-blocked, or structurally invalid candidate recorded only as metadata and never as fake business content.
- `archive_present`: archive candidate present and owner review required before extraction or parsing.
- `insufficient_space`: local-space pressure blocks continuation before OCR, Embedding, index, or import.

## Outputs
Phase 1 defines these owner-facing output fields for future Phase 2:
- `scenario_validation_summary`: compact owner-visible summary of the scenario suite result.
- `required_scenarios`: required scenario IDs, expected metadata signals, and acceptance hints.
- `scenario_results`: per-scenario pass, warning, blocked, or needs-owner-review result.
- `preflight_summary_snapshot`: copied metadata-only preflight summary used by the scenario suite.
- `risk_summary_snapshot`: copied metadata-only risk summary used by the scenario suite.
- `cost_summary_snapshot`: copied metadata-only cost summary used by the scenario suite.
- `risk_items`: blocked reasons, offline source, archive review, bad-file indicators, unknown formats, oversized candidates, or high-risk items requiring owner review.
- `cost_items`: estimated OCR, Embedding, external API, index size, local-space pressure, and high-cost signals requiring owner review.
- `confirmation_status`: owner-visible preflight scenario confirmation state.
- `human_product_entrance_payload`: restrained Chinese scenario-test summary for `人类产品入口 + IDS 系统运营入口`.
- `ids_operations_entrance_payload`: machine-side status and audit hints for IDS operators.

## Confirmation States
- `PREFLIGHT_SCENARIO_DRAFT`: scenario-test summary is incomplete and cannot be approved.
- `PREFLIGHT_SCENARIO_READY`: metadata is sufficient for owner review.
- `PREFLIGHT_SCENARIO_OWNER_REVIEW_REQUIRED`: owner must review risk, cost, scenario, and readiness before batch processing.
- `PREFLIGHT_SCENARIO_WAITING_OWNER_CONFIRMATION`: scenario suite is ready but no owner confirmation has been recorded.
- `PREFLIGHT_SCENARIO_OWNER_APPROVED`: owner explicitly approves the scenario result for the next batch-processing gate.
- `PREFLIGHT_SCENARIO_PAUSED`: owner pauses the scenario suite without side effects.
- `PREFLIGHT_SCENARIO_BLOCKED`: missing metadata, raw-data boundary conflict, offline drive, bad file, archive risk, local-space pressure, high-risk item, cost block, or policy conflict blocks continuation.

Owner confirmation is mandatory: owner 确认后才进入批量处理.

## Risk, Cost, And Confirmation Rules
- Large directories, empty directories, offline removable drives, bad files, archives, unknown formats, oversized candidates, scanned materials, insufficient space, and high OCR/Embedding/API/index estimates can require `PREFLIGHT_SCENARIO_OWNER_REVIEW_REQUIRED`.
- Scenario status is advisory until owner confirmation; it must not trigger parsing, OCR, Embedding, indexing, import, report generation, manifest writes, database writes, or queue execution.
- Future Phase 2 may compute scenario-test outputs only from approved metadata snapshots; this Phase 1 does not implement those computations.

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
- `NO_PHASE2`: this run must not implement or exercise the preflight scenario-test runner.

## Rollback
Revert only `IDS-V0_1-STAGE023-P1` entry/scope evidence, focused tests, `BATCH021_030_UPLOAD_LOCK.yaml`, roadmap/event, Stage005 governance-regression updates, and rendered owner files. Do not touch `/Users/linzezhang/Downloads/IDS_MetaData`, runtime data, reports, outputs, persisted manifests, evidence ledgers, audit logs, indexes, delivered reports, app entries, GitHub state, or Phase 2 artifacts.

# S12-P3 Completion Record｜重跑机制

更新时间: 2026-07-01T14:00:00+10:00

## Scope

- phase: `S12-P3｜重跑机制`
- task_ids: `S12PCT01-S12PCT03`
- status: `completed_validated_local_only`
- version: `0.1.0-s12p3-rerun-mechanism`
- source_dependency: `S12-P1 人工处理事件` + `S12-P2 影响预览`
- upload_status: `not_performed`

## Completed

- `S12PCT01`: S12-P2 preview passed and publish-allowed events invalidate derived cache.
- `S12PCT02`: rerun chain covers `field_mapping`, `fact_layer`, `derived_metric`, `report_reference`.
- `S12PCT03`: rerun output has same-source consistency checks with mismatch count `0`.

## Evidence

- Runtime: `KMFA/tools/manual_rerun_mechanism.py`
- Validator: `KMFA/tools/check_s12_p3_manual_rerun_mechanism.py`
- Unit tests: `KMFA/tests/test_manual_rerun_mechanism.py`
- Manifest: `KMFA/metadata/lineage/manual_rerun_manifest.json`
- Cache invalidations: `KMFA/metadata/lineage/manual_rerun_cache_invalidations.jsonl`
- Rerun steps: `KMFA/metadata/lineage/manual_rerun_steps.jsonl`
- Consistency checks: `KMFA/metadata/lineage/manual_rerun_consistency_checks.jsonl`
- Stage manifest: `KMFA/stage_artifacts/S12_P3_manual_rerun_mechanism/machine/s12_p3_manifest.json`
- HTML preview: `KMFA/stage_artifacts/S12_P3_manual_rerun_mechanism/exports/html/kmfa_manual_rerun_mechanism.html`

## Counts

- source events: `5`
- source impact previews: `5`
- eligible preview-passed events: `2`
- blocked previews: `3`
- cache invalidations: `2`
- rerun steps: `8`
- same-source consistency checks: `2`
- raw layer writes: `0`
- formal reports: `0`
- Stage 12 review executions: `0`
- GitHub uploads: `0`

## Boundaries

- Does not commit raw business data, private file content, field plaintext, zip, Excel, PDF, private CSV, sqlite/db, credentials or account data.
- Does not mutate raw/source layers.
- Does not overwrite old derived versions; rerun writes append-only public-safe derived version refs.
- Does not generate formal reports, upgrade report grade, close pending reconciliation differences, perform Stage 12 review, perform GitHub upload, perform lineage full check or call external connectors.

## Next Gate

下一步只能执行 `Stage 12 整体复审`：复跑 S12-P1/P2/P3 validators、治理 validator、raw/secret scan、parse checks 和 evidence consistency，并修复 findings。不得在未复审前 upload。

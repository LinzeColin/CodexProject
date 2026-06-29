# S03-P3 Source Priority Completion Record

## Scope

- stage: `S03`
- phase: `S03-P3`
- tasks: `S3PCT01-S3PCT03`
- version: `0.1.0-s03p3`
- status: `completed_validated_local_only_stage_review_passed`

## Completed

- `S3PCT01`: 固化源类别优先级：`raw_upload -> authorized_export -> raw_extracted_value -> staging_structured_row -> canonical_fact -> derived_metric -> report_reference -> frontend_display -> processed_data`。
- `S3PCT02`: 同源不同引用不一致时生成 metadata event，动作固定为 `invalidate_derived_cache` 和 `request_rerun`。
- `S3PCT03`: 跨源冲突生成 `source_difference_queue_item`，状态为 `queued_for_manual_review`，`auto_selection_allowed=false`。

## Files Added Or Updated

- `KMFA/tools/source_priority.py`
- `KMFA/tests/test_source_priority.py`
- `KMFA/metadata/sources/source_priority_policy.yaml`
- `KMFA/metadata/sources/source_priority_events.jsonl`
- `KMFA/metadata/quality/source_difference_queue.jsonl`
- `KMFA/metadata/sources/source_registry.yaml`
- `KMFA/metadata/lineage/derived_data_policy.yaml`
- `KMFA/metadata/protocol/directory_manifest.json`
- `KMFA/tools/metadata_protocol_check.py`

## Non Scope

- 不解析业务字段。
- 不读取或提交真实原始业务数据。
- 不计算金额、不建立事实层、不生成报告。
- 不自动选择跨源冲突的一边。
- 不执行 Stage 3 复审或 GitHub 上传。

## Stage Boundary

S03-P3 已本地完成，但 Stage 3 尚未整体复审；复审、修复和 GitHub 上传必须在后续 run work 中单独执行。

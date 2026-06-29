# KMFA S01-P1 Files To Modify

更新时间: 2026-06-29

## 1. 本轮允许修改

仅允许写入 S01-P1 计划与证据文件:

```text
stage_artifacts/S01_P1_read_only_plan/human/implementation_plan.md
stage_artifacts/S01_P1_read_only_plan/human/files_to_read.md
stage_artifacts/S01_P1_read_only_plan/human/files_to_modify.md
stage_artifacts/S01_P1_read_only_plan/human/test_commands.md
stage_artifacts/S01_P1_read_only_plan/human/rollback_plan.md
stage_artifacts/S01_P1_read_only_plan/human/risk_register.md
stage_artifacts/S01_P1_read_only_plan/human/stop_conditions.md
stage_artifacts/S01_P1_read_only_plan/human/no_omission_check_result.md
stage_artifacts/S01_P1_read_only_plan/human/s01_p1_completion_record.md
stage_artifacts/S01_P1_read_only_plan/machine/s01_p1_manifest.json
stage_artifacts/S01_P1_read_only_plan/machine/source_hashes.json
```

## 2. 本轮禁止修改

```text
KMFA/
README.md
功能清单.md
开发记录.md
模型参数.md
metadata/
scripts/
src/
web/
```

原因: 这些属于 `S01-P2` 或后续业务实现，不属于 `S01-P1`。

## 3. S01-P2 预计会修改

如果进入下一 Phase，预计创建:

```text
KMFA/README.md
KMFA/功能清单.md
KMFA/开发记录.md
KMFA/模型参数.md
KMFA/HANDOFF.md
KMFA/metadata/project/project.yaml
KMFA/metadata/stage_status.jsonl
KMFA/metadata/model_registry.yaml
KMFA/metadata/quality/
KMFA/metadata/traceability/
```

实际落地前必须重新给 S01-P2 execution contract。

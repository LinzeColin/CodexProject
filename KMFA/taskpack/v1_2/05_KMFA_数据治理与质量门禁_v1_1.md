# KMFA 数据治理与质量门禁 v1.1

## 1. 核心原则

1. 原始数据不可污染。
2. 原始上传/授权导出数据优先级最高。
3. 派生数据可重跑、可对比、可回滚。
4. 前端只写控制事件，不改原始事实。
5. 报告只读事实层和指标层，不能直接改数。
6. 金额一律整数分或Decimal。
7. 任意0.01元差异必须失败或进入差异队列。
8. 质量门禁优先于时间参考。

## 2. 必须生成的metadata

```text
metadata/sources/source_registry.yaml
metadata/imports/import_runs.jsonl
metadata/imports/raw_file_manifest.jsonl
metadata/schema_maps/source_mapping_versions.yaml
metadata/quality/data_quality_results.jsonl
metadata/quality/zero_delta_results.jsonl
metadata/quality/mismatch_report.csv
metadata/lineage/field_lineage.jsonl
metadata/lineage/metric_lineage.jsonl
metadata/lineage/report_lineage.jsonl
metadata/approvals/resolution_events.jsonl
metadata/approvals/human_signoff_log.jsonl
metadata/reports/report_manifest.jsonl
```

## 3. 状态定义

| 状态 | 含义 | 行为 |
|---|---|---|
| 已就绪 | 已上传/已同步，校验通过 | 可推进 |
| 部分/阻塞 | 部分可用或关键字段缺失 | 降级或阻塞对应报告 |
| 失败/不适用 | 文件失败、格式不适用、规则不支持 | 不参与正式计算 |
| 已过期 | 超过新鲜度要求 | 报告降级 |
| 人工复核 | 需要人为判断 | 进入待处理事项 |

## 4. 报告发布门禁

1. A级报告必须Q5数据。
2. B级报告必须Q4及以上，且限制清晰。
3. C级报告只可预览。
4. D级报告不得作为经营决策依据。
5. 差异未处理不得升级报告等级。

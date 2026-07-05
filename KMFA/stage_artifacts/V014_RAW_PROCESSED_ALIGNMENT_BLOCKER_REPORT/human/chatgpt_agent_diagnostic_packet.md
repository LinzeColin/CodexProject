# 可转发诊断包：KMFA raw/processed 暂无法对齐

## 可公开给外部 agent 的事实

- 版本：`0.1.4-raw-processed-alignment-blocker-report`
- 当前决策：`NO_GO`
- raw 数值 fingerprint 已存在：`871` 条
- raw unique numeric fingerprint：`330`
- processed target slots：`149`
- staged processed value fingerprints：`0`
- usable processed source-map：`0`
- authorized filled / unfilled：`36` / `113`
- unresolved source-map gaps：`113`
- comparable value pairs：`0`
- business_value_consistency_verified：`false`

## 需要外部 agent 诊断的问题

如何在不暴露原始业务数据、不提交 raw 文件、不公开字段/表名/行列/业务值的前提下，补齐 target-slot 到 processed-value source-map 的授权证据，使系统能生成可比较的 raw/processed value pairs？

## 允许的输入结构

- `target_slot_reference_from_existing_private_worklist`
- `authorized_processed_value_fingerprint`
- `authorized_source_basis_reference`
- `owner_or_authorized_delegate_role`
- `authorization_timestamp`
- `allowed_action_code`

## 禁止事项

- 不要要求公开 raw 文件名、raw hash、表名、字段/表头、行列坐标或业务值。
- 不要把本诊断解释为已经完成 raw-to-processed comparison。
- 不要建议直接上传 GitHub、重装 app、发布正式报告或执行业务动作。

# S18-P1 回滚计划

1. 回退本 phase local commit 与 `KMFA/stage_artifacts/V014_S18_P1_POST_REMEDIATION_PRECISION_STRESS` public-safe 证据。
2. 删除 ignored `KMFA/.codex_private_runtime/v014_s18_p1_post_remediation_precision_stress` 私有快照和诊断，不触碰 raw inbox。
3. 回退 S18-P1 metadata 与治理登记，恢复 Stage 17 review 为 current pointer。
4. 不执行生产恢复、补偿业务动作、GitHub upload 或 app reinstall。

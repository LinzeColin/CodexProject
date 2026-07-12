# Stage 17 整体复审回滚计划

1. 回退本 review 本地 commit 与 `KMFA/stage_artifacts/V014_S17_POST_REMEDIATION_STAGE_REVIEW` public-safe 证据。
2. 同步回退本 review 对 P1 通知契约和 P3 owner/audit mapping 的修复，避免半套合同。
3. 回退 review metadata 和治理登记，不改历史 S17-P1/P2/P3 legacy 夹具。
4. 删除 ignored review 私有快照，不触碰原始目录，不执行生产恢复或补偿业务动作。

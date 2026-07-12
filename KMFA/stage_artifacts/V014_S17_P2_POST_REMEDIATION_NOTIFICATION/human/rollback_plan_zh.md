# S17-P2 通知回滚计划

1. 回退本 phase 的本地 commit 与 `KMFA/stage_artifacts/V014_S17_P2_POST_REMEDIATION_NOTIFICATION` public-safe 证据。
2. 回退本 phase 新增的 metadata/notifications 镜像和治理登记，不改历史 S17-P2 夹具。
3. 删除 ignored private raw/scan 证据，不触碰原始目录。
4. 不发送补偿通知，不调用外部连接器，不修改任何原始文件。

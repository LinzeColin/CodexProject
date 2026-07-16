# Known gaps · ADP-S1-P01-T011

- **manifest 快照为 T009 基线 commit**：STATUS_GENERATED 绑定的 commit 来自 deployment_manifest.sample.json（T009 生成，commit 83a845be），比 T010 后的 worker 略旧；但 build_id（bd67a78020a3，线上）为当前真相，架构断言（云端原生/无隧道）正确。每次部署重跑 generate_manifest + generate_status 是持续纪律。
- **drift check 未接入 GitHub CI workflow**：check_status_drift.py 可本地/CI 运行并已验证，但尚未挂进 .github workflow；接入属后续（S1 部署纪律）。
- **generate_status 读线上 /build.json 需网络**：离线时 build_id 标 UNVERIFIED_LIVE；可用 --build-id 传入确定值（本任务用 bd67a78020a3）。
- **只标 R6 superseded，未删除历史**：R6 段保留为历史记录（superseded_note 指向 generated current），不删除（保留可追溯）。
- 独立验证：本报告以 IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION 结束，PASS/FAIL 由独立上下文判定，实现者不自签。

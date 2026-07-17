# KMFA v1.5 S02-P2 回滚方案

1. 仅回滚本 Phase 新增的 builder、validator、helper、tests、`V015_S02_P2_END_TO_END_TRACEABILITY` 证据目录及对应治理文本。
2. 恢复 S02-P1 commit `1de399f35d1c0d2b7ee1ea6451c2be8d1c49a861` 的 current/next gate，但不得改写 S02-P1 已通过历史。
3. 不删除、移动、重命名或修改 raw inbox；本 Phase 没有 raw、private runtime、GitHub、App 或业务 side effect 需要逆操作。
4. 回滚后复跑 S02-P1 strict validator、roadmap governance 与项目治理检查。

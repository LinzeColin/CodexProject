# KMFA v0.1.4 一次性 GitHub main 上传回滚计划

1. 上传前任一 validator、测试或安全扫描失败：不推送，保留本地 commit 并修复后重新验收。
2. push dry-run 发现远端 main 已移动：停止，fetch 后重新集成，不使用 force。
3. 实际 push 被拒绝：不绕过保护规则，记录命令结果并修复远端门禁。
4. 推送后 parity 失败：停止 App 重装，重新 fetch 和核对 commit；不得用第二次未经复审的 push 掩盖差异。
5. 已上传代码出现回归：另立修复 phase 和新 commit，不删除、重写或修改用户原始数据。

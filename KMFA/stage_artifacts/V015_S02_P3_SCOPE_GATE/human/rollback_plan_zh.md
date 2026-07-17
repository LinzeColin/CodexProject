# KMFA v1.5 S02-P3 回滚方案

## 回滚范围

仅回滚本 Phase 的 tracked 代码、测试、治理登记与 `V015_S02_P3_SCOPE_GATE` 公开安全证据。不得触碰 S02-P1/P2 依赖证据、raw inbox、私有运行目录、已发布 App 或远端分支。

## 回滚步骤

1. 在确认本地结果 commit 后，以普通 revert 创建反向提交；不得使用破坏性 reset。
2. 删除或恢复仅属于本 Phase 的新增工具、测试和 Stage artifacts，并恢复本 Phase 修改的治理文件。
3. 复跑 S02-P1 与 S02-P2 strict dependency validator、Roadmap `--check`、project/lean governance、no-float、no-omission 与 governance sync。
4. 确认治理状态回到 S02-P2 已通过、仅允许 S02-P3 的历史前置状态；不得把 S02 或 S03 误标为通过。

## 停止条件

- 任一操作将触碰 raw、私有输入、远端 Git、安装 App 或用户业务系统时立即停止。
- 无法保持 S02-P1/P2 证据 byte/hash 绑定时立即停止并人工复核。

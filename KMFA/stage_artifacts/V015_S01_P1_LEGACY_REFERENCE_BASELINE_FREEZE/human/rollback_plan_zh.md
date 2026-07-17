# S01P1 legacy 参考基线回滚与重建计划

## 可重建部分

1. 通过 baseline commit `d6f379ad11d486d8a7ebde9e61b2fc7b3aaf9d05` 重建 repo snapshot。
2. 从该 commit 的 `KMFA/metadata` Git tree 重建公开 metadata。
3. 从该 commit 重建 `kmfa_home_navigation.html`，并校验 SHA-256 `8b3618...16b2`。

推荐使用新的临时 Git worktree 或 `git archive` 验证，不对 canonical worktree 执行 reset/checkout。

## 只能恢复、尚不能重建的部分

已安装 `/Users/linzezhang/Downloads/KMFA.app` 可以用全树 SHA-256 和 code signature 比较，也可以从现有已验证副本恢复；仓库没有 builder/installer 源码，因此不能声称能从 Git 重新构建该 App。

## 本 Phase 回滚

本 Phase 只新增公开安全审计证据、validator、test 和治理登记，不改业务代码。若证据本身错误，使用反向补丁移除本 Phase 新增行和文件；不得改动 baseline commit、raw root 或现有 App 来“制造一致”。

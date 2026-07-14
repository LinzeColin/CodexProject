# S12-P2 回滚方案

1. 仅回退本 phase 的本地 commit。
2. 删除 ignored private S12-P2 运行证据。
3. 保留 S12-P1 commit 与历史 S12-P2 fixture，不改 raw inbox。
4. 复跑 S12-P1 strict validator，确认前序边界仍有效。

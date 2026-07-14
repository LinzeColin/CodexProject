# S12-P3 回滚方案

1. 仅回退本 phase 的本地 commit。
2. 删除 ignored private S12-P3 运行证据。
3. 保留 S12-P1/P2 commits 与旧版 policy fixture，不改 raw inbox。
4. 复跑 S12-P2 strict validator，确认前序影响预览边界仍有效。

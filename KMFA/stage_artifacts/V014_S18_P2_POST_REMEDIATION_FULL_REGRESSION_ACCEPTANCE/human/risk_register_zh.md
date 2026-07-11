# S18-P2 风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 旧上传记录被误当当前验收 | 当前 Stage 索引仅引用 review manifest 与 S18-P1/P2 证据 | 已控制 |
| lineage 检查通过被误读为 lineage 完整 | 结果明确为 BLOCKED_SAFE，full lineage=false | 已控制 |
| 旧 HTML 54/54 被当作当前执行 | 本轮重新运行 Playwright 并生成当前 CSV | 已控制 |
| 质量未通过仍交付 | Go/No-Go 强制 NO_GO，全部交付门禁关闭 | 已控制 |
| raw 被回归测试污染 | raw 仅作 ignored private 前后快照，五类检查均使用公开安全证据 | 已控制 |

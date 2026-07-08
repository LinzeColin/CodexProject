# Raw机器账本说明

Task ID: `MA-V12-S03P3`.

Acceptance ID: `ACC-MA-V12-S03P3`.

Status: `phase_s03_p3_machine_ledger_completed_pending_s03_review`.

本页只解释 S03 P3 的机器账本边界，不展示 raw manifest 逐行明细。

S03 P3 已把 raw manifest 和 hash ledger 生成为机器文件。机器账本用于记录
source/file/hash/imported_at 映射，让后续 agent 可以判断公开 raw 是否只追加、
是否发生 hash drift、是否有 manifest entry 被删除。

当前仓库还没有真实 raw transcript 文件，因此 baseline machine ledger 可以为空。
`README.md`、`.gitkeep`、`.DS_Store` 这类说明或占位文件不会被锁成 transcript raw。

S03 P3 的边界：

- raw manifest 是机器文件，不是人类主要页面。
- 新 raw 文件允许追加。
- 已有 raw 文件 hash 改变会让 audit fail。
- 已登记 raw 文件被删除会让 audit fail。
- 本 phase 不实现 connector，不导入真实 transcript，不新增 UI。
- No GitHub main upload in this phase.

下一步是 S03 Review。

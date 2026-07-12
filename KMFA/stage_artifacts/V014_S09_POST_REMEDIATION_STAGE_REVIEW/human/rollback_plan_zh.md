# Stage 9 修补后整体复审回滚计划

1. 回退本 review 的本地 commit，恢复 review 前治理与证据文件。
2. 不回退、不覆盖、不移动、不删除原始目录中的任何文件。
3. 若状态字段规范化需要撤销，只回退本次新增字段，不改变历史状态结论。
4. 回滚后恢复到上一 residual phase 的 `69 closed-or-excluded / 3 final-accepted-open / NO_GO` 状态。

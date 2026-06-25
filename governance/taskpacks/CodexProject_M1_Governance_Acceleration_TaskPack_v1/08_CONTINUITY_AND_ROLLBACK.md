# 连续开发、交接与回滚

## 新 Agent 五文件启动集

任何后续 Agent 最多先读：

1. 根 `AGENTS.md`；
2. `docs/governance/STANDARD.md`；
3. 本任务的最终 handoff；
4. 当前 Task 对应代码/测试；
5. 当前 PR diff 或 run manifest。

禁止要求新 Agent 读取所有历史压缩包才能知道当前状态。

## Handoff 最低字段

```text
repository
branch
base_sha
head_sha
current_task_id
numeric_sequence
acceptance_ids
decision: SHIP/FIX-ONE/STOP
files_read
files_changed
diff_summary
commands_and_exit_codes
legacy_result
candidate_result
zero_write_proof
open_P0_P1
remaining_P2_P3
rollback_command
next_unique_task
```

## 并行规则

- S1/S2 的三个审查 Agent 可并行，因为只读且互不依赖。
- S3-S5 写入任务默认串行：测试 -> 实现 -> parity -> 激活。
- 若确需两个写线程，必须独立 worktree、write_scope 不重叠、接口稳定，并指定 Integrator。
- `scripts/lean_governance.py`、workflow、标准与同一测试文件属于共享热点，不允许两个实现线程并行修改。

## 回滚

1. Shadow 阶段：关闭候选输出/分支即可；legacy 从未失去权威。
2. 有限激活：通过 feature flag/单提交 revert 恢复 legacy。
3. Workflow 异常：恢复上一版 workflow，保持 Required Check 名称。
4. 出现 tracked 写入：立即停止、保存 diff 证据、重置该 Task 的未验收改动。
5. 出现 false negative：撤销激活，所有候选分类回到完整检查，重新进入 S4。

## 数据与缓存

- 审查、遥测和完整 JSON 放 `.git/codex-review/`、runner temp 或 CI artifact。
- 初版不引入 persistent cache。
- 不保存凭据、环境变量或敏感日志。
- 任务完成/取消后清理临时目录和后台进程。

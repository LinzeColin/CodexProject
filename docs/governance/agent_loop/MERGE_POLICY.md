# Agent Loop Merge Policy

## 风险等级

Agent Loop 只使用两个等级：

- `T1`: 旧低/中风险任务。
- `T2`: 旧高/关键风险任务。

T1 和 T2 都不要求 Owner 在 workflow 中人工批准。自动合并只在所有 gate 通过后发生。

## T1 ROI Hotfix v1

T1 默认使用 `executor_mode=codex-one-shot`：

- 只允许一次 paid `openai/codex-action@v1` 调用。
- 不再单独跑 paid plan call。
- Codex review 默认关闭。
- Architect Review 默认关闭。
- autofix 默认关闭。
- production deploy 禁止。

T1 merge 必须满足：

- Task Pack validation PASS。
- Routing READY。
- Implementation validation PASS。
- Changed-files policy PASS。
- Merge policy PASS。
- 没有 `BLOCK_MERGE=true`。
- 没有 forbidden path 修改。
- 没有 secret/env/dependency/production deployment 变更，除非 Task Pack 明确授权。

## T2

T2 仍必须 plan-first，但不能在同一个 GitHub Actions job 内用多次
`openai/codex-action@v1` 实现 plan + implement。

在独立 multi-job T2 编排实现前，workflow 必须以
`T2_MULTI_JOB_NOT_IMPLEMENTED` 阻断并且不消耗 paid Codex call。

## No Blind Rerun

任何 paid call 之后失败，都必须先检查 artifact：

- `agent-loop-roi-summary.md`
- `failure-git-status.txt`
- `failure-diff-name-only.txt`
- `failure-diff-stat.txt`

未完成 artifact review 前，不应删除 `agent:blocked` 或重新触发 issue。

## 禁止合并

以下情况必须阻断合并：

- Task Pack metadata 缺失或无效。
- `production_deploy` 不是 `false`。
- changed-files policy FAIL。
- validation FAIL。
- paid-call limit reached。
- unresolved P0/P1 issue。
- secret/env/dependency/production deploy 文件被修改且未授权。
- T2 试图在 single-job multi Codex Action 模式中执行。

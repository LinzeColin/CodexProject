# Agent Loop ROI Policy

## 目标

Agent Loop 先追求低成本跑通主链，再逐步打开高消耗复审和修复能力。
Owner 的小额试运行预算应优先用于：

1. 第一次成功的 T1 自动合并。
2. 一个真实高价值任务。
3. 只在 artifact 已读清楚后做必要 rerun。

不要把预算消耗在重复调试同一个 workflow 失败点上。

## T1 默认执行

T1 是低/中风险任务。ROI Hotfix v1 规定：

- `executor_mode`: `codex-one-shot`
- paid Codex Action calls: 最多 1 次
- Codex review: 默认关闭
- Architect Review: 默认关闭
- autofix: 默认关闭
- production deploy: 禁止

T1 one-shot 流程：

Task Pack validation -> routing/autofill -> one-shot Codex implementation ->
validation commands -> changed-files policy -> PR -> merge policy -> squash
merge。

one-shot prompt 要求 Codex 先给出简短实现计划，再修改文件并返回 Result Pack。
workflow 不再为 T1 单独跑一次 paid plan call。

## T2 当前策略

T2 是高/关键风险任务。T2 仍必须 plan-first，但不能在同一个 GitHub Actions
job 内连续调用多次 `openai/codex-action@v1`。

在单独的多 job plan/implement 编排实现前，T2 会以
`T2_MULTI_JOB_NOT_IMPLEMENTED` 安全阻断，不消耗 paid Codex call。

## No Blind Rerun

任何 paid Codex call 之后失败，都必须先检查 artifact：

- `agent-loop-run-<run-id>`
- `agent-loop-roi-summary.md`
- `failure-git-status.txt`
- `failure-diff-name-only.txt`
- `failure-diff-stat.txt`

未完成 artifact review 前，不应删除 `agent:blocked` 或重新触发 issue。

## Paid Call Limit

workflow 在每次 `openai/codex-action@v1` 前都会先占用 paid-call 额度。
如果下一次调用会超过 `max_paid_codex_calls`，workflow 会在调用前停止，
将 issue 标记为 `agent:blocked`，并评论 `PAID_CALL_LIMIT_REACHED`。

## 预算操作规则

- 默认 T1 预算上限可设为 `roi_budget_usd: 2.0`。
- 默认 `value_score` 最低为 1；低价值 smoke test 应避免进入高消耗 review/autofix。
- `$20` 试运行预算下，优先证明一条 T1 主链能从 Issue 到 auto-merge 跑通。
- 重复失败时先读日志和 artifact，再修改 workflow；不要直接 rerun。

## 后续打开顺序

1. T1 one-shot 主链成功 auto-merge。
2. 增加 mock/off 等零成本 plumbing 模式。
3. 为 T2 增加 fresh-job plan/implement 编排。
4. 再考虑默认打开 Codex review、Architect Review 或 autofix。

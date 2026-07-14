# v0.1.4 全局残余差异队列重放或权威排除

- Phase: `V014_GLOBAL_RESIDUAL_DIFFERENCE_QUEUE_REPLAY_OR_AUTHORITATIVE_EXCLUSION`
- 决策: `NO_GO`
- 队列记录 / 已分类: 72 / 72
- 私有目标值重放 / 整数公式重放: 37 / 16
- 经授权非数值排除: 8
- 已关闭或排除 / 继续未决: 61 / 11
- 保留非零差异: 9
- raw 前后完全一致: `true`

本 phase 对 72 条队列逐条重放。仅在来源唯一、整数公式可重放且不会覆盖现有非零差异时关闭；其余记录继续进入全中文 private 差异报告。
